from collections import Counter
from mrcc import CCJob


class WordCount(CCJob):
    def process_record(self, record):
        if record['Content-Type'] != 'text/plain':
            return

        text = record.payload.read().decode('utf-8', 'strict')
        for word, count in Counter(text.split()).items():
            yield word, 1

        self.increment_counter('commoncrawl', 'processed_pages', 1)


if __name__ == '__main__':
    WordCount.run()
