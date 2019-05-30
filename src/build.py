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


def build_site(title, text, songs):
    with open('dist/index.html') as fp:
        template = fp.read()
    output = template.replace('SONGDATA', json.dumps(songs, indent=4))
    output = output.replace('TITLE', title)
    print(output)


def main(input, output, debug):
    songs = []
    if os.path.isdir(input):
        paths = [os.path.join(input, f) for f in os.listdir(input)]
    else:
        paths = [input]

    for path in paths:
        if path.endswith('.pdf'):
            songs.append(parse.parse_pdf(path, debug))

    if debug:
        for song in songs:
            print(song['title'])
            print(song['key'])
            print(song['tempo'])
            print(song['ccli'])
            for name, section in song['sections'].items():
                print(name)
                print(section)
    else:
        build_site('12th May', 'test\ntesting\ntester', songs)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.dir, args.output, args.debug)
