#!/usr/bin/env python
#
# YACDArtDownloader 
# (c) Copyright 2010 by Camille Moncelier <moncelier@devlife.org>
# http://devlife.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA
#


#
# This source code is dirty, made in a couple of minutes and tuned 
# to be able to download cdarts for my poorly tagged music collection
# 
# Currently I do not have time norr motivation to further enhance
# hhis program. However, if you have any question regarding it, I'll
# be pleased to help you.
#
# Camille.
#

API_KEY = "86vjb-6FIbvuy6V5"

import sqlite3
import sys
import urllib
import re, os

from xml.dom.minidom import parseString


if len(sys.argv) < 3:
    print "usage: " + sys.argv[0] + " /path/to/Music7.db /path/to/CDArt/folder" 
    sys.exit(1);
try:
    conn = sqlite3.connect(sys.argv[1])
    conn.row_factory = sqlite3.Row
except:
    print "Unable to open: " + sys.argv[1]


# "http://www.xbmcstuff.com/music_scraper.php?&id_scraper=" + API_KEY + "&t=artists"
def grabXML(url):
    # Get something to work with.
    f = urllib.urlopen(url)
    xml = f.read().lstrip()
    try:
        xml = unicode(xml).decode('utf-8')
    except:
        xml = unicode(xml.decode('ascii', 'ignore')).decode('utf-8')

    return parseString(xml)


artists = dict()

def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

def cleanName(name):
    return name.lstrip().lower()

def cleanAlbum(artist, album):
    str = album.lower().replace(cleanName(artist) + " - ", "").lstrip()
    
    p = re.compile( '\(?\s?(disc|cd)\s*[0-9]+\s?\)?')
    str = p.sub('', str)

    return str


def grabArtists():
    print "grabArtists()"
    artists = dict()
    dom = grabXML("http://www.xbmcstuff.com/music_scraper.php?&id_scraper=" + API_KEY + "&t=artists")

    artist_nodes = dom.getElementsByTagName("artist")
    for artist_node in artist_nodes:
        name = artist_node.childNodes[0].data
        artists[cleanName(name)] = artist_node.getAttribute('id')

    return artists

def grabAlbums(artist, artistId):
    print "grabAlbums("+artist+")"
    albums = dict()
    domAlbum = grabXML("http://www.xbmcstuff.com/music_scraper.php?&id_scraper=" + API_KEY + "&t=cdarts&id_artist=" + artistId)
    cdarts = domAlbum.getElementsByTagName("cdart")
    for cdart in cdarts:
        albums[cleanAlbum(artist, cdart.getAttribute('album'))] = cdart.getElementsByTagName("picture")[0].childNodes[0].data

    return albums

artists = grabArtists()


c = conn.cursor()
c.execute('select * from artist order by strArtist')
for row in c:
    try:

        value = artists[cleanName(row['strArtist'])]
        albums = grabAlbums(row['strArtist'], value)


        c2 = conn.cursor()
        c2.execute('select * from album where idArtist = ?', (row['idArtist'],))
        
        for row2 in c2:
            try:
                url = albums[cleanAlbum(row['strArtist'], row2["strAlbum"])]
                filename = row['strArtist']+"-"+row2["strAlbum"]+".png"
                path = os.path.join(sys.argv[2], filename)

                if not os.path.exists(path):
                    print "Found: " + row['strArtist'] + " " + row2["strAlbum"]
                    urllib.urlretrieve(url, path)
            except KeyError:
                pass

    except KeyError:
        # key error
        pass
