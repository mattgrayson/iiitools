#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
#from BeautifulSoup import BeautifulSoup

BASE_URI_RECORD = 'http://opac.utmem.edu/record=%s~S2'
BASE_URI_MARC = 'http://opac.utmem.edu/search~S2?/.%s/.%s/1%%2C1%%2C1%%2CB/marc~%s'
MARC_REGEX = re.compile(r'<pre>(.*)</pre>', re.DOTALL)
SUBFIELD_INDICATOR = '|'

def _contains(string, search_for):
    try:
        string.index(search_for)
        return True
    except ValueError:
        return False

def _get_page(url):
    try:
        return urllib2.urlopen(url).read()
    except urllib2.HTTPError:
        return None

def _starts_with_type(string, type_of):
    """docstring for _starts_with_type"""
    pass

def _unescape(text):
    """Removes HTML or XML character references 
      and entities from a text string.
      keep &amp;, &gt;, &lt; in the source code.
    from Fredrik Lundh
    http://effbot.org/zone/re-sub.htm#unescape-html
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                print "erreur de valeur"
                pass
        else:
            # named entity
            try:
                if text[1:-1] == "amp":
                    text = "&amp;amp;"
                elif text[1:-1] == "gt":
                    text = "&amp;gt;"
                elif text[1:-1] == "lt":
                    text = "&amp;lt;"
                else:
                    print text[1:-1]
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                print "keyerror"
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)



def record_exists(bibnumber):
    """
    >>> record_exists('b1012752')
    True
    >>> record_exists('b1012752...234245265')
    True
    >>> record_exists('bz1012752')
    False
    """
    record_page = _get_page(BASE_URI_RECORD % (bibnumber,))
    if record_page:
        record_does_not_exist = _contains(record_page, 'No Such Record')
        if record_does_not_exist:
            return False
        else:
            return True
    else:
        return False

def get_record(bibnumber):
    """
    >>> rec = get_record('b1012752')
    >>> print rec.fields['245']
    Annales de genetique. 
    """
    if record_exists(bibnumber):
        record_page = _get_page(BASE_URI_MARC % (3*(bibnumber,)))
        record_data = re.findall(MARC_REGEX, record_page)[0]
        record = IIIOpacRecord(record_data)
        return record
    else:
        print 'Nothing there ...'


class IIIOpacRecord(object):
    def __init__(self, raw_data =''):
        self.raw = raw_data
        self.fields = {}
        if self.raw != '':
            self.process_raw()
    
    def process_raw(self):
        """docstring for process"""
        raw_list = self.raw.strip().split('\n')
        raw_fields = {'leader': raw_list[0][7:]}
        last_tag = ''
        
        # First, iterate over raw data, cleaning and gathering up raw field data
        for field in raw_list[1:]:
            fnum = field[:3]
            if fnum[0] == ' ':
                raw_fields[last_tag] = "%s%s" % (raw_fields[last_tag], _unescape(field[6:].decode('latin1')))
            else:
                # field_str = field[4:].decode('latin1')
                # self.raw_fields[fnum] = field_str[:2] + 'a' + field_str[3:]
                raw_fields[fnum] = _unescape(field[4:].decode('latin1'))
                last_tag = fnum
        
        # Then, iterate over raw fields, processing each
        for tag in raw_fields:
            self.fields[tag] = IIIDataField(tag, raw_fields[tag])

class IIIDataField(object):
    def __init__(self, tag, raw_string=''):
        self.raw = raw_string
        self.tag = tag
        self.indicators = {'1': '', '2': ''}
        self.subfields = {}
        
        if self.raw != '':
            self.process_raw_string()
        
    def process_raw_string(self):
        raw = self.raw
        self.indicators['1'] = raw[0]
        self.indicators['2'] = raw[1]
        
        # For whatever reason Innovative leaves off the "a" subfield indicator.
        # Add it on, just to make looping over subfields simpler.
        subfields = u'a' + raw[3:]
        subfields_list = subfields.split('|')
        for sub in subfields_list:
            self.subfields[sub[0]] = sub[1:]
    
    def __repr__(self):
        return ' '.join([self.subfields[f].encode('utf8') for f in self.subfields])

if __name__ == "__main__":
    import doctest
    doctest.testmod()