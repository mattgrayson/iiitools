#!/usr/bin/env python

from pymarc import ForgivingReader as Reader
# from pymarc import MARCReader as Reader
import sys

def process(file_num):
    reader = Reader(file('marc_%s.dat' % (file_num,)))
    records = []
    for rec in reader:
        print rec.title()
        print rec.isbn()
        print rec.author()
        print rec
        records.append(rec)
        print '+++++++++++++++++++++++++'
    print "%s records processed" % (len(records),)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 1:
        process(args[0])
    else:
        print "Usage:"
        print "  process_marc [file_number]"
        print "  ---------------------------"
        print ""