import re
from collections import Counter
from mrcc import CCJob


def get_tag_count(data, ctr=None):
    """Extract the names and total usage count of all the opening HTML tags in the document"""
    if ctr is None:
        ctr = Counter()
    # Convert the document to lower case as HTML tags are case insensitive
    ctr.update(HTML_TAG_PATTERN.findall(data.lower()))
    return ctr


# Optimization: compile the regular expression once so it's not done each time
# The regular expression looks for (1) a tag name using letters (assumes lowercased input) and numbers
# and (2) allows an optional for a space and then extra parameters, eventually ended by a closing >
HTML_TAG_PATTERN = re.compile(b'<([a-z0-9]+)[^>]*>')
# Let's check to make sure the tag counter works as expected
assert get_tag_count(b'<html><a href="..."></a><h1 /><br/><p><p></p></p>') == {b'html': 1, b'a': 1, b'p': 2, b'h1': 1, b'br': 1}


class TagCounter(CCJob):
    def process_record(self, record):
        # WARC records have three different types:
        #  ["application/warc-fields", "application/http; msgtype=request", "application/http; msgtype=response"]
        # We're only interested in the HTTP responses
        if record['Content-Type'] == 'application/http; msgtype=response':
            payload = record.payload.read()
            # The HTTP response is defined by a specification: first part is headers (metadata)
            # and then following two CRLFs (newlines) has the data for the response
            headers, body = payload.split(b'\r\n\r\n', 1)
            if b'Content-Type: text/html' in headers:
                # We avoid creating a new Counter for each page as that's actually quite slow
                tag_count = get_tag_count(body)
                for tag, count in tag_count.items():
                    yield tag.decode('ascii'), count
                self.increment_counter('commoncrawl', 'processed_pages', 1)


if __name__ == '__main__':
    TagCounter.run()
