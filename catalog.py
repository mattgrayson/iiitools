#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# - for some reason this file must be saved in same encoding also ...
# 
# - Encoding set to latin1 so that unicode search strings are correctly 
#   quoted by urllib.quote before being passed to host, which expects 
#   query args encoded as latin1.


class Catalog(object):
    def __init__(self):
        self.base_url = 'http://opac.utmem.edu/search/?'        
        self.search_params = {
            'issn': 'searchtype=i&searchscope=2&searcharg=%s',
        }
    
    def get(self, query, query_field='bib'):
        """docstring for get"""
        pass
    
    def search(self, query, query_field='keyword'):
        """docstring for search"""
        pass    
    
    
    def _url_for_request(search_type):
        return self.search_params[search_type]