import gzip
import logging
import os.path as Path

from tempfile import TemporaryFile

import boto3
import botocore
import warc

from mrjob.job import MRJob
from mrjob.util import log_to_stream

from gzipstream import GzipStreamFile


# Set up logging - must ensure that log_to_stream(...) is called only once
# to avoid duplicate log messages (see https://github.com/Yelp/mrjob/issues/1551).
LOG = logging.getLogger('CCJob')
log_to_stream(format="%(asctime)s %(levelname)s %(name)s: %(message)s", name='CCJob')


class CCJob(MRJob):
    """
    A simple way to run MRJob jobs on Common Crawl data
    """
    def configure_args(self):
        super(CCJob, self).configure_args()
        self.pass_arg_through('--runner')
        self.add_passthru_arg('--s3_local_temp_dir',
                              help='local temporary directory to buffer content from S3',
                              default=None)
        self.add_passthru_arg('--bucket',
                              help='bucket to read data from S3',
                              default='commoncrawl')

    def process_record(self, record):
        """
        Override process_record with your mapper
        """
        raise NotImplementedError('Process record needs to be customized')

    def mapper(self, _, line):
        """
        The Map of MapReduce
        If you're using Hadoop or EMR, it pulls the Common Crawl files from S3,
        otherwise it pulls from the local filesystem. Dispatches each file to
        `process_record`.
        """
        # If we're on EC2 or running on a Hadoop cluster, pull files via S3
        if self.options.runner in ['emr', 'hadoop']:
            # Connect to Amazon S3 using anonymous credentials
            boto_config = botocore.client.Config(
                read_timeout=180,
                retries={'max_attempts' : 20})
            if self.options.bucket != 'commoncrawl':
                # use defaults if data is read from a custom bucket
                boto_config = botocore.client.Config()
            s3client = boto3.client('s3', config=boto_config)
            # Verify bucket
            try:
                s3client.head_bucket(Bucket=self.options.bucket)
            except botocore.exceptions.ClientError as exception:
                LOG.error('Failed to access bucket "%s": %s',
                          self.options.bucket, exception)
                return
            # Check whether WARC/WAT/WET input exists
            try:
                s3client.head_object(Bucket=self.options.bucket,
                                     Key=line)
            except botocore.client.ClientError as exception:
                LOG.error('Input not found: %s', line)
                return
            # Start a connection to one of the WARC/WAT/WET files
            LOG.info('Loading s3://%s/%s', self.options.bucket, line)
            try:
                temp = TemporaryFile(mode='w+b',
                                     dir=self.options.s3_local_temp_dir)
                s3client.download_fileobj(self.options.bucket, line, temp)
            except botocore.client.ClientError as exception:
                LOG.error('Failed to download %s: %s', line, exception)
                return
            temp.seek(0)
            ccfile = warc.WARCFile(fileobj=(GzipStreamFile(temp)))
        # If we're local, use files on the local file system
        else:
            line = Path.join(Path.abspath(Path.dirname(__file__)), line)
            LOG.info('Loading local file %s', line)
            ccfile = warc.WARCFile(fileobj=gzip.open(line))

        for _i, record in enumerate(ccfile):
            for key, value in self.process_record(record):
                yield key, value
            self.increment_counter('commoncrawl', 'processed_records', 1)

    def combiner(self, key, values):
        """
        Combiner of MapReduce
        Default implementation just calls the reducer which does not make
        it necessary to implement the combiner in a derived class. Only
        if the reducer is not "associative", the combiner needs to be
        overwritten.
        """
        for key_val in self.reducer(key, values):
            yield key_val

    def reducer(self, key, values):
        """
        The Reduce of MapReduce
        If you're trying to count stuff, this `reducer` will do. If you're
        trying to do something more, you'll likely need to override this.
        """
        yield key, sum(values)
