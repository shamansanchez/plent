#!/usr/bin/python

import sys

import pydbus

if len(sys.argv) != 2:
    sys.exit(0)

bus = pydbus.SessionBus()
player = bus.get("com.shamansanchez.plent")

cmd = sys.argv[1]

if cmd == "play":
    player.play()
elif cmd == "pause":
    player.pause()
elif cmd == "playpause":
    if player.state == "playing":
        player.pause()
    else:
        player.play()
elif cmd == "next":
    player.skip()
elif cmd == "previous":
    player.previous()
elif cmd == "shuffle":
    player.toggle_shuffle()
