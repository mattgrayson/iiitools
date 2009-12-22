#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
iiiutils

Utilities for interacting with III Millennium WebPac. Primary goal is to
retrieve and parse bibliographic records via the WebPac proto-MARC output.

Requirements:   Python 2.5 or later
                httplib2 <http://code.google.com/p/httplib2/>
                pymarc <http://github.com/edsu/pymarc>
"""

__author__ = "Matt Grayson (mattgrayson@uthsc.edu)"
__copyright__ = "Copyright 2009, Matt Grayson"
__license__ = "MIT"
__version__ = "1.02"

import httplib2
import re
import string
from pymarc import Record, Field
from string import Template

class Leader(object):
    """
    Class for accessing the MARC Leader
    Ported from http://github.com/rsinger/enhanced-marc/blob/master/lib/enhanced_marc/leader.rb
    
    Used by iiitools.Record to determine the record type.
    """
    def __init__(self, data):        
        self.data = data
    
    def __str__(self):
        return self.data
    
    def is_archival(self):
        return True if self[8] == 'a' else False
    
    @property
    def type_code(self):
        return self.data[6]
    
    @property
    def type(self):
        valid_types = ['a','t','g','k','r','o','p','e','f','c','d','i','j','m']
        try:
            valid_types.index(self.type_code)
        except ValueError:
            raise ValueError("Invalid Type!")
        
        rec_types = {
            'BKS': { 'type': r'[at]{1}',     'blvl': r'[acdim]{1}' },
            'SER': { 'type': r'[a]{1}',      'blvl': r'[bis]{1}' },
            'VIS': { 'type': r'[gkro]{1}',   'blvl': r'[abcdims]{1}' },
            'MIX': { 'type': r'[p]{1}',      'blvl': r'[cdi]{1}' },
            'MAP': { 'type': r'[ef]{1}',     'blvl': r'[abcdims]{1}' },
            'SCO': { 'type': r'[cd]{1}',     'blvl': r'[abcdims]{1}' },
            'REC': { 'type': r'[ij]{1}',     'blvl': r'[abcdims]{1}' },
            'COM': { 'type': r'[m]{1}',      'blvl': r'[abcdims]{1}' }
        }
        
        for type in rec_types:            
            if re.match(rec_types[type]['type'], self.type_code) and re.match(rec_types[type]['blvl'],self.blvl_code):
                return type
        
        raise ValueError("Invalid BLvl!")
    
    @property
    def blvl_code(self):
        r"""Returns bibliographic level code from self.data"""
        return self.data[7]
    
    @property
    def bibliographic_level(self):
        r"""Returns label for bibliographic level code from self.data"""
        blvls = {
            'a': 'Monographic component part',
            'b': 'Serial component part',
            'c': 'Collection',
            'd': 'Subunit',
            'i': 'Integrating resource',
            'm': 'Monograph/Item',
            's': 'Serial'
        }
        return blvls[self.blvl_code]    
    
    @property
    def elvl_code(self):
        r"""Returns encoding level code from self.data"""
        return self.data[17]
    
    @property
    def encoding_level(self):
        r"""Returns label for encoding level code from self.data"""
        elvls = {
            ' ': 'Full',
            '1': 'Full, not examined',
            '2': 'Less-than-full',
            '3': 'Abbreviated',
            '4': 'Core',
            '5': 'Partial',
            '7': 'Minimal',
            '8': 'Prepublication',
            'I': 'Full-level input by OCLC participants',
            'K': 'Less-than-full input by OCLC participants',
            'L': 'Full-level input added from a batch process',
            'M': 'Less-than-full added from a batch process',
            'E': 'System-identified MARC error in batchloaded record',
            'J': 'Deleted record'
        }
        return elvls[self.elvl_code]
    
    @property
    def desc_code(self):
        r"""Returns descriptive cataloging form code from self.data"""
        return self.data[18]
    
    @property
    def descriptive_cataloging_form(self):
        r"""
        Returns label for descriptive cataloging form code from self.data
        """
        codes = {' ': 'Non-ISBD', 'a': 'AACR2', 'i': 'ISBD', 'u': 'Unknown'}
        return codes[self.desc_code]



class Record(Record):
    r"""
    Extension to pymarc.Record. Some methods and properties are just 
    convenience accessors, some are specific to III and others are specific 
    to opac.uthsc.edu (i.e. call_number).
    """
    
    PRECEEDING_ENTRY_LABELS = [
        "Continues",
        "Continues in part",
        "Supersedes",
        "Supersedes in part",
        "Formed by the union of",
        "Absorbed",
        "Absorbed in part",
        "Separated from",
    ]

    SUCCEEDING_ENTRY_LABELS = [
        "Continued by",
        "Continued in part by",
        "Superseded by",
        "Superseded in part by",
        "Absorbed by",
        "Absorbed in part by",
        "Split into",
        "Merged with",
        "Changed back to",
    ]

    ISSN_ISBN_PATTERN = re.compile('^([\w\d-]+)')

    def __init__(self, *args, **kwargs):
        super(Record, self).__init__(*args, **kwargs)
        self.type = None
        self.bibnumber = None
        self.raw = None
        self.src_host = ''
        self.record_url = ''
        self.record_marc_url = ''
    
    def parse_leader(self):
        """Parses leader data to try to detect the record type."""
        self.leader = Leader(self.leader)
        self.type = self.leader.type

    def has_link(self):
        return True if self['856'] else False

    # Turn certain pymarc.Record attribute methods into properties
    addedentries = property(Record.addedentries)
    location = property(Record.location)        
    pubyear = property(Record.pubyear)
    
    # Accessor methods for various fields
    @property
    def access_restrictions(self):
        return "; ".join([f.format_field() for f in self.get_fields('506')])
    
    @property
    def author(self):
        for field in ('100','110','111'):
            if self[field]:
                return self[field].format_field()
        return ''
    
    @property
    def author_name(self):
        for field in ('100','110','111'):
            if self[field]:
                return self[field].get_subfields('a')[0]
        return ''
    
    @property
    def author_dates(self):
        for field in ('100','110','111'):
            if self[field] and self[field]['c']:
                return self[field].get_subfields('c')
        return []

    @property
    def other_authors(self):
        for field in ('700','710','711'):
            if self.get_fields(field):
                return [f.format_field() for f in self.get_fields(field)]
        return []

    @property
    def call_number(self):
        return self['096'].format_field() if self['096'] else ''

    @property
    def comp_file_characteristics(self):
        return self['256'].format_field() if self['256'] else ''

    @property
    def contents(self):
        return " ".join([f.format_field() for f in self.get_fields('505')])

    @property
    def edition(self):
        return self['250'].format_field() if self['250'] else ''

    @property
    def entry_preceding_is_union(self):
        if self['780']:
            return True if self['780'].indicator2 == ("4") else False
        return false

    @property
    def entry_notes(self):
        return [f.format_field() for f in self.get_fields('580')]

    @property
    def entry_preceding(self):
        return [{
                    'title': ("%s %s" % (f['a'], f['t'])).strip(),
                    'issn': f['x'] if f['x'] else '',
                    'rel': self.PRECEEDING_ENTRY_LABELS[int(f.indicator2)]
                } for f in self.get_fields('780')]

    @property
    def entry_succeeding(self):
        return [{
                    'title': ("%s %s" % (f['a'], f['t'])).strip(),
                    'issn': f['x'] if f['x'] else '',
                    'rel': self.SUCCEEDING_ENTRY_LABELS[int(f.indicator2)] if f.indicator2.strip() else ''
                } for f in self.get_fields('785')]

    @property
    def isbn(self):
        if self.get_fields('020'):
            return [self.ISSN_ISBN_PATTERN.match(f['a']).group() for f in self.get_fields('020') if self.ISSN_ISBN_PATTERN.match(f['a'])]
        else:
            return []

    @property
    def issn(self):
        if self.get_fields('022'):
            return [self.ISSN_ISBN_PATTERN.match(f['a']).group() for f in self.get_fields('022') if self.ISSN_ISBN_PATTERN.match(f['a'])]
        else:
            return []

    @property
    def links(self):
        if self.has_link():
            return [{'url': f.get_subfields('u')[0], 'label': f.get_subfields('z')[0] } for f in self.get_fields('856')]
        return []

    @property
    def notes(self):
        ignore = [505,506,520,580,590] # 590 is a local notes field that isn't particularly relevant outside of III
        notes = []
        for field in range(500, 599):
            if field in ignore: continue
            notes += [f.format_field() for f in self.get_fields(field.__str__())]
        return notes
    
    @property
    def physical_description(self):
        return "; ".join([f.format_field() for f in self.get_fields('300')])
    
    @property
    def publishers(self):
        return [f.format_field() for f in self.get_fields('260')]
    
    @property
    def publisher_names(self):
        return [strip_end_punctuation(f['b']) for f in self.get_fields('260') if f['b']]
    
    @property
    def pub_dates(self):
        return [f.format_field() for f in self.get_fields('362')]

    @property
    def pub_frequency(self):
        return self['310'].format_field() if self['310'] else ''

    @property
    def former_pub_frequencies(self):
        return [f.format_field() for f in self.get_fields('321')]

    @property
    def series(self):
        for field in ('490','440'):
            return [f.format_field() for f in self.get_fields(field)]
        return []

    @property
    def series_main(self):
        return [f.format_field() for f in self.get_fields('760')]

    @property
    def subjects(self):
        return [f.format_field() for f in self.get_fields('650')]

    @property
    def summary(self):
        return " ".join([f.format_field() for f in self.get_fields('520')])

    @property
    def supplements(self):
        return [f.format_field() for f in self.get_fields('770')]

    @property
    def supplement_parents(self):
        return [f.format_field() for f in self.get_fields('772')]
    
    @property
    def title(self):        
        t = self['245']['a'] if self['245']['a'] else ''
        t = "%s %s" % (t, self['245']['b']) if self['245']['b'] else t
        t = "%s %s" % (t, self['245']['c']) if self['245']['c'] else t
        return strip_end_punctuation(t)
    
    @property
    def title_varying_forms(self):
        return [f.format_field() for f in self.get_fields('246')]

    @property
    def title_abbrv(self):
        return [f.format_field() for f in self.get_fields('210')]

    @property
    def title_key(self):
        return [f.format_field() for f in self.get_fields('222')]

    @property
    def title_uniform_related(self):
        return [f.format_field() for f in self.get_fields('730')]

    @property
    def title_uniform(self):
        return self['130'].format_field() if self['130'] else ''

    @property
    def check_digit(self):
        """Calculates the check digit from bib record number.

        The algorithm to calculate check digits is found at the following URL:
        http://csdirect.iii.com/manual/rmil_records_numbers.html
        """
        if not self.bibnumber:
            return None
        else:        
            total = 0
            multiplier = 2
            for i in reversed(self.bibnumber[1:]):
                i = int(i)
                assert 0 <= i <= 9
                i *= multiplier
                total += i
                multiplier += 1
            dig = total % 11
            return str(dig) if dig != 10 else 'x'


class Reader(object):
    """
    Main interface for retrieving records from III Millennium WebPac.
    """
    
    URI_FOR_RECORD = Template('$host/record=$bibnum~S$scope')
    URI_FOR_MARC = Template('$host/search~S$scope?/.$bibnum/.$bibnum/1%2C1%2C1%2CB/marc~$bibnum')
    URI_FOR_HOLDINGS = Template('$host/search~S$scope/.$bibnum/.$bibnum/1,1,1,B/holdings')
    MARC_REGEX = re.compile(r'<pre>(.*)</pre>', re.DOTALL)
    
    def __init__(self, opac_host, scope=''):        
        self.host = opac_host
        self.scope = scope
        self.conn = httplib2.Http()    
    
    def get_page(self, url):
        resp, content = self.conn.request(url)
        if resp.status < 400:
            return content
        else:
            return None            
    
    def record_exists(self, bibnumber):
        r"""
        >>> reader = Reader('http://opac.uthsc.edu')
        >>> reader.record_exists('b1012752')
        True
        >>> reader.record_exists('b1012752...234245265')
        True
        >>> reader.record_exists('bz1012752')
        False
        """
        record_page = self.get_page(self.URI_FOR_RECORD.substitute(host=self.host, bibnum=bibnumber, scope=self.scope))
        if record_page and record_page.find('No Such Record') == -1:
            return True
        else:
            return False
    
    def get_record(self, bibnumber):
        r"""
        >>> reader = Reader('http://opac.uthsc.edu')
        >>> record = reader.get_record('b1012752')
        >>> print record.title
        Annales de genetique
        >>> print record.urls
        [{'url': 'http://library.uthsc.edu/ems/eresource/3581', 'label': 'Full text  at ScienceDirect: 43(1) Jan 2000 - 47(4) Dec 2004'}]
        >>> print record.subjects
        ['Genetics -- Periodicals.']
        """
        if not bibnumber.startswith('b'):
            raise ValueError("Invalid bib record number.")
        
        if self.record_exists(bibnumber):
            record_page = self.get_page(self.URI_FOR_MARC.substitute(host=self.host, bibnum=bibnumber, scope=self.scope))
            record_data = re.findall(self.MARC_REGEX, record_page)[0]
            record = self.decode_record(record_data)
            if record:
                # Store relevant system data in record object
                record.bibnumber = bibnumber
                record.raw = record_data.decode('latin1')
                record.src_host = self.host
                record.record_url = self.URI_FOR_RECORD.substitute(host=self.host, bibnum=bibnumber, scope=self.scope)
                record.record_marc_url = self.URI_FOR_MARC.substitute(host=self.host, bibnum=bibnumber, scope=self.scope)
            return record
        else:
            return None
    
    def crawl_records(self, bib_start, bib_end):
        r"""
        >>> reader = Reader('http://opac.uthsc.edu', 2)
        >>> records = reader.crawl_records('b1053852', 'b1053862')
        >>> len(records)
        9
        >>> records[0].title
        'Molecular biology of the cell / Bruce Alberts ... [et  al.] ; with problems by John Wilson, Tim Hunt'
        """
        if not bib_start.startswith('b') or not bib_end.startswith('b'):
            raise ValueError("Invalid bib record number(s).")
    
        bib_start = int(bib_start[1:])
        bib_end = int(bib_end[1:])+1
        records = []
        
        for num in range(bib_start, bib_end):
            bibnum = "b%s" % (num,)
            record = self.get_record(bibnum)
            if record:
                records.append(record)
        return records    
    
    def decode_record(self, record):
        r"""
        >>> reader = Reader('http://opac.uthsc.edu', 2)
        >>> raw = "\nLEADER 00000cas  2200517 a 4500 \n001    1481253 \n003    OCoLC \n005    19951109120000.0 \n008    750727c19589999fr qrzp   b   0   b0fre d \n010    sn 86012727 \n022    0003-3995 \n030    AGTQAH \n035    0062827|bMULS|aPITT  NO.  0639600000|asa64872000|bFULS \n040    MUL|cMUL|dFUL|dOCL|dCOO|dNYG|dHUL|dSER|dAIP|dNST|dAGL|dDLC\n       |dTUM \n041 0  engfre|bgeritaspa \n042    nsdp \n049    TUMS \n069 1  A32025000 \n210 0  Ann. genet. \n222  0 Annales de genetique \n229 00 Annales de genetique \n229    Ann Genet \n242 00 Annals on genetics \n245 00 Annales de genetique. \n260    Paris :|bExpansion scientifique,|c1958-2004. \n300    v. :|bill. &#59;|c28 cm. \n310    Quarterly \n321    Two no. a year \n362 0  1,1958-47,2004. \n510 1  Excerpta medica \n510 1  Index medicus|x0019-3879 \n510 2  Biological abstracts|x0006-3169 \n510 2  Chemical abstracts|x0009-2258 \n510 2  Life sciences collection \n510 0  Bulletin signaletique \n510 0  Current contents \n546    French and English, with summaries in German, Italian, and\n       Spanish. \n550    Journal of the Societe francaise de genetique. \n650  2 Genetics|vPeriodicals. \n710 2  Societ\xe9 fran\xe7aise de genetique. \n785 00 |tEuropean journal of medical genetics.  \n856 41 |uhttp://library.uthsc.edu/ems/eresource/3581|zFull text \n       at ScienceDirect: 43(1) Jan 2000 - 47(4) Dec 2004 \n936    Unknown|ajuin 1977 \n"
        >>> record = reader.decode_record(raw)
        >>> print record.title
        Annales de genetique
        """
        
        pseudo_marc = record.strip().split('\n')
        raw_fields = []
        if pseudo_marc[0][0:6] == 'LEADER':
            record = Record()
            record.leader = pseudo_marc[0][7:].strip()
        else:
            return None

        for field in pseudo_marc[1:]:
            tag = field[:3]
            data = unescape_entities(field[6:].decode('latin1')).encode('utf8')
                        
            if tag.startswith(' '):
                # Additional field data needs to be prepended with an extra space 
                # for certain fields ...
                for special_tag in ('55','260'):
                    data = " %s" % (data,) if tag.startswith(special_tag) else data                
                raw_fields[-1]['value'] = "%s%s" % (raw_fields[-1]['value'], data)
                raw_fields[-1]['raw'] = "%s%s" % (raw_fields[-1]['raw'], field.strip())
            else:
                data = data if (tag < '010' and tag.isdigit()) else "a%s" % (data,)
                raw_fields.append({
                    'tag': tag, 
                    'indicator1': field[3], 
                    'indicator2': field[4], 
                    'value': data, 
                    'raw': field.strip()
                })
        
        for raw in raw_fields:
            tag = raw['tag']
            data = raw['value'].strip()
            field = Field(tag=tag, indicators=[raw['indicator1'], raw['indicator2']], data=data)
            if not field.is_control_field():
                for sub in data.split('|'):
                    try:
                        field.add_subfield(sub[0].strip(), sub[1:].strip())
                    except Exception:
                        # Skip blank/empty subfields
                        continue
            record.add_field(field)
            
        record.parse_leader()
        return record
    
    def get_items_for_record(self, bibnumber):
        r"""
        >>> reader = Reader('http://opac.uthsc.edu', 2)
        >>> items = reader.get_items_for_record('b1012752')
        >>> items[0]
        {'status': 'AVAILABLE', 'call_num': 'v.47 no.4 Oct/Dec 2004', 'url': '', 'location': 'Journal Collection'}
        >>> len(items)
        56
        """
        if not bibnumber.startswith('b'):
            raise ValueError("Invalid bib record number.")
        
        if self.record_exists(bibnumber):
            from lxml import html
            url = self.URI_FOR_HOLDINGS.substitute(host=self.host, 
                    bibnum=bibnumber, scope=self.scope)
            record_holdings_page = self.get_page(url)
            items_data = html.document_fromstring(record_holdings_page)
            table_rows = items_data.cssselect('.bibItems tr.bibItemsEntry')
            table_rows.reverse() # Sort from newest to oldest
            items = []
            for item in table_rows:                
                if item[1].cssselect('a'):
                    url = item[1].cssselect('a')[0].get('href').encode('utf8')
                else:
                    url = ''
                items.append({
                    'location': item[0].text_content().strip().encode('utf8'), 
                    'call_num': item[1].text_content().strip().encode('utf8'), 
                    'status': item[2].text_content().strip().encode('utf8'),
                    'url': url
                })
            return items
        else:
            return []

def unescape_entities(text):
    r"""
    Removes HTML or XML character references and entities from a text string.
    Keeps &amp;, &gt;, &lt; in the source code. Based on original from Fredrik 
    Lundh. http://effbot.org/zone/re-sub.htm#unescape-html
      
    Note: 'text' must be a Unicode string
    
    >>> output = unescape_entities(u'This leads to &raquo; that')
    >>> print output.encode('utf8')
    This leads to » that
    """
    def fixup(m):
        import htmlentitydefs
        
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                print "Some kind of ValueError encountered ..."
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
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                print "keyerror"
                pass
        return text # leave as is
    regex = re.compile(ur'&#?\w+;', re.UNICODE)    
    return regex.sub(fixup, text)

def strip_end_punctuation(text):
    return text[:-1] if text[-1] in string.punctuation else text
    

if __name__ == "__main__":
    import doctest
    doctest.testmod()