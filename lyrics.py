#!/usr/bin/env python3

import requests
import ssl
import sys
import time
from bs4 import BeautifulSoup
from functools import reduce


utf8Map = {
    ('’', "'"), # single right quote
    ('“', '"'), # double left quote
    ('”', '"'), # double right quote
}

cp1252Map = {
    ('', "`"), # single left quote
    ('', "'"), # single right quote
    ('', '"'), # double left quote
    ('', '"'), # double right quote
}


def tr(mapping, src):
    return reduce(lambda a, kv: a.replace(*kv), mapping, src)

def hget(hymnNum, hymnLetter):
    cat = {
        'C': 'h/',
        'B': 'lb/',
        'N': 'ns/',
        'T': 'nt/'
    }
    try:
        r = requests.get('https://www.hymnal.net/en/hymn/'
            + cat[hymnLetter] + hymnNum)
    except requests.exceptions.ConnectionError as e:
        return e

    soup = BeautifulSoup(r.text, 'html.parser')
    # There should only be one "lyrics" class.
    lyrics = soup.select('.lyrics')[0]
    # Each "td" is a stanza or stanza number. Join them with newlines.
    stanzas = ['\n'.join(t.stripped_strings) for t in lyrics.select('td')]
    stanzas = [tr(utf8Map, s) for s in stanzas]

    return '\n'.join(stanzas) + '\n\n' + r.url

def wget(hymnNum):
    try:
        r = requests.get('http://www.witness-lee-hymns.org/hymns/H'
            + hymnNum + '.html')
    except requests.exceptions.ConnectionError as e:
        return e

    soup = BeautifulSoup(r.text, 'html.parser')
    # Each "text2" class is a stanza.
    text = soup.select('.text2')
    stanzas = [''.join(t.stripped_strings) for t in text]
    # Remove blank sections.
    stanzas = filter(lambda x: len(x), stanzas)
    # Remove headers.
    headers = ('SUBJECT', 'METER', 'AUTHOR', 'COMPOSER')
    notHeader = lambda s: s.split(':')[0] not in headers
    stanzas = filter(notHeader, stanzas)
    stanzas = [tr(cp1252Map, s) for s in stanzas]

    return '\n'.join(stanzas) + '\n\n' + r.url

def sget():
    r = requests.get('http://listen.hymnsradio.com:2199/external/rpc.php',
        params={'m': 'streaminfo.get', 'username': 'hymnsradio'})

    json = r.json()
    track = json['data'][0]['track']
    track['json'] = json
    return track

def loop():
    cur = None

    while True:
        try:
            track = sget()
        except requests.exceptions.ConnectionError as e:
            print(e)
            time.sleep(10)
            continue
        artist, title, stream = track['artist'], track['title'], track['json']
        if (artist, title) != cur:
            titleAscii = tr(utf8Map, title)
            print('\n')
            print(titleAscii + '\n')

            cat, num = artist[2], artist[3:]
            if cat == 'L':
                print(wget(num))
            elif cat in 'CBNT':
                print(hget(num, cat))

            cur = (artist, title)
        time.sleep(10)

if __name__ == '__main__':
    try:
        loop()
    except KeyboardInterrupt:
        pass
