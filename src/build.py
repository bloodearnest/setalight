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


def build_site(title, text, songs, template):
    output = template.replace('SONGDATA', json.dumps(songs, indent=4))
    output = output.replace('TITLE', title)
    print(output)


def main(args):
    songs = []
    if os.path.isdir(args.dir):
        paths = [os.path.join(args.dir, f) for f in os.listdir(args.dir)]
    else:
        paths = [args.dir]
    paths.sort()

    if args.debug:
        print(paths)

    for path in paths:
        if path.endswith('.pdf'):
            songs.append(parse.parse_pdf(path, args.debug))
        elif path.endswith('.onsong'):
            songs.append(parse.parse_onsong(path))

    if args.debug:
        for song in songs:
            parse.print_song(song)

    else:
        with open(args.template) as fp:
            template = fp.read()
        build_site('12th May', 'test\ntesting\ntester', songs, template)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
