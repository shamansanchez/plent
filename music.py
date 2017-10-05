#!/usr/bin/python

import random
from operator import itemgetter
from pydbus import SessionBus

import gi
import gmusicapi
import yaml

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
        self.playbin.set_property('buffer-size', 104857600)

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()

        self.bus.connect("message::error", self.on_error)
        self.bus.connect("message::eos", self.on_eos)
        self.playbin.connect("about-to-finish", self.next_song)

        self.shuffle = 'alltracks'

        with open("conf.yml", 'r') as y:
            self.conf = yaml.load(y)

        self.client = gmusicapi.Mobileclient()

        if not self.client.is_authenticated():
            self.client.login(self.conf['email'], self.conf['pass'], self.conf['deviceid'])

        self.songs = self.client.get_all_songs()

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

    def _play_song(self, song):
        print("{} - {}".format(song['title'], song['artist']))
        self.playbin.set_state(Gst.State.READY)
        self.playbin.set_property('uri', self.client.get_stream_url(song['id']))
        self.current_song = song
        self.playbin.set_state(Gst.State.PLAYING)

    def _get_next_song(self, num_songs=1):
        if self.shuffle == "alltracks":
            song = random.choice(self.songs)
        else:
            song = self.songs[(self.current_song["num"] + num_songs) % len(self.songs)]
        return song

    def next_song(self, playbin):
        song = self._get_next_song()
        self.playbin.set_property('uri', self.client.get_stream_url(song['id']))
        self.current_song = song

    def skip(self):
        song = self._get_next_song()
        self._play_song(song)

    def previous(self):
        song = self._get_next_song(num_songs=-1)
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
            self.shuffle = "ordered"
        else:
            self.shuffle = "alltracks"

    def print_song_list(self):
        s = 0
        for song in self.songs:
            print(str(s) + " " + str(song['trackNumber'])  + ". " + song['title'] + " - " + song['artist'] + " - " + song['album']+ " - " + str(song['year']))
            s = s + 1

    def main(self):
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
