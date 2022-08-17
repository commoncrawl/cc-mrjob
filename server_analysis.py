try:
    # try to load the more efficient ujson
    import ujson as json
except ImportError:
    import json

from mrcc import CCJob


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
            yield server, 1
            self.increment_counter('commoncrawl', 'processed_server_headers', 1)
        except KeyError:
            pass

        self.increment_counter('commoncrawl', 'processed_pages', 1)


if __name__ == '__main__':
    ServerAnalysis.run()
