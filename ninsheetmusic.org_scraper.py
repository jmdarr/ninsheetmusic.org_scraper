#!/bin/env python

### ninsheetmusic.org_scraper.py
### author: jdarr
### date:   11/12/2018

### pull down all PDFs from ninsheetmusic.org

## imports
import errno
import re
import shutil
import os
import urllib3
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

## disable some stuff... ignore the man behind the curtain
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## functions
def create_dir(dirname):
  #print 'I would try to create the directory "{0}".'.format(dirname)
  try:
    os.mkdir(dirname)
  except OSError as e:
    if e.errno != errno.EEXIST:
      print ("Creation of the directory '%s' failed" % dirname)

def normalize(value):
  #return instring.strip().replace(' ','_').replace(':','').lower().encode('utf-8')
  import unicodedata
  value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
  value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
  value = unicode(re.sub('[-\s]+', '-', value))
  return value

def download(url,path):
    r = get(url, stream=True, verify=False)
    with open(path, 'wb') as f:
      shutil.copyfileobj(r.raw, f)

    return path
    #print 'I would try to download "{0}" and write it to "{1}".'.format(url, path)

## variables
urlbase = 'http://www.ninsheetmusic.org'
basepath = '/path/to/root/of/downloads'

## double check we have our basepath for downloads fixed up
create_dir(basepath)

## do the thing, unsafely as possible #YOLO (seriously kids don't do this at home)
html_soup = BeautifulSoup(get(urlbase, stream=True, verify=False).content, 'html.parser')

## lets go through all the series pages..
for a in html_soup.find_all(href=re.compile('browse\/series')):
  print 'Processing "{0}"'.format(a.get('href'))

## on each series page, we want to get some data (e.g. https://www.ninsheetmusic.org/browse/series/AceAttorney):
##  1. the game name, e.g. <td colspan="6">Ace Attorney Investigations: Miles Edgeworth</td>
##     we should check to make sure the folder exists before we start looping through the file downloads
##  2. the artist and song name, e.g. <b>Kay Faraday ~ The Great Truth Burglar</b>
##  3. the pdf link for the track, e.g. <a href="https://www.ninsheetmusic.org/download/pdf/2932"><img src="https://www.ninsheetmusic.org/images/pdf.png" title="Download as PDF"></a>
## once we have this data we know where to write the file to.
## current organization is 'pdfs/<game name>/<artist name>_<song name>.pdf'

## lets collect the table out of the series page so we can loop through the elements within
  series_soup = BeautifulSoup(get(a.get('href'), stream=True, verify=False).content)
  table_soup = series_soup.find_all('table', style='text-align: center;')[0]
  directory = ''
  filepath = ''

## if we loop through the table rows we get either:
##   1. a row that cell that has a class of game
##   2. a row with cell that has bgcolor="#EEEEEE" (song)
## if it has a class, we write a dir and make that the active subdir
## if it doesn't, we process the artist~song or just song
  for row in table_soup.find_all('tr'):
    if row.td.get('colspan') == '6':
      print 'Found new game "{0}"'.format(normalize(row.text))
      directory = basepath + '/' + normalize(row.text)
      print 'Creating directory "{0}"'.format(directory)
      create_dir(directory)
    else:
      if '~' in row.td.text:
        # this has an artist and a song name
        filename = normalize(row.td.text.split('~')[0]) + "_" + normalize(row.td.text.split('~')[1]) + '.pdf'
      else:
        filename = normalize(row.td.text) + '.pdf'
      print 'Found sheet to download: "{0}"'.format(filename)

      if row.find_all('a', href=re.compile('pdf')):
        url = row.find_all('a', href=re.compile('pdf'))[0].get('href')
        filepath = directory + '/' + filename
        print 'Downloading "{0}" to "{1}"'.format(url, filepath)
        download(url, filepath)
      else:
        print 'No downloadable PDF found'

print 'All done!'
