import random
from operator import itemgetter

import gi
import gmusicapi
import yaml

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

class Player(object):

    def __init__(self):
        GObject.threads_init()
        Gst.init(None)

        self.loop = GObject.MainLoop()

        self.playbin = Gst.ElementFactory.make("playbin", "player")
        self.playbin.set_property('buffer-size', 104857600)

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()

        self.bus.connect("message::error", self.on_error)
        self.bus.connect("message::eos", self.on_eos)
        self.playbin.connect("about-to-finish", self.next_song)

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

        # s = 0
        # for song in self.songs:
        #     print(str(s) + " " + str(song['trackNumber'])  + ". " + song['title'] + " - " + song['artist'] + " - " + song['album']+ " - " + str(song['year']))
        #     s = s + 1

    def on_error(self, bus, message):
        err, dbg = message.parse_error()
        print("ERROR:", message.src.get_name(), ":", err.message)

    def on_eos(self, bus, message):
        print("EOS")
        self.playbin.set_state(Gst.State.READY)

    def next_song(self, playbin):
        song = random.choice(self.songs)
        print("NEXT SONG")
        print("{} - {}".format(song['title'], song['artist']))
        self.playbin.set_property('uri', self.client.get_stream_url(song['id']))

    def main(self):
        song = random.choice(self.songs)
        print("{} - {}".format(song['title'], song['artist']))
        self.playbin.set_property('uri', self.client.get_stream_url(song['id']))
        self.playbin.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except:
            pass

        self.playbin.set_state(Gst.State.NULL)

if __name__ == '__main__':
    player = Player()
    player.main()
