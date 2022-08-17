import functools

from mrcc import CCJob
from mrjob.step import MRStep

try:
    # try to load the more efficient ujson
    import ujson as json
except ImportError:
    import json

try:
    # Python2
    from urlparse import urlparse
except ImportError:
    # Python3
    from urllib.parse import urlparse


class ServerAnalysis(CCJob):
    def process_record(self, record):
        # We're only interested in the JSON responses
        if record['Content-Type'] != 'application/json':
            return

        payload = record.payload.read()
        data = json.loads(payload)

        # Only interested in 'response, skip the 'metadata' and 'request' entries
        if data['Envelope']['WARC-Header-Metadata']['WARC-Type'] != 'response':
            return

        try:
            server = data['Envelope']['Payload-Metadata']['HTTP-Response-Metadata']['Headers']['Server']
            url = data['Envelope']['WARC-Header-Metadata']['WARC-Target-URI']
            # Extract the domain (aws.amazon.com) from the URL (http://aws.amazon.com/blogs/aws/ec2-maintenance/)
            domain = urlparse(url).netloc
            # Output the server and the domain
            yield server, tuple([domain])
            self.increment_counter('commoncrawl', 'processed_server_headers', 1)
        except KeyError:
            pass

        self.increment_counter('commoncrawl', 'processed_pages', 1)

    def reducer(self, key, value):
        # Take a list of tuples of domains, combine them, find only the unique ones (using a set), return a new tuple
        # (example: [('msn.com'), ('wikipedia.org', 'msn.com'), (...)])
        # Note: tuple is required as they will be hashed during the MapReduce process
        out_val = set(functools.reduce(lambda x, y: x + y, value))
        yield key, tuple(out_val)

    def reducer_count_total(self, key, value):
        # Return the total number of elements in value, which will only be one item in length
        # If it was more than one in length, we would turn this into a for loop
        yield key, len(next(value))

    def steps(self):
        return [
            MRStep(mapper=self.mapper, combiner=self.reducer, reducer=self.reducer),
            MRStep(reducer=self.reducer_count_total)
        ]


if __name__ == '__main__':
    ServerAnalysis.run()
