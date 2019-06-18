import base64
from collections import OrderedDict, defaultdict
import itertools
import re
import subprocess

import chardet
from pdfrw import PdfReader
import pdftitle


class RE:

    PAGE = re.compile(r'Page ?[A-Za-z0-9]+')
    KEY = re.compile(
        r'key\s*(?:[-:]|of)\s+\[?(?P<key>[A-G][♯♭#b]?)\]?'
        r'\s*(?:Capo (?P<capo>\d+))?',
        re.I,
    )
    TIME = re.compile(r'time\s+[-:]\s+(\d+/\d+)', re.I)
    TEMPO = re.compile(r'tempo\s+[-:]\s+(\d+)', re.I)
    SECTION = re.compile(r"""^\(?(
        intro|
        verse|
        chorus|
        refrain|
        bridge|
        pre[- ]?chorus|
        instrumental|
        interlude|
        turnaround|
        ending|
        coda|
        outro
        )\)?
    """, re.I | re.VERBOSE)
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
    CCLI = re.compile(r'CCLI.*# ?(\d+)', re.I)
    # used to split a chord line into tokens including splitting on |
    CHORD_SPLIT = re.compile(r"""
        [ ](\([^\d].*?\))|  # matches (To SECTION) or (CHORD), keep
        (\|)|               # bar lines, keep
        [ ]+                # spaces, discard
    """, re.VERBOSE)

    # CHORDPRO directive
    DIRECTIVE = re.compile(r'{(?P<directive>\w+):(?P<value>.*)}')


KEY_CHORDS = {
    'A':  'A Bm C#m D E F#m',
    'Ab': 'Ab Bbm Cm Db Eb Fm',
    'A#': 'A# Cm Dm D# F Gm',
    'B':  'B C#m D#m E F# G#m',
    'Bb': 'Bb Cm Dm Eb F Gm',
    'C':  'C Dm Em F G Am',
    'C#': 'C# D#m Fm F# G# A#m',
    'D':  'D Em F#m G A Bm',
    'Db': 'Db Ebm Fm Gb Ab Bbm',
    'D#': 'D# Fm Gm G# A# Cm',
    'E':  'E F#m G#m A B C#m',
    'Eb': 'Eb Fm Gm Ab Bb Cm',
    'F':  'F Gm Am Bb C Dm',
    'F#': 'F# G#m A#m B C# D#m',
    'G':  'G Am Bm C D Em',
    'Gb': 'Gb Abm Bbm B Db Ebm',
    'G#': 'G# A#m B#m C# D# Fm',
}

CHORD_KEYS = defaultdict(list)

for key, chords in KEY_CHORDS.items():
    for chord in chords.split(' '):
        CHORD_KEYS[chord].append(key)


def search(regex, text):
    """Helper for regex searching."""
    match = regex.search(text)
    search.match = match
    return match


def infer_key(chords):
    counts = defaultdict(int)
    for c in chords:
        if search(RE.CHORD, c):
            d = search.match.groupdict()
            if d['note']:
                simple = d['note'] + (d.get('third') or '')
                if simple in CHORD_KEYS:
                    for key in CHORD_KEYS[c]:
                        counts[key] += 1

    if counts:
        result = list(sorted(counts.items(), key=lambda i: i[1]))
        return result[-1][0]
    else:
        return None


def add_inferred_key(song):
    seen = []
    for section in song['sections'].values():
        chords = re.findall(r'\[(.*?)\]', section)
        seen.extend(chords)
    inferred_key = infer_key(seen)
    song['inferred_key'] = inferred_key
    if not song['key']:
        song['key'] = inferred_key


def clean_encoding(contents):
    contents = contents.replace('\u200B', '')  # no zero-width spaces
    contents = contents.replace('\t', ' ')  # no tabs
    contents = contents.replace('\x85', ' ')   # no weird new lines
    return contents


def strip_brackets(l):
    if not l:
        return l
    if l[0] == '(' and l[-1] == ')':
        return l[1:-1].replace('\\', '')
    else:
        return l.replace('\\', '')


def convert_pdf(song, path, output):
    """Parse and convert a pdf into text, including metadata.

    Deals with various common conversion errors."""

    meta = PdfReader(str(path)).Info
    song['author'] = strip_brackets(meta.Author)
    song['creator'] = strip_brackets(meta.Creator)
    song['producer'] = strip_brackets(meta.Producer)
    if meta.Title:
        # explicit title in metadata, use that. Fairly rare.
        song['title'] = strip_brackets(meta.Title.strip())
    else:
        # multiline titles get mangles when converting to text, so we use
        # a library that uses heuristics to guess the title.
        # It is slow, though
        try:
            title = pdftitle.get_title_from_file(str(path)).strip()
        except Exception:
            pass
        else:
            song['title'] = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)

    cmd = ['pdftotext', '-layout', '-enc', 'UTF-8', '-eol', 'unix', '-nopgbrk']
    subprocess.run(cmd + [str(path), output])
    with open(output, 'r') as f:
        contents = f.read()
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


def is_chord_line(tokens, comments=True):
    """Is this line a chord line?"""
    chords = not_chords = 0
    for t in tokens:
        # bars
        if t == '|':
            chords += 1
        elif comments and t[0] == '(' and t[-1] == ')':
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
        tokens = re.split(r'( +)|(:?\|\|:?)|(\|)', chord_line)
        output = []
        for token in tokens:
            if token is None:
                continue
            if token.strip():
                output.append('[' + token + ']')
            else:
                output.append(token)
        return ''.join(output)
    else:
        return chord_and_lyrics(chord_line, lyric_line)


def chord_and_lyrics(chord_line, lyric_line):
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


def parse_header(song, header):
    # first line has 'Key - X' or 'Key of X'
    title = song['title']
    if title:
        zipped = zip(title.lower(), header[0].lower())
        for i, (t, h) in enumerate(zipped):
            if t != h:
                break
        header[0] = header[0][i:]

    parsed_title = []
    key = RE.KEY.search(header[0])
    if key:
        groupdict = key.groupdict()
        song['key'] = groupdict.get('key')
        song['capo'], groupdict.get('capo')
        position = key.span()[0]
        parsed_title.append(header[0][:position].strip())
    elif ' key ' in header[0].lower():
        # we sometimes can't extract the actual key, and are left with "Key - "
        # so clean that up
        position = header[0].lower().find(' key ')
        parsed_title.append(header[0][:position].strip())
    else:
        parsed_title.append(header[0].strip())

    if song['title'] is None:
        song['title'] = ' '.join(parsed_title)

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
        author = header[1][:pos].strip()
        current = song.get(author)
        if current and current.lower() != author.lower():
            song['alt_author'] = author
        else:
            song['author'] = author

    if len(header) > 2:
        song['blurb'] = '\n'.join(header[2:])


def parse_pdf(path, build_dir):
    """Parse a pdf intro plain text.

    Right now this is simple and a bit brittle. It converts the pdf to text
    using pdttotext from the poppler project, then attempts to parse that
    textual output into a semantic song data.

    In the future, it could parse the pdf directly.
    """

    song = new_song()
    song['type'] = 'pdf'
    sheet = convert_pdf(song, path, str(build_dir / (path.stem + '.raw')))

    sheet_lines = sheet.split('\n')
    # skip any leading blank lines
    for i, line in enumerate(sheet_lines):
        if line.strip():
            break

    lines = sheet_lines[i:]

    failed = False
    header = []
    for i, line in enumerate(lines[:10]):
        if RE.SECTION.search(line):
            break
        elif is_chord_line(tokenise_chords(line), comments=False):
            break
        elif search(RE.CCLI, line):
            failed = True
            parse_legal(song, lines[i:])
            break
        else:
            header.append(line)
    else:
        # no discernable header, so go from start
        i = 0

    if header:
        parse_header(song, header)

    parse_sections(song, iter(lines[i:]))

    if failed or not song['sections']:
        song['type'] = 'pdf-failed'
        song['pdf'] = base64.b64encode(path.read_bytes()).decode('utf8')

    return song


def parse_legal(song, lines):
    lines = list(lines)
    if search(RE.CCLI, lines[0]):
        song['ccli'] = search.match.groups()[0]
    song['legal'] += '\n'.join(l.strip() for l in lines)


def parse_sections(song, line_iter):
    section_name = None
    section_lines = []
    chord_line = None
    superscript_line = None

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
                if section_name is None:
                    if all(l is None for c, l in section_lines):
                        # all chords, is intro
                        section_name = 'INTRO'
                    else:
                        # some lyrics, assume V1
                        section_name = 'VERSE 1'
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
        if section_name is None:
            # no section names at all. It happens.
            section_name = 'VERSE 1'
        song['sections'][section_name] = section_lines

    # did we reached the CCLI number
    if ccli is not None:
        parse_legal(song, [line] + list(line_iter))

    # convert into chordpro
    for name, section_lines in song['sections'].items():
        for chords, _ in section_lines:
            if not chords:
                continue
        song['sections'][name] = '\n'.join(
            chordpro_line(c, l) for c, l in section_lines
        )


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
    raw = path.read_bytes()
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
            # else:
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
