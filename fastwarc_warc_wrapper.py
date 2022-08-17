import io

import fastwarc.warc as fastwarc


class WARCFile():
    """Wrapper around fastwarc.warc.ArchiveIterator to mimic the behavior of
    warc.WARCFile when reading WARC/WAT/WET files"""
    def __init__(self, filename=None, fileobj=None):
        if fileobj is None:
            fileobj = open(filename, "rb")
        self.fileobj = fileobj
        self.iter = fastwarc.ArchiveIterator(self.fileobj, parse_http=False)

    def __iter__(self):
        try:
            while True:
                yield next(self)
        except  StopIteration:
            pass

    def __next__(self):
        return WARCRecord(next(self.iter))

    def close(self):
        self.fileobj.close()

    def tell(self):
        raise NotImplementedError('Use record.stream_pos instead')


class WARCRecord(object):
    """Replacement for warc.WARCRecord backed by warcio.recordloader.ArcWarcRecord"""
    def __init__(self, warc_record):
        self._rec = warc_record

    @property
    def type(self):
        """Record type"""
        return self._rec.record_type

    @property
    def url(self):
        """The value of the WARC-Target-URI header if the record is of type "response"."""
        return self._rec.headers.get('WARC-Target-URI')

    @property
    def ip_address(self):
        """The IP address of the host contacted to retrieve the content of this record. 

        This value is available from the WARC-IP-Address header."""
        return self._rec.headers.get('WARC-IP-Address')
    @property
    def date(self):
        """UTC timestamp of the record."""
        return self._rec.headers.get("WARC-Date")

    @property
    def checksum(self):
        return self._rec.headers.get('WARC-Payload-Digest')

    @property
    def payload(self):
        return io.BytesIO(self._rec.reader.read())

    def __getitem__(self, name):
        return self._rec.headers.get(name)

    def __setitem__(self, name, value):
        raise NotImplementedError('FastWARC headers cannot be modified')

    def __contains__(self, name):
        return name in self._rec.headers

    def __str__(self):
        return str(self._rec)

    def __repr__(self):
        return "<WARCRecord: type={} record_id={}>".format(
            self.type, self['WARC-Record-ID'])


class ARCFile(WARCFile):
    def __init__(self, filename=None, fileobj=None):
        raise NotImplementedError('FastWARC cannot read ARC files.')
