import logging
import re
import sys

import mrjob

try:
    # Python2
    from urlparse import urlparse
    from urlparse import urljoin
except ImportError:
    # Python3
    from urllib.parse import urlparse
    from urllib.parse import urljoin

from mrcc import CCJob
from mrjob.util import log_to_stream


LOG = logging.getLogger('SitemapExtractor')
log_to_stream(format="%(asctime)s %(levelname)s %(name)s: %(message)s",
              name='SitemapExtractor', stream=sys.stderr)


class SitemapExtractor(CCJob):
    """Extract sitemap URLs (http://www.sitemaps.org/) from robots.txt WARC files."""

    sitemap_pattern = re.compile(b'^sitemap:\\s*(\\S+)', re.IGNORECASE)

    def process_record(self, record):
        """emit: sitemap_url => [host]"""
        if record['WARC-Type'] != 'response':
            # we're only interested in the HTTP responses
            return

        url = None
        host = None
        n_sitemaps = 0
        self.increment_counter('commoncrawl', 'robots.txt processed', 1)

        for line in record.payload:
            match = SitemapExtractor.sitemap_pattern.match(line)
            if match:
                sitemap_url = match.group(1).strip()
                self.increment_counter('commoncrawl', 'sitemap URLs found', 1)
                n_sitemaps += 1
                try:
                    sitemap_url = sitemap_url.decode('utf-8', 'strict')
                except UnicodeDecodeError:
                    # invalid encoding, ignore
                    # LOG.warning('Invalid encoding of sitemap URL: %s', sitemap_url)
                    self.increment_counter('commoncrawl', 'sitemap URL invalid encoding', 1)
                    continue

                if url is None:
                    # first sitemap found: set base URL and get host from URL
                    url = record['WARC-Target-URI']
                    try:
                        host = urlparse(url).netloc.lower().lstrip('.')
                    except Exception as url_parse_error:
                        try:
                            LOG.warning('Invalid robots.txt URL: %s - %s',
                                        url, url_parse_error)
                        except UnicodeEncodeError as unicode_error:
                            LOG.warning('Invalid robots.txt URL - %s - %s',
                                        url_parse_error, unicode_error)
                        self.increment_counter('commoncrawl', 'invalid robots.txt URL', 1)
                        # skip this robots.txt record
                        return

                if not sitemap_url.startswith('http'):
                    sitemap_url = urljoin(url, sitemap_url)

                yield sitemap_url, [host]

        if n_sitemaps > 0:
            self.increment_counter('commoncrawl', 'robots.txt files announcing a sitemap', 1)
        if n_sitemaps > 50:
            LOG.warning('Unexpectedly large number of sitemaps (%d) announced in robots.txt URL: %s',
                        n_sitemaps, url)
            self.increment_counter('commoncrawl',
                                   'robots.txt files with more than 50 sitemap URLs', 1)

    def reducer(self, key, values):
        """Map sitemap URL to cross-submit hosts:
            sitemap_url => [host_1, ..., host_n]"""

        try:
            sitemap_uri = urlparse(key)
        except Exception as url_parse_error:
            try:
                LOG.warning('Invalid sitemap URL: %s - %s', key, url_parse_error)
            except UnicodeEncodeError as unicode_error:
                LOG.warning('Invalid sitemap URL - %s - %s', url_parse_error, unicode_error)
            self.increment_counter('commoncrawl', 'invalid sitemap URL', 1)
            return

        sitemap_host = sitemap_uri.netloc.lower().lstrip('.')
        cross_submit_hosts = set()

        for robots_txt_hosts in values:
            for robots_txt_host in robots_txt_hosts:
                if robots_txt_host != sitemap_host:
                    cross_submit_hosts.add(robots_txt_host)

        yield key, list(cross_submit_hosts)


if __name__ == '__main__':
    SitemapExtractor.run()
