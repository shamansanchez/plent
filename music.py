#!/usr/bin/python

import json
import os
import random
from operator import itemgetter

import gi
import gmusicapi
import requests
import yaml
from pydbus import SessionBus

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

class Player(object):
    """
        <node>
        <interface name='com.shamansanchez.plent'>
            <method name='previous'/>
            <method name='skip'/>
            <method name='play'/>
            <method name='pause'/>
            <method name='print_song_list'/>
            <method name='toggle_shuffle'/>
            <method name='select_song'>
                <arg name="song_num" type="u" direction="in" />
            </method>
            <property name="title" type="s" access="read"/>
            <property name="artist" type="s" access="read"/>
            <property name="album" type="s" access="read"/>
            <property name="current_time" type="t" access="read"/>
            <property name="total_time" type="t" access="read"/>
            <property name="album_art" type="s" access="read"/>
            <property name="state" type="s" access="read"/>
            <property name="shuffle" type="s" access="read"/>
        </interface>
        </node>
    """
    def __init__(self):
        GObject.threads_init()
        Gst.init(None)

        self.loop = GObject.MainLoop()
        self.dbus = SessionBus()

        self.playbin = Gst.ElementFactory.make("playbin", "player")

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()

        self.bus.connect("message::error", self.on_error)
        self.bus.connect("message::eos", self.on_eos)
        self.playbin.connect("about-to-finish", self.next_song)

        self.shuffle = 'alltracks'

        with open("conf.yml", 'r') as y:
            self.conf = yaml.load(y)

        self.client = gmusicapi.Mobileclient()

        self.cache_dir = os.path.expanduser(self.conf['cache_dir'])
        os.makedirs(self.cache_dir, exist_ok=True)

        if not self.client.is_authenticated():
            self.client.login(self.conf['email'], self.conf['pass'], self.conf['deviceid'])

        self.songs = self.client.get_all_songs()

        with open("{}/metadata.json".format(self.cache_dir), 'w') as fd:
            json.dump(self.songs, fd)

        for song in self.songs:
            if song['albumArtist'] == "":
                song['albumArtist'] = song['artist']

        self.songs.sort(key=itemgetter('albumArtist', 'year', 'album', 'discNumber', 'trackNumber'))

        s = 0
        for song in self.songs:
            song['num'] = s
            s += 1

    @property
    def title(self):
        return self.current_song["title"]

    @property
    def artist(self):
        return self.current_song["artist"]

    @property
    def album(self):
        return self.current_song["album"]

    @property
    def current_time(self):
        ret, current = self.playbin.query_position(Gst.Format.TIME)
        return current

    @property
    def total_time(self):
        ret, duration = self.playbin.query_duration(Gst.Format.TIME)
        return duration

    @property
    def album_art(self):
        if "albumArtRef" in self.current_song and self.current_song["albumArtRef"]:
            return self.current_song["albumArtRef"][0]["url"]
        return ""

    @property
    def state(self):
        ret, state, pending = self.playbin.get_state(10)

        if state == Gst.State.PLAYING:
            return "playing"
        else:
            return "notplaying"

    def on_error(self, bus, message):
        err, dbg = message.parse_error()
        print("ERROR:", message.src.get_name(), ":", err.message)

    def on_eos(self, bus, message):
        print("EOS")
        self.playbin.set_state(Gst.State.READY)

    def _cache_song(self, song):
        filename = "{}/{}.mp3".format(self.cache_dir,song['id'])

        if not os.path.exists(filename):
            r = requests.get(self.client.get_stream_url(song['id']), stream=True)
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)

        return "file://{}".format(filename)

    def _play_song(self, song):
        self.playbin.set_state(Gst.State.READY)
        url = self._cache_song(song)
        self.playbin.set_property('uri', url)
        self.current_song = song
        self.playbin.set_state(Gst.State.PLAYING)

    def next_song(self, playbin):
        song = self.songs[self.current_song["next"]]
        url = self._cache_song(song)
        self.playbin.set_property('uri', url)
        self.current_song = song

    def skip(self):
        song = self.songs[self.current_song["next"]]
        self._play_song(song)

    def previous(self):
        song = self.songs[self.current_song["prev"]]
        self._play_song(song)

    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)

    def play(self):
        self.playbin.set_state(Gst.State.PLAYING)

    def select_song(self, song_num):
        song = self.songs[song_num]
        self._play_song(song)

    def toggle_shuffle(self):
        if self.shuffle == "alltracks":
            self._order_songs()
            self.shuffle = "ordered"
        else:
            self._shuffle_songs()
            self.shuffle = "alltracks"

    def print_song_list(self):
        s = 0
        for song in self.songs:
            print(str(s) + " " + str(song['trackNumber'])  + ". " + song['title'] + " - " + song['artist'] + " - " + song['album']+ " - " + str(song['year']))
            s = s + 1

    def _shuffle_songs(self):
        order = list(range(len(self.songs)))
        random.shuffle(order)

        first = order.pop()
        song = self.songs[first]
        while order:
            num = song["num"]
            song["next"] = order.pop()
            song = self.songs[song["next"]]
            song["prev"] = num

        song["next"] = first
        self.songs[first]["prev"] = song["num"]

    def _order_songs(self):
        for song in self.songs:
            song["prev"] = (song["num"] - 1) % len(self.songs)
            song["next"] = (song["num"] + 1) % len(self.songs)

    def main(self):
        self._shuffle_songs()
        song = random.choice(self.songs)
        self._play_song(song)

        try:
            self.dbus.publish("com.shamansanchez.plent", self)
            self.loop.run()
        except Exception as e:
            print(e)

        self.playbin.set_state(Gst.State.NULL)

if __name__ == '__main__':
    player = Player()
    player.main()
