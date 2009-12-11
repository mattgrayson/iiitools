#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib2
import re
from pymarc import Record, Field

class Leader(object):
    """
    Class for accessing the MARC Leader
    Ported from http://github.com/rsinger/enhanced-marc/blob/master/lib/enhanced_marc/leader.rb
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
        return self.data[7]
    
    @property
    def bibliographic_level(self):
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
        return self.data[17]
    
    @property
    def encoding_level(self):
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
        return self.data[18]
    
    @property
    def descriptive_cataloging_form(self):
        codes = {' ': 'Non-ISBD', 'a': 'AACR2', 'i': 'ISBD', 'u': 'Unknown'}
        return codes[self.desc_code]



class IIIRecord(Record):
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

    """docstring for IIIRecord"""
    def __init__(self, *args, **kwargs):
        super(IIIRecord, self).__init__(*args, **kwargs)
        self.type = None
        self.bibnumber = None
        self.raw = None
    
    def parse_leader(self):
        self.leader = Leader(self.leader)
        self.type = self.leader.type

    def has_url(self):
        return True if self['856'] else False

    # Turn certain pymarc.Record attribute methods into properties
    title = property(Record.title)        
    author = property(Record.author)    
    addedentries = property(Record.addedentries)
    location = property(Record.location)        
    pubyear = property(Record.pubyear)

    @property
    def access_restrictions(self):
        return "; ".join([f.format_field() for f in self.get_fields('506')])
    
    @property
    def author_name(self):
        for field in ('100','110','111'):
            if self[field]:
                return self[field].get_subfields('a')[0]
        return ''
    
    @property
    def author_dates(self):
        for field in ('100','110','111'):
            if self[field]:
                return self[field].get_subfields('c')
        return ''

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
    def description_physical(self):
        return "; ".join([f.format_field() for f in self.get_fields('300')])

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
                    'title': "{0} {1}".format(f['a'], f['t']).strip(),
                    'issn': f['x'],
                    'rel': self.PRECEEDING_ENTRY_LABELS[int(f.indicator2)]
                } for f in self.get_fields('780')]

    @property
    def entry_succeeding(self):
        return [{
                    'title': "{0} {1}".format(f['a'], f['t']).strip(),
                    'issn': f['x'],
                    'rel': self.SUCCEEDING_ENTRY_LABELS[int(f.indicator2)]
                } for f in self.get_fields('785')]

    @property
    def isbn(self):
        try:
            # if anyone ever cares alot about performance
            # this compilation could be moved out and compiled once
            isbn = [self.ISSN_ISBN_PATTERN.match(f['a']).group() for f in self.get_fields('020') if self.ISSN_ISBN_PATTERN.match(f['a'])]
        except TypeError:
            isbn = []
        return isbn

    @property
    def issn(self):
        try:
            # if anyone ever cares alot about performance
            # this compilation could be moved out and compiled once
            issn = [self.ISSN_ISBN_PATTERN.match(f['a']).group() for f in self.get_fields('022') if self.ISSN_ISBN_PATTERN.match(f['a'])]
        except TypeError:
            issn = []
        return issn

    @property
    def notes(self):
        ignore = [505,506,520,580,590] # 590 is a local notes field that isn't particularly relevant outside of III
        notes = []
        for field in range(500, 599):
            if field in ignore: continue
            notes += [f.format_field() for f in self.get_fields(field.__str__())]
        return notes

    @property
    def publisher(self):
        return [f.format_field() for f in self.get_fields('260')]

    @property
    def pub_dates(self):
        return [f.format_field() for f in self.get_fields('362')]

    @property
    def pub_frequency(self):
        return self['310'].format_field() if self['310'] else ''

    @property
    def pub_frequency_former(self):
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
    def supplement(self):
        return [f.format_field() for f in self.get_fields('770')]

    @property
    def supplement_parent(self):
        return [f.format_field() for f in self.get_fields('772')]

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
    def urls(self):
        if self.has_url():
            return [{'url': f.get_subfields('u')[0], 'label': f.get_subfields('z')[0] } for f in self.get_fields('856')]
        return []

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


class IIIReader(object):
    
    URI_FOR_RECORD = '{host}/record={bibnum}~S2'
    URI_FOR_MARC = '{host}/search~S2?/.{bibnum}/.{bibnum}/1%2C1%2C1%2CB/marc~{bibnum}'
    URI_FOR_HOLDINGS = '{host}/search~S2/.{bibnum}/.{bibnum}/1,1,1,B/holdings'
    MARC_REGEX = re.compile(r'<pre>(.*)</pre>', re.DOTALL)
    
    def __init__(self, opac_host):        
        self.host = opac_host
        self.conn = httplib2.Http()    
    
    def get_page(self, url):
        resp, content = self.conn.request(url)
        if resp.status < 400:
            return content
        else:
            return None            
    
    def record_exists(self, bibnumber):
        """
        #>>> reader = IIIReader('http://opac.utmem.edu')
        #>>> reader.record_exists('b1012752')
        #True
        #>>> reader.record_exists('b1012752...234245265')
        #True
        #>>> reader.record_exists('bz1012752')
        #False
        """
        record_page = self.get_page(self.URI_FOR_RECORD.format(host=self.host, bibnum=bibnumber))
        if record_page and record_page.find('No Such Record') == -1:
            return True
        else:
            return False
    
    def get_record(self, bibnumber):
        """
        >>> reader = IIIReader('http://opac.utmem.edu')
        >>> print reader.get_record('b1012752')
        Annales de genetique. 
        """
        if not bibnumber.startswith('b'):
            raise ValueError("Invalid bib record number.")
        
        if self.record_exists(bibnumber):
            record_page = self.get_page(self.URI_FOR_MARC.format(host=self.host, bibnum=bibnumber))
            record_data = re.findall(self.MARC_REGEX, record_page)[0]
            record = self.decode(record_data)
            if record:
                record.bibnumber = bibnumber
                record.raw = record_data
            return record
        else:
            return None
    
    def crawl_records(self, bib_start, bib_end):
        if not bib_start.startswith('b') or not bib_end.startswith('b'):
            raise ValueError("Invalid bib record number(s).")
    
        bib_start = int(bib_start[1:])
        bib_end = int(bib_end[1:])+1
        records = []
        
        for num in range(bib_start, bib_end):
            bibnum = "b{0}".format(num)
            record = self.get_record(bibnum)
            print bibnum
            if record:
                print record
                records.append(record)
            print '*'*100
        return records    
    
    def decode(self, record):
        pseudo_marc = record.strip().split('\n')
        raw_fields = []
        if pseudo_marc[0][0:6] == 'LEADER':
            record = IIIRecord()
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
                    data = " {data}".format(data=data) if tag.startswith(special_tag) else data                
                raw_fields[-1]['value'] = "{old}{new}".format(old=raw_fields[-1]['value'], new=data)
                raw_fields[-1]['raw'] = "{old}{new}".format(old=raw_fields[-1]['raw'], new=field.strip())
            else:
                data = data if (tag < '010' and tag.isdigit()) else "a{0}".format(data)
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

def unescape_entities(text):
    """Removes HTML or XML character references 
      and entities from a text string.
      keep &amp;, &gt;, &lt; in the source code.
      from Fredrik Lundh
      http://effbot.org/zone/re-sub.htm#unescape-html
      
      'text' must be a Unicode string
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
                    print text[1:-1]
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                print "keyerror"
                pass
        return text # leave as is
    regex = re.compile(ur'&#?\w+;', re.UNICODE)    
    return regex.sub(fixup, text)    


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    from datetime import datetime
    start = datetime.now()
    reader = IIIReader('http://opac.uthsc.edu')    
    
    if len(args) == 1:
        record = reader.get_record(args[0])
        print record
    elif len(args) == 2:
        # records = reader.crawl_records('b1069500','b1069530')
        records = reader.crawl_records(args[0], args[1])
                
        end = datetime.now()    
        elapsed = (end - start)
        seconds = elapsed.seconds + elapsed.microseconds/float(1000000)
        per_sec = len(records)/seconds
        print "Total records found: {0}".format(len(records))
        print "Total time: {0}".format(elapsed)
        print "Records per second: {0}".format(per_sec)
