#!/usr/bin/env python
from telnetlib import Telnet

# http://docs.python.org/library/telnetlib.html
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
t.write("59\n")
t.read_until("Choose one (T,P,A,E,R,S,L,X,K,O,N,C,U,Q)")
t.write("x\n")
t.read_until("Choose one (F,B,P,E,M,Q)")
t.write("m\n")
# t.read_until("Choose one (P,E,C,Q)")
# t.write("c\n")
t.read_until("Press the SPACE BAR to proceed  (or <ESC> to quit)")
t.write(" ")
out = t.read_until("Export complete, stop your capture program now", 30)
t.close()

txt = open('telnet.txt','w')
txt.write(out)
txt.close()