import json
import os
from operator import itemgetter

import taglib
import yaml

with open("conf.yml", 'r') as y:
    conf = yaml.load(y)

dirname = conf['music_dir']

output = []

for root, dir, files in os.walk(dirname):
    for file in files:
        if file.endswith((".flac",".mp3")):
            path = "{}/{}".format(root,file)

            tags = taglib.File(path)

            song = {
                "path": path.replace(dirname,""),
                "title": tags.tags.get("TITLE")[0],
                "artist": tags.tags.get("ARTIST")[0],
                "albumArtist": tags.tags.get("ALBUMARTIST", tags.tags["ARTIST"])[0],
                "album": tags.tags.get("ALBUM")[0],
                "year": int(tags.tags.get("DATE", ["0"])[0]),
                "trackNumber": int(tags.tags.get("TRACKNUMBER", ["0/0"])[0].split("/")[0]),
                "discNumber": int(tags.tags.get("DISCNUMBER", ["1/1"])[0].split("/")[0]),
            }

            output.append(song)

output.sort(key=itemgetter('albumArtist', 'year', 'album', 'discNumber', 'trackNumber'))

s = 0
for song in output:
    song['num'] = s
    s += 1

print(json.dumps(output))
