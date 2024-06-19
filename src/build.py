import argparse
import email
import html.parser
import logging
import json
import os
from pathlib import Path
import shutil

import parse


logging.basicConfig()
logger = logging.getLogger('setalight')

parser = argparse.ArgumentParser()
parser.add_argument(
    'input', type=Path, help='email file or directory of files to process')
parser.add_argument('build', type=Path, default='setlist',
                    help='directory to build setlist in')
parser.add_argument('--template', type=Path, default=Path('dist/index.html'),
                    help='template to use')
parser.add_argument('--inline', type=Path, default=Path('dist/inline.html'),
                    help='inline template to use')
parser.add_argument(
    '--debug', '-d', default=False, action='store_true',
    help='just output song data, do not build site',
)


class ExtractTextParser(html.parser.HTMLParser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = []

    def handle_data(self, data):
        s = data.strip()
        if s:
            self.text.append(s)


def cleanup_filename(name):
    name = name.replace('-', ' ').replace('_', ' ')
    parts = name.split(' ')
    if parts[0].isdigit():
        parts = parts[1:]
    if parts[-1] in 'ABCDEFG':
        parts = parts[:-1]
    return ' '.join(parts).title()


def valid_html_part(text):
    if not text.strip():
        return False
    parser = ExtractTextParser()
    parser.feed(text)
    if len(parser.text) == 0:
        return False
    elif 'sent from my ' in parser.text[0].lower():
        return False

    return True


def extract_email(email_path, build_dir):
    with email_path.open('rb') as fp:
        msg = email.message_from_binary_file(fp)

    text = []
    html = []
    paths = []

    for part in msg.walk():
        # multipart/* are just containers
        if part.get_content_maintype() == 'multipart':
            continue

        filename = part.get_filename()
        part_type = part.get_content_type()
        if filename:  # attachment
            payload = part.get_payload(decode=True)
            if part_type in ('text/html', 'text/plain'):
                if not valid_html_part(payload.decode('utf8')):
                    continue
            
            path = build_dir / filename
            path.write_bytes(payload)
            paths.append(path)
        else:
            payload = part.get_payload(decode=True).decode('utf8').strip()
            if not payload:
                continue
            if part_type == 'text/plain':
                lines = payload.splitlines()
                if 'sent from my ' in lines[-1].lower():
                    lines = lines[0:-1]
                text.append('\n'.join(lines).strip())
            elif part_type == 'text/html':
                if valid_html_part(payload):
                    html.append(payload)

    return {
        'id': msg['Message-Id'],
        'from': msg['From'],
        'to': msg['To'],
        'subject': msg['Subject'],
        'date': msg['Date'],
        'html': html,
        'text': text,
        'paths': paths,
    }


def get_chordpro(song):
    if song['title']:
        yield '{{title:{}}}'.format(song['title'])
    if song['key']:
        yield '{{key:{}}}'.format(song['key'])
    yield ''
    for name, section in song['sections'].items():
        yield '{{comment:{}}}'.format(name)
        yield section
        yield ''


def build_site(args, setlist):
    pdfdata = {}
    for id, song in setlist['songs'].items():
        data = song.pop('pdf', None)
        if data:
            pdfdata[id] = data
    setlist_json = json.dumps(setlist, indent=4)
    pdfdata_json = json.dumps(pdfdata, indent=4)

    (args.build / 'setlist.json').write_text(setlist_json)
    template = args.template.read_text()
    output = template.replace('SETLIST', setlist_json)
    output = output.replace('PDFDATA', pdfdata_json)
    output = output.replace('TITLE', setlist['title'])
    (args.build / 'index.html').write_text(output)

    for songid, song in setlist['songs'].items():
        if song['file'].endswith('.pdf'):
            text = '\n'.join(get_chordpro(song))
            fname = song['file'][:-4] + '.txt'
            (args.build / fname).write_text(text)
    #inline = args.inline.read_text()
    #output = inline.replace('SETLIST', json.dumps(setlist, indent=4))
    #output = output.replace('PDFDATA', pdfdata_json)
    #output = output.replace('TITLE', setlist['title'])
    (args.build / 'inline.html').write_text(output)
    files = [
        'node_modules/@bundled-es-modules/pdfjs-dist/build/pdf.worker.js',
        'node_modules/drag-drop-touch-polyfill/DragDropTouch.js',
        'dist/fonts.css',
        'dist/main.css',
        'dist/main.js',
    ]
    for f in files:
        shutil.copy(f, str(args.build / Path(f).name))

    for song in setlist["songs"].values():
        print(f'{song["title"]} ({song["ccli"]})')


def get_song_id(song, i):
    if song['ccli']:
        return song['ccli']
    elif song['title']:
        return song['title'].lower().replace(' ', '-')
    else:
        return 'song-{}'.format(i)


def main(args):
    if args.debug:
        logger.setLevel(logging.DEBUG)

    args.build.mkdir(parents=True, exist_ok=True)
    for p in args.build.iterdir():
        p.unlink()

    if args.input.is_dir():
        paths = []
        for path in args.input.iterdir():
            dst = args.build / path.name
            shutil.copy(path, dst)
            paths.append(dst)
            logger.debug('copied {} to {}'.format(str(path), str(dst)))

        paths.sort()
        raw_setlist = {'paths': paths}
    else:
        raw_setlist = extract_email(args.input, args.build)

    songs = {}
    order = []

    for i, path in enumerate(raw_setlist['paths']):
        song = None
        song_type = None
        if path.suffix == '.pdf':
            song = parse.parse_pdf(path, args.build)
        elif path.suffix in ('.onsong', '.cho', '.txt', '.chopro'):
            song = parse.parse_onsong(path)
        if song:
            song_id = get_song_id(song, i)
            song['id'] = song_id
            song['file'] = path.name
            if not song['title']:
                song['title'] = cleanup_filename(path.stem)
            parse.add_inferred_key(song)
            if song_id in songs:
                # ok, songs has been attached twice, possible pdf and onsong/chordpro
                if song['type'] == 'onsong':
                    songs[song_id] = song
            else:
                order.append(song_id)
                songs[song_id] = song

    setlist = {
        'title': raw_setlist.get('subject', os.path.basename(args.input)),
        'text': raw_setlist.get('text'),
        'html': raw_setlist.get('html'),
        'leaders': raw_setlist.get('from'),
        'songs': songs,
        'order': order,
    }

    if args.debug:
        for id, song in songs.items():
            parse.print_song(song)
    else:
        build_site(args, setlist)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
