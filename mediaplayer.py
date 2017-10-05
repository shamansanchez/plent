#!/usr/bin/python

# Media Status for i3blocks

import pydbus
import sys

try:
    bus = pydbus.SessionBus()
    player = bus.get("com.shamansanchez.plent")
except:
    sys.exit(0)

try:
    title  = player.title[:40]
except:
    title = "..."
try:
    artist = player.artist[:40]
except:
    artist = "..."
try:
    album  = player.album[:40]
except:
    album = "..."


if len(title) == 40:
    title = title + "..."

if len(artist) == 40:
    artist = artist + "..."

if len(album) == 40:
    album= album+ "..."

try:
    status  = player.state
except:
    status = "none"

try:
    shuffle = player.shuffle
except:
    shuffle = "none"

try:
    repeat = 'alltracks'
except:
    repeat = "none"

if status == 'playing':
    icon = "⮓"
elif status == 'none':
    icon = "?"
else:
    icon = "⮔"

if shuffle == 'alltracks':
    shufficon = "⇌"
elif shuffle == 'none':
    shufficon = "?"
else:
    shufficon = "⇀"

if repeat == 'singletrack':
    repeaticon = '1'
else:
    repeaticon = ''

duration = player.total_time // 1000000000
position = player.current_time // 1000000000

mins = duration // 60
secs = duration % 60
dur = "{0}:{1:02}".format(mins,secs)

mins = position // 60
secs = position % 60
pos = "{0}:{1:02}".format(mins,secs)

print("{0} {1} [{2}] - {3} | ⮖ {4}/{5} {6} {7}".format(icon, artist, album, title, pos, dur, shufficon, repeaticon))


