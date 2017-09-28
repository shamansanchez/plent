#!/usr/bin/python

import sys

import pydbus

if len(sys.argv) != 2:
    sys.exit(0)

bus = pydbus.SessionBus()
player = bus.get("com.shamansanchez.plent")

cmd = sys.argv[1]

if cmd == "play":
    player.play_song()
elif cmd == "pause":
    player.pause_song()
elif cmd == "playpause":
    if player.state == "playing":
        player.pause_song()
    else:
        player.play_song()
elif cmd == "next":
    player.skip_song()