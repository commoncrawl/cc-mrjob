import gzip
import logging
import os.path as Path
import warc
import boto
from boto.s3.key import Key
from gzipstream import GzipStreamFile
from mrjob.job import MRJob
from mrjob.util import log_to_stream

# Set up logging
# Duplicate log messages caused by: https://github.com/Yelp/mrjob/issues/1551
LOG = logging.getLogger(__name__)
log_to_stream(format="%(asctime)s;%(levelname)s;%(message)s", name=__name__)

class CCJob(MRJob):
    """
    A simple way to run MRJob jobs on CommonCrawl Data
    """
    def configure_options(self):
        super(CCJob, self).configure_options()
        self.pass_through_option('--runner')
        self.pass_through_option('-r')

    def process_record(self, record):
        """
        Override process_record with your mapper
        """
        raise NotImplementedError('Process record needs to be customized')

    def mapper(self, _, line):
        """
        The Map of MapReduce
        If you're using Hadoop or EMR, it pulls the CommonCrawl files from S3,
        otherwise it pulls from the local filesystem. Dispatches each file to
        `process_record`.
        """
        # If we're on EC2 or running on a Hadoop cluster, pull files via S3
        if self.options.runner in ['emr', 'hadoop']:
            # Connect to Amazon S3 using anonymous credentials
            conn = boto.connect_s3(anon=True)
            pds = conn.get_bucket('commoncrawl')
            # Start a connection to one of the WARC files
            k = Key(pds, line)
            ccfile = warc.WARCFile(fileobj=GzipStreamFile(k))
        # If we're local, use files on the local file system
        else:
            line = Path.join(Path.abspath(Path.dirname(__file__)), line)
            LOG.info('Loading local file {}'.format(line))
            ccfile = warc.WARCFile(fileobj=gzip.open(line))

        for i, record in enumerate(ccfile):
            for key, value in self.process_record(record):
                yield key, value
            self.increment_counter('commoncrawl', 'processed_records', 1)

    def combiner(self, key, value):
        # use the reducer by default
        for key_val in self.reducer(key, value):
            yield key_val

    def reducer(self, key, value):
        """
        The Reduce of MapReduce
        If you're trying to count stuff, this `reducer` will do. If you're
        trying to do something more, you'll likely need to override this.
        """
        yield key, sum(value)
