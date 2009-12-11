#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telnetlib import Telnet
import sys

def download(list_num):
    
    def regenerate_list(list_num):
        # 45, List of e-journals
        if list_num == "45":
            t.write("n\n")
            t.write("y\n")
            t.read_until("Choose one (B,O,C,A,I,P,R,V,N,Q)")
            t.write("b\n")
            t.read_until("Find BIBLIOGRAPHIC records that satisfy the following conditions")
            t.write("3\n")
            t.write("=\n")
            t.write("ejour\n")
            t.write("a\n")
            t.write("7\n")
            t.write("~\n")
            t.write("n\n")
            t.write("a\n")
            t.write("!\n")
            t.write("856\n")
            t.write("h\n")
            t.write("http\n")
            print "Searching ..."
            t.write("s\n")
            t.read_until("What name would you like to give this file of records?")
            t.write("E-journals with 856\n")
            t.read_until("Press <SPACE> to continue")    
            t.write(" ")
        # 59, List of e-books
        elif list_num == "59":
            t.write("n\n")
            t.write("y\n")
            t.read_until("Choose one (B,O,C,A,I,P,R,V,N,Q)")
            t.write("b\n")
            t.read_until("Find BIBLIOGRAPHIC records that satisfy the following conditions")
            t.write("3\n")
            t.write("=\n")
            t.write("ebook\n")
            t.write("a\n")
            t.write("7\n")
            t.write("~\n")
            t.write("n\n")
            t.write("a\n")
            t.write("!\n")
            t.write("856\n")
            t.write("h\n")
            t.write("http\n")    
            print "Searching ..."
            t.write("s\n")
            t.read_until("What name would you like to give this file of records?")
            t.write("E-books with 856\n")
            t.read_until("Press <SPACE> to continue")    
            t.write(" ")
    
    
    # http://docs.python.org/library/telnetlib.html
    print "Opening telnet connection ..."
    
    t = Telnet('opac.utmem.edu')
    t.read_until("login: ")
    t.write("infoserv\n")
    t.read_until("Password:")
    t.write("sugar\n")
    t.read_until("Choose one (S,D,C,M,I,A,X)")
    t.write("m\n")
    t.read_until("Choose one (I,A,G,P,R,C,L,S,M,Q)")
    t.write("l\n")
    t.read_until("initials : ")
    t.write("jmg\n")
    t.read_until("password : ")
    t.write("g079sox\n")
    t.read_until("Choose one (1-80,F,Q)")
    t.write("%s\n" % (list_num,))
    t.read_until("Choose one (T,P,A,E,R,S,L,X,O,N,C,U,Q)")
    
    # Regenerate list ...
    print "Regenerating requested list of records ..."
    regenerate_list(list_num)
    
    print "Exporting list ..."
    t.write("x\n")
    t.read_until("Choose one (F,B,P,E,M,Q)")
    t.write("m\n")
    t.read_until("Press the SPACE BAR to proceed  (or <ESC> to quit)")
    t.write(" ")
    out = t.read_until("Export complete, stop your capture program now", 30)
    t.close()

    marcdata = file('marc_%s.dat' % (list_num,), 'w')
    rawdata = out.splitlines()[1:] # First line will always be empty
    for line in rawdata:
        # Keep every line except last "export complete" msg
        if not line.startswith('Export complete'):
            line = line.decode('ascii','ignore')	
            marcdata.write(line)
            marcdata.write(chr(0x1D))
    marcdata.close()

    print "Download complete!"

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 1:
        download(args[0])
    else:
        print "Usage:"
        print "  download_list [list_number]"
        print "  ---------------------------"
        print "  "