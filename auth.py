#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib2
import re

def auth(username, password):
    http = httplib2.Http()
    sess_id_regex = re.compile(r'III_SESSION_ID=(\d+);')
    session_id = None

    # Do initial request to get a session ID
    url = 'https://opac.uthsc.edu/search~S2'
    init_response, init_content = http.request(url)
    result = re.findall(sess_id_regex, init_response['set-cookie'])
    if result:
        session_id = result[0]

    # Then post to auth form with session ID and user credentials
    url2 = 'https://opac.uthsc.edu/patroninfo'
    headers = {'Content-type': 'application/x-www-form-urlencoded', 'Cookie': init_response['set-cookie']}
    response, content = http.request(url2, 'POST', headers=headers, body='extpatid={0}&extpatpw={1}&name=&code=&pin=&submit=Login'.format(username, password))

    # If status is 302, send back session ID - auth is good.
    if response['status'] == '302':
        return session_id
    else:
        return None

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    from getpass import getpass
    passw = getpass()
    
    print auth(args[0], passw)