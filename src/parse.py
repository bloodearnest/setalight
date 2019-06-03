from collections import OrderedDict
import itertools
import os
import re
import subprocess
import tempfile

import chardet

# from PyPDF2 import PdfFileReader


class RE:

    PAGE = re.compile(r'Page ?[A-Za-z0-9]+')
    KEY = re.compile(
        r'key\s*(?:[-:]|of)\s+\[?(?P<key>[A-G][♯♭#b]?)\]?'
        r'\s*(?:Capo (?P<capo>\d+))?',
        re.I,
    )
    TIME = re.compile(r'time\s+[-:]\s+(\d+/\d+)', re.I)
    TEMPO = re.compile(r'tempo\s+[-:]\s+(\d+)', re.I)
    SECTION = re.compile(r"""^(
        intro|
        verse|
        chorus|
        bridge|
        pre-chorus|
        instrumental|
        interlude|
        turnaround|
        ending|
        coda|
        outro
    )""", re.I | re.VERBOSE)
    # this sucker is a beauty
    CHORD = re.compile(r"""
        ^
        (?P<nochords>[Nn]\.?[Cc]\.?)|       # N.C used for acapella sections
        (?P<note>[A-JZ][♯♭b#]?)             # root note
        (?P<third>mM|min|MIN|Min|maj|MAJ|Maj|m|M)?  # major/minor 3rd
        (?P<fifth>aug|AUG|dim|DIM|\+|ø|°)?  # sharp or flat 5th
        (?P<number>\(?(?:dom|DOM)?\d+\)?)?  # added notes, implies 7th if >7
        (?P<subtraction>\(?no3r?d?\)?)?     # C(no3) = C5
        (?P<altered>[♯♭b#\-\+]\d+)?         # added out-of-chord notes
        (?P<suspension>(?:sus|SUS)\d*)?     # suspended 2 or 4
        (?P<addition>(?:add|ADD|/)\d+)?     # added notes no 7th implied
        (?P<bass>/[A-JZ][♯♭b#]?)?           # BASS
        $
    """, re.VERBOSE)
    CCLI = re.compile(r'CCLI ?Song ?# ?(\d+)', re.I)
    # used to split a chord line into tokens including splitting on |
    CHORD_SPLIT = re.compile(r"""
        [ ](\([^\d].*?\))|  # matches (To SECTION) or (CHORD), keep
        (\|)|                # bar lines, keep
        [ ]+               # spaces, discard
    """, re.VERBOSE)

    # CHORDPRO directive
    DIRECTIVE = re.compile(r'{(?P<directive>\w+):(?P<value>.*)}')


def search(regex, text):
    """Helper for regex searching."""
    match = regex.search(text)
    search.match = match
    return match


# def get_pdf_type(path):
#    with open(path, 'rb') as f:
#        pdf = PdfFileReader(f)
#        creator = pdf.documentInfo['/Creator'].lower()
#
#    if 'onsong' in creator:
#        return 'onsong'
#    elif 'pdfsharp' in creator:
#        return 'pdfsharp'
#    else:
#        return None


def clean_encoding(contents):
    contents = contents.replace('\u200B', '')  # no zero-width spaces
    contents = contents.replace('\t', ' ')  # no tabs
    contents = contents.replace('\x85', ' ')   # no weird new lines
    return contents


def convert_pdf(path):
    """Converts a pdf file to text.

    Deals with various common conversion errors."""
    cmd = ['pdftotext', '-layout', '-enc', 'UTF-8', '-eol', 'unix', '-nopgbrk']
    try:
        _, output = tempfile.mkstemp()
        subprocess.run(cmd + [path, output])
        with open(output, 'r') as f:
            contents = f.read()
    finally:
        os.unlink(output)

    # fix various issues
    contents = clean_encoding(contents)
    # TODO: we probably enforce ASCII, stripping unicode?
    # sometimes a chord like D(4) is extracted as D(4 which is hard to parse
    contents = re.sub(r'([A-JZ]\([\d])([ $])', r'\1)\2', contents)
    return contents


def tokenise_chords(chord_line):
    """Tokenise a chord line into separate items.

    Valid tokens are: chords, |, and bracketed directives e.g. (To Chorus).
    """
    chords = []
    chord = []
    closer = None
    brackets = {
        '(': ')',
        '[': ']',
        '{': '}',
    }

    for c in chord_line:
        if closer:
            if c == closer:
                closer = None
            chord.append(c)
        elif c in brackets:
            chord.append(c)
            closer = brackets[c]
        elif c in '| \t\n\r':
            if chord:
                chords.append(''.join(chord))
            if c == '|':
                chords.append('|')
            chord = []
        else:
            chord.append(c)

    if chord:
        chords.append(''.join(chord))

    return chords


def chord_indicies(chord_line):
    """Find the indicies of all chords, bars and comments in the chord line."""
    i = 0
    for chord in tokenise_chords(chord_line):
        search_index = chord_line[i:].find(chord)
        if search_index == -1:
            raise Exception(
                'could not find {} in {}'.format(chord, chord_line)
            )
        chord_index = i + search_index
        yield chord_index, chord
        i = chord_index + len(chord)


def is_chord_line(tokens):
    """Is this line a chord line?"""
    chords = not_chords = 0
    for t in tokens:
        # bars
        if t == '|':
            chords += 1
        elif t[0] == '(' or t[-1] == ')':
            # directions like (To Pre-Chorus) that appear in chord lines
            chords += 1
        elif RE.CHORD.match(t):
            chords += 1
        else:
            not_chords += 1

    return chords > not_chords


def chordpro_line(chord_line, lyric_line):
    """Merge separate chord and lyric lines into one chordpro line.

    Builds an index of the chords, then iterates through the lyric line,
    inserting chords at those indexes. There is some finesse about spaces,
    chords consuming spaces in the lyric line, and handling |'s in chords, as
    well as different chord/lyric line lengths.
    """
    if not chord_line:
        return lyric_line
    elif not lyric_line:
        # chords not wrapped in []
        return chord_line
    else:
        chord_iter = itertools.chain(
            chord_indicies(chord_line),
            itertools.repeat((-1, None)),
        )
        line_iter = enumerate(
            itertools.chain(
                lyric_line,
                itertools.repeat(None),
            ),
        )
        output = []

        index, chord = next(chord_iter)
        i, char = next(line_iter)
        last_char = None
        while chord or char:
            if i == index:
                if chord.startswith('(') and chord.endswith(')'):
                    output.append('{comment:' + chord + '}')
                else:
                    if output and output[-1][-1] == ']':
                        # ensure a space between chords
                        output.append(' ')
                    elif char == ' ' and last_char != ' ':
                        # ensure there is a space in the lyric line to 'attach'
                        # to
                        output.append(' ')
                    output.append('[' + chord + ']')
                # skip up to the chord's length of spaces in the lyric line
                skipped = 0
                while char == ' ' and skipped < len(chord):
                    last_char = char
                    i, char = next(line_iter)
                    skipped += 1

                index, chord = next(chord_iter)
            else:
                if char is None:
                    output.append(' ')
                    last_char = ' '
                else:
                    output.append(char)
                    last_char = char
                i, char = next(line_iter)

        # condense spaces
        chordpro = ''.join(output).strip()
        condensed = re.sub('  +', ' ', chordpro)
        return condensed


def fix_superscript_line(superscript, chords):
    """Collapse superscript line into a chord line in the right place.

    This is specific fix for an issue seen with real pdfs. A superscript line
    occurs when pdftotext pushes a numeric superscript into its own line,
    rather than keeping it with the chord.

    E.G. A⁶/B is output as two lines:

    " 6"
    "A /B"

    This function merges back the superscript line into:

    "A6/B"
    """
    out = []
    for s, c in itertools.zip_longest(superscript, chords):
        if s is None:
            out.append(c)
        elif s == ' ':
            out.append(c)
        elif c == ' ':
            out.append(s)
        else:
            # this might be wrong, but best we can do for now
            out.append(s)
            out.append(c)
    return ''.join(out)


def parse_header(header):
    # first line has 'Key - X' or 'Key of X'
    key = RE.KEY.search(header[0])
    if key:
        groupdict = key.groupdict()
        yield 'key', groupdict.get('key')
        yield 'capo', groupdict.get('capo')
        position = key.span()[0]
        yield 'title', header[0][:position].strip()
    else:
        yield 'title', header[0].strip()

    # is there a second header line?
    if len(header) > 1:
        time = RE.TIME.search(header[1])
        pos = len(header[1])
        if time:
            if time:
                yield 'time', time.groups()[0]
                pos = min(pos, time.span()[0])

        tempo = RE.TEMPO.search(header[1])
        if tempo:
            if tempo:
                yield 'tempo', tempo.groups()[0]
                pos = min(pos, tempo.span()[0])
        yield 'author', header[1][:pos].strip()

    if len(header) > 2:
        yield 'blurb', '\n'.join(header[2:])


def parse_pdf(path, debug):
    """Parse a pdf intro plain text.

    Right now this is simple and a bit brittle. It converts the pdf to text
    using pdttotext from the poppler project, then attempts to parse that
    textual output into a semantic song data.

    In the future, it could parse the pdf directly.
    """

    sheet = convert_pdf(path)
    if debug:
        print(sheet)

    song = new_song()
    song['type'] = 'pdf'

    sheet_lines = sheet.split('\n')
    # skip any leading blank lines
    for i, line in enumerate(sheet_lines):
        if line.strip():
            break

    lines = sheet_lines[i:]

    if RE.SECTION.search(lines[0]) or is_chord_line(tokenise_chords(lines[0])):
        line_iter = iter(lines)
    else:  # must be some kind of title block
        header = []
        for i, line in enumerate(lines[:6]):
            if line.strip():
                header.append(line)
            else:
                # found the end of the header
                song.update(dict(parse_header(header)))
                line_iter = iter(lines[i:])
                break
        else:
            # no discernable header ended by blank line
            line_iter = iter(lines)

    # default name
    section_name = 'VERSE 1'
    section_lines = []
    chord_line = None
    superscript_line = None
    # set a default first section name, in case it's missing

    for line in line_iter:
        if not line.strip():  # skip blank lines
            continue
        ccli = RE.CCLI.search(line)
        if ccli:
            break
        if RE.PAGE.search(line.strip()):
            continue

        tokens = tokenise_chords(line)
        if RE.SECTION.search(line):
            if chord_line:
                section_lines.append((chord_line, None))
            if section_lines:
                song['sections'][section_name] = section_lines
            chord_line = None
            section_name = line.strip()
            section_lines = []
        elif is_chord_line(tokens):
            if chord_line is not None:
                section_lines.append((chord_line, None))
            if superscript_line is not None:
                chord_line = fix_superscript_line(
                    superscript_line,
                    line.rstrip(),
                )
                superscript_line = None
            else:
                chord_line = line.rstrip()
        else:
            # handle case where superscript chord markings get pushed onto
            # their own line above by pdftotext
            if line.strip().isdigit():
                superscript_line = line
            else:
                section_lines.append((chord_line, line.rstrip()))
                chord_line = None

    # handle dangling chord line
    if chord_line:
        section_lines.append((chord_line, None))
    # finish final section
    if section_lines:
        song['sections'][section_name] = section_lines

    # did we reached the CCLI number
    if ccli is not None:
        song['ccli'] = ccli.groups()[0]
        song['legal'] += line.strip() + '\n'.join(l.strip() for l in line_iter)

    # convert into chordpro
    for name, section_lines in song['sections'].items():
        song['sections'][name] = '\n'.join(
            chordpro_line(c, l) for c, l in section_lines
        )

    if debug:
        print_song(song)

    if not song['sections']:
        song['type'] = 'pdf-failed'

    return song


def new_song():
    song = {
        'title': None,
        'key': None,
        'capo': None,
        'tempo': None,
        'author': None,
        'time': None,
        'ccli': None,
        'blurb': '',
        'legal': '',
        'sections': OrderedDict(),
        'type': None,
    }
    return song


def print_song(song):
    print('title', song['title'])
    print('author', song['author'])
    print('blurb', song['blurb'])
    print('key', song['key'])
    print('capo', song['capo'])
    print('time', song['time'])
    print('tempo', song['tempo'])
    print('ccli', song['ccli'])

    for name, section in song['sections'].items():
        print(name)
        print(section)


META = {
    'title': 'title',
    't': 'title',
    # subtitle (short: st),
    'artist': 'author',
    'composer': 'author',
    # lyricist
    'copyright': 'legal',
    # album
    # year
    'key': 'key',
    'time': 'time',
    'tempo': 'tempo',
    # duration
    'capo': 'capo',
    # meta
}


def parse_onsong(path):
    with open(path, 'rb') as f:
        raw = f.read()
    meta = chardet.detect(raw)
    encoding = meta['encoding']
    if 'UTF-16' in encoding:
        encoding = 'UTF-16'  # this encoding strips any BOM
    text = clean_encoding(raw.decode(encoding))

    song = new_song()
    song['type'] = 'onsong'

    verse_counter = 1
    section = None
    section_lines = []

    line_iter = iter(text.split('\n'))

    # parse header
    for line in line_iter:
        # try detect if there is no header
        if RE.SECTION.search(line):
            section = line.strip()
            break

        if search(RE.DIRECTIVE, line):
            meta = META.get(search.match.group('directive'))
            if meta:
                current = song[meta]
                value = search.match.group('value')
                if current:
                    song[meta] += ' ' + value
                else:
                    song[meta] = value
            #else:
            #    print('skipping unknown directive {}'.format(line))

        elif search(RE.KEY, line):
            song['key'] = search.match.group('key')
        elif line.strip():
            if song['title'] is None:
                song['title'] = line.strip()
            elif song['author'] is None:
                song['author'] = line.strip()
            else:
                song['blurb'] += line.strip()
        else:
            break

    for line in line_iter:
        if not line.strip():
            # reached the end of a section
            if section is not None and section_lines:
                song['sections'][section] = '\n'.join(section_lines)
            section = None
            section_lines = []
            continue

        if RE.SECTION.search(line):
            if section is not None and section_lines:
                song['sections'][section] = '\n'.join(section_lines)
            section = line.strip()
            section_lines = []
        elif search(RE.CCLI, line):
            song['ccli'] = search.match.groups()[0]
            song['legal'] = '\n'.join(line_iter)
            break
        else:  # normal line
            if section is None:
                section = 'VERSE {}'.format(verse_counter)
                verse_counter += 1
            if '|' in line:
                line = re.sub(r'(^|[^\[])\|([^]]|$)', '[|]', line)
            section_lines.append(line.rstrip())

    if section is not None and section_lines:
        song['sections'][section] = '\n'.join(section_lines)

    return song
