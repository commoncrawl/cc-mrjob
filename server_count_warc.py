import re
from mrcc import CCJob

server_regex = re.compile(b'^server:\s*(.+)$', re.IGNORECASE)


class ServerCount(CCJob):
    """
    Count server names in HTTP headers contained in WARC files.

    Note: If WAT files are available the class ServerAnalysis should be used.
          WAT files are smaller and faster to process.
    """

    def process_record(self, record):
        if record['WARC-Type'] != 'response':
            # we're only interested in the HTTP responses
            return
        for line in record.payload:
            match = server_regex.match(line)
            if match:
                server = match.group(1).strip()
                yield server.decode('iso-8859-1'), 1
                return
            elif line.strip() == '':
                # empty line indicates end of HTTP response header
                yield '(no server in HTTP header)', 1
                return


if __name__ == '__main__':
    ServerCount.run()
