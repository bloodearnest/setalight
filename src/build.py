import argparse
import json
import os

import parse

parser = argparse.ArgumentParser()
parser.add_argument(
    'dir', help='file or directory to load from')
parser.add_argument(
    '--template', default='dist/index.html', help='template to use')
parser.add_argument(
    '--output', default=os.getcwd(), help='directory output setlist in')
parser.add_argument(
    '--debug', '-d', default=False, action='store_true',
    help='just output song data, do not build site',
)


def build_site(setlist, template):
    output = template.replace('SETLIST', json.dumps(setlist, indent=4))
    output = output.replace('TITLE', setlist['title'])
    print(output)


def get_song_id(song, i):
    if song['ccli']:
        return song['ccli']
    elif song['title']:
        return song['title'].lower().replace(' ', '-')
    else:
        return 'song-{}'.format(i)


def main(args):
    if os.path.isdir(args.dir):
        paths = [os.path.join(args.dir, f) for f in os.listdir(args.dir)]
    else:
        paths = [args.dir]
    paths.sort()

    if args.debug:
        print(paths)

    songs = {}
    order = []

    for i, path in enumerate(paths):
        if path.endswith('.pdf'):
            song = parse.parse_pdf(path, args.debug)
        elif path.endswith('.onsong'):
            song = parse.parse_onsong(path)
        id = get_song_id(song, i)
        song['id'] = id
        order.append(id)
        songs[id] = song

    setlist = {
        'title': 'Test Setlist',
        'message': 'test\ntesting\ntester',
        'songs': songs,
        'order': order,
    }

    if args.debug:
        for id, song in songs.items:
            parse.print_song(song)
    else:
        with open(args.template) as fp:
            template = fp.read()
        build_site(setlist, template)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
