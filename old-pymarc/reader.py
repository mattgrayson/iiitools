from cStringIO import StringIO

from pymarc import Record, AlephSequentialRecord
from pymarc.exceptions import RecordLengthInvalid

class Reader(object):
    """
    A base class for all iterating readers in the pymarc package. 
    """
    def __iter__(self):
        return self

class MARCReader(Reader):
    """
    An iterator class for reading a file of MARC21 records. 

    Simple usage:

        from pymarc import MARCReader

        ## pass in a file object
        reader = MARCReader(file('file.dat'))
        for record in reader:
            ...

        ## pass in marc in transmission format 
        reader = MARCReader(rawmarc)
        for record in reader:
            ...
    """
    def __init__(self, marc_target):
        """
        The constructor to which you can pass either raw marc or a file-like
        object. Basically the argument you pass in should be raw MARC in 
        transmission format or an object that responds to read().
        """
        super(MARCReader, self).__init__()
        if (hasattr(marc_target, "read") and callable(marc_target.read)):
            self.file_handle = marc_target
        else: 
            self.file_handle = StringIO(marc_target)

    def next(self):
        """
        To support iteration. 
        """
        first5 = self.file_handle.read(5)
        if not first5:
            raise StopIteration
        if len(first5) < 5:
            raise RecordLengthInvalid
        
        length = int(first5)
        chunk = self.file_handle.read(length - 5)
        chunk = first5 + chunk
        record = Record(chunk)
        return record 

class ForgivingReader(MARCReader):
    """
    """
    def __init__(self, marc_target):
        super(ForgivingReader, self).__init__(marc_target)
        self.file_lines = self.file_handle.read().split(chr(0x1D))
        self.current_index = 0

    def next(self):
        """
        To support iteration.
        """
        if self.current_index == len(self.file_lines):
            self.current_index = 0
            raise StopIteration 

        chunk = self.file_lines[self.current_index]
        self.current_index += 1
        return Record(chunk)
        


class AlephSequentialReader(MARCReader):
    """
    An iterator class for reading a file of MARC records in Aleph Sequential
    format. Based on Tim Prettyman's MARC::File::AlephSeq Perl code.
    """
    def __init__(self, marc_target):
        super(AlephSequentialReader, self).__init__(marc_target)

    def next(self):
        """
        To support iteration.
        """
        record_data = ''
        line = self.file_handle.readline()
        if not line:
            raise StopIteration
        key = line[0:9]
        current_key = key
        
        while key == current_key:
            record_data += line
            position = self.file_handle.tell()
            line = self.file_handle.readline()
            key = line[0:9]
        
        self.file_handle.seek(position)
        record = AlephSequentialRecord(record_data)
        return record

def map_records(f, *files):
    """
    Applies a given function to each record in a batch. You can
    pass in multiple batches.

    >>> def print_title(r): 
    >>>     print r['245']
    >>> 
    >>> map_records(print_title, file('marc.dat'))
    """
    for file in files:
        map(f, MARCReader(file))

