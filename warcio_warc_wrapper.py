import io

import warcio


class WARCFile(warcio.ArchiveIterator):
    """Wrapper around warcio.ArchiveIterator to mimic the behavior of
    warc.WARCFile when reading WARC/ARC/WAT/WET files"""
    def __init__(self, filename=None, fileobj=None):
        if fileobj is None:
            fileobj = open(filename, "rb")
        self.fileobj = fileobj
        super().__init__(self.fileobj, no_record_parse=True, arc2warc=True)

    def __iter__(self):
        try:
            while True:
                yield next(self)
        except  StopIteration:
            pass

    def __next__(self):
        return WARCRecord(super().__next__())

    def close(self):
        self.fileobj.close()

    def tell(self):
        return self_archive_iter.get_record_offset()


class WARCRecord(object):
    """Replacement for warc.WARCRecord backed by warcio.recordloader.ArcWarcRecord"""
    def __init__(self, arc_warc_record):
        self._rec = arc_warc_record

    @property
    def type(self):
        """Record type"""
        return self._rec.rec_type

    @property
    def url(self):
        """The value of the WARC-Target-URI header if the record is of type "response"."""
        return self._rec.rec_headers.get_header('WARC-Target-URI')

    @property
    def ip_address(self):
        """The IP address of the host contacted to retrieve the content of this record. 

        This value is available from the WARC-IP-Address header."""
        return self._rec.rec_headers.get_header('WARC-IP-Address')

    @property
    def date(self):
        """UTC timestamp of the record."""
        return self._rec.rec_headers.get_header("WARC-Date")

    @property
    def checksum(self):
        return self._rec.rec_headers.get_header('WARC-Payload-Digest')

    @property
    def payload(self):
        return io.BytesIO(self._rec.content_stream().read())

    def __getitem__(self, name):
        return self._rec.rec_headers.get_header(name)

    def __setitem__(self, name, value):
        self._rec.rec_headers.replace_header(name, value)

    def __contains__(self, name):
        return name in self._rec.rec_headers

    def __str__(self):
        return str(self._rec)

    def __repr__(self):
        return "<WARCRecord: type={} record_id={}>".format(
            self.type, self['WARC-Record-ID'])


class ARCFile(WARCFile):
    # warcio converts ARC records on the fly: no need to implement anything
    pass


