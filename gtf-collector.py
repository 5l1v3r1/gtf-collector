#!/usr/bin/env python

import urllib
import urllib2
import cookielib
import xml.dom.minidom
import json
import time
import random
import re

# Config
HOST = "global-trend-finder.com"
PASSWORD = "u42UzwZx"
CHUNK_SIZE = 500

def sign_in(password):
  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  urllib2.install_opener(opener)
  urllib2.urlopen('http://' + HOST + '/sessions.json', urllib.urlencode({'password': password}))

def send_entities(mtype, mname, data):
  request = urllib2.Request('http://' + HOST + '/' + mtype + '.json')
  request.add_data(json.dumps({'mname': mname, 'data': data}))
  request.add_header('Content-Type', 'application/json')
  urllib2.urlopen(request)
 
def sign_out():
  request = urllib2.Request('http://' + HOST + '/sessions/0.json')
  request.get_method = lambda: 'DELETE'
  urllib2.urlopen(request)


random.seed()

# Get words
input = open('words.txt', 'r')

words = []
sites = []
last_chunk = 0
offset = 0

compete_sites = []

lines = input.readlines()

# Shuffle lines
random.shuffle(lines)

# Sign in
print "Signing in..."
sign_in(PASSWORD)

# Collect entities - Google
print "Collecting Google Ranks..."

for word in lines:
  word = urllib.quote(word.rstrip('\n'))
  suggest = urllib2.urlopen('http://google.com/complete/search?output=toolbar&q=' + word)

  input = suggest.read()
  if not input: continue

  # Parse Google XML response
  dom = xml.dom.minidom.parseString(input)
  for suggestion in dom.getElementsByTagName('CompleteSuggestion'):
    entity = suggestion.getElementsByTagName('suggestion')[0].getAttribute('data')
    if len(suggestion.getElementsByTagName('num_queries')) > 0:
      measurement = suggestion.getElementsByTagName('num_queries')[0].getAttribute('int')
    else:
      measurement = 0

    # Separate websites from words
    if re.match("^[^ ]*\.(com|gov|net|edu)$", entity):
      sites.append([ unicode(entity), int(measurement) ])
      compete_sites.append(unicode(entity))
    else:
      words.append([ unicode(entity), int(measurement) ])

  # Send chunks of data - every CHUNK_SIZE entries
  entities = offset + len(sites) + len(words)
  if entities / CHUNK_SIZE != last_chunk:

    print "Entities collected: " + str(entities) + ", sending..."

    # Send collected words using REST
    send_entities('words', 'Google', words)
    words = []
    
    # Send collected sites using REST
    send_entities('sites', 'Google', sites)
    sites = []

    # As we clear arrays, we need to keep an offset for counting purposes
    offset = entities
    
  last_chunk = entities / CHUNK_SIZE

  # Random pause to confuse automated checking tools
  time.sleep(random.random())

# Send remaining items
if last_chunk * CHUNK_SIZE != entities:
  print "Entities collected: " + str(entities) + ", sending..."
  send_entities('words', 'Google', words)
  send_entities('sites', 'Google', sites)

# =====

sites = []
last_chunk = 0
offset = 0

# Collect entities - Compete
print "Collecting Compete Ranks..."

for site in compete_sites:
  rank = urllib2.urlopen('http://apps.compete.com/sites/' +
                         site +
                         '/trended/rank/?apikey=d1897cc9fc7aad00186bd3a02d6db67d&latest=1')

  input = rank.read()
  if not input: continue
 
  # Parse response
  measurement = json.loads(input)
  if not measurement.has_key('data'): continue

  measurement = measurement['data']['trends']['rank'][0]['value']
  sites.append([ site, int(measurement) ])

  # Send chunks of data - every CHUNK_SIZE entries
  entities = offset + len(sites)
  if entities / CHUNK_SIZE != last_chunk:

    print "Entities collected: " + str(entities) + ", sending..."

    # Send collected sites using REST
    send_entities('sites', 'Compete', sites)
    sites = []

    # As we clear arrays, we need to keep an offset for counting purposes
    offset = entities
    
  last_chunk = entities / CHUNK_SIZE
  
  # Random pause to confuse automated checking tools
  time.sleep(random.random())

# Send remaining items
if last_chunk * CHUNK_SIZE != entities:
  print "Entities collected: " + str(entities) + ", sending..."
  send_entities('sites', 'Compete', sites)

# Sign out
print "Signing out..."
sign_out()
