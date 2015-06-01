import gzip
#
import boto
import warc
#
from boto.s3.key import Key
from gzipstream import GzipStreamFile
from mrjob.job import MRJob


class CCJob(MRJob):
    def process_record(self, record):
        """
    Override process_record with your mapper
    """
        raise NotImplementedError('Process record needs to be customized')

    def mapper(self, _, line):
        f = None
        # # If we're on EC2 or running on a Hadoop cluster, pull files via S3
        if self.options.source in ['s3']:
            # Connect to Amazon S3 using anonymous credentials
            conn = boto.connect_s3(anon=True)
            pds = conn.get_bucket('aws-publicdatasets')
            # Start a connection to one of the WARC files
            k = Key(pds, line)
            f = warc.WARCFile(fileobj=GzipStreamFile(k))
        # # If we're local, use files on the local file system
        else:
            print 'Loading local file {}'.format(line)
            f = warc.WARCFile(fileobj=gzip.open(line))
        # ##
        for i, record in enumerate(f):
            for key, value in self.process_record(record):
                yield key, value
            self.increment_counter('commoncrawl', 'processed_records', 1)

    # TODO: Make the combiner use the reducer by default
    def combiner(self, key, value):
        yield key, sum(value)

    def reducer(self, key, value):
        yield key, sum(value)

    def configure_options(self):
        super(CCJob, self).configure_options()
        self.add_passthrough_option('--source', help="Provide the source of CC data")
