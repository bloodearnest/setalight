import pytest
import parse


TEST_CHORDS = {
    # no chords
    'NC': {'nochords': 'NC'},
    'nc': {'nochords': 'nc'},
    'N.C': {'nochords': 'N.C'},
    'N.C.': {'nochords': 'N.C.'},
    'NC.': {'nochords': 'NC.'},
    # note
    'A': {'note': 'A'},
    'Ab': {'note': 'Ab'},
    'A#': {'note': 'A#'},
    'A♭': {'note': 'A♭'},
    'A♯': {'note': 'A♯'},
    # third
    'Abm': {'note': 'Ab', 'third': 'm'},
    'Abmin': {'note': 'Ab', 'third': 'min'},
    'Abmaj': {'note': 'Ab', 'third': 'maj'},
    'AbM': {'note': 'Ab', 'third': 'M'},
    'AbmM': {'note': 'Ab', 'third': 'mM'},
    # fifth
    'Abaug': {'note': 'Ab', 'fifth': 'aug'},
    'Abdim': {'note': 'Ab', 'fifth': 'dim'},
    'Ab+': {'note': 'Ab', 'fifth': '+'},
    'Abø': {'note': 'Ab', 'fifth': 'ø'},
    'Ab°': {'note': 'Ab', 'fifth': '°'},
    # number
    'Ab2': {'note': 'Ab', 'number': '2'},
    'Ab4': {'note': 'Ab', 'number': '4'},
    'Ab(4)': {'note': 'Ab', 'number': '(4)'},
    'Ab6': {'note': 'Ab', 'number': '6'},
    'Ab9': {'note': 'Ab', 'number': '9'},
    'Ab11': {'note': 'Ab', 'number': '11'},
    'Ab13': {'note': 'Ab', 'number': '13'},
    # subtraction
    'Abno3': {'note': 'Ab', 'subtraction': 'no3'},
    'Abno3rd': {'note': 'Ab', 'subtraction': 'no3rd'},
    'Ab(no3)': {'note': 'Ab', 'subtraction': '(no3)'},
    'Ab(no3rd)': {'note': 'Ab', 'subtraction': '(no3rd)'},
    # altered
    'Ab♯5': {'note': 'Ab', 'altered': '♯5'},
    'Ab♭5': {'note': 'Ab', 'altered': '♭5'},
    'Abb5': {'note': 'Ab', 'altered': 'b5'},
    'Ab#5': {'note': 'Ab', 'altered': '#5'},
    'Ab#4': {'note': 'Ab', 'altered': '#4'},
    'Ab7+5': {'note': 'Ab', 'altered': '+5'},
    'Ab7-5': {'note': 'Ab', 'altered': '-5'},
    # suspension
    'Absus': {'note': 'Ab', 'suspension': 'sus'},
    'Absus2': {'note': 'Ab', 'suspension': 'sus2'},
    'Absus4': {'note': 'Ab', 'suspension': 'sus4'},
    # addition
    'Abadd9': {'note': 'Ab', 'addition': 'add9'},
    'Abadd11': {'note': 'Ab', 'addition': 'add11'},
    'Abadd13': {'note': 'Ab', 'addition': 'add13'},
    'Ab6/9': {'note': 'Ab', 'number': '6', 'addition': '/9'},
    # bass
    'Ab/E': {'note': 'Ab', 'bass': '/E'},
    'Ab/Eb': {'note': 'Ab', 'bass': '/Eb'},
    'Ab/E♭': {'note': 'Ab', 'bass': '/E♭'},
    'Ab/F#': {'note': 'Ab', 'bass': '/F#'},
    'Ab/F♯': {'note': 'Ab', 'bass': '/F♯'},
}


@pytest.mark.parametrize('input,output', TEST_CHORDS.items())
def test_chord_regex_separate(input, output):
    match = parse.RE.CHORD.match(input)
    assert match
    groupdict = match.groupdict()
    for k, v in groupdict.items():
        if k in output:
            assert v == output[k], groupdict


# chords taken from
# https://callumacrae.github.io/regex-tuesday/challenge15.html
CHALLENGE_CHORDS = [
    'C',
    'E',
    'G',
    'A',
    'B♭',
    'F♯',
    'D',
    'Cmaj',
    'E♭M',
    'Dmin',
    'Fmin',
    'Em',
    'E♭m',
    'E+',
    'G+',
    'B♭+',
    'Aaug',
    'B♭aug',
    'C°',
    'B♭°',
    'Edim',
    'Fdim',
    'C6',
    'Cmaj6',
    'Dmin6',
    'D7',
    'Ddom7',
    'Fmaj7',
    'Gmin7',
    'C♯6',
    'FM6',
    'Gm7',
    'C♯m6',
    'Dm6',
    'F+7',
    'B+7',
    'E♭+7',
    'Eaug7',
    'Aaug7',
    'G♭aug7',
    'Cø',
    'Dø',
    'G♭ø',
    'Eø7',
    'Fø7',
    'F♯ø7',
    'Z',
    'H',
    'I',
    'F♭',
    'C♭',
    'E♯',
    'B♯',
    'Imaj',
    'ZM',
    'E♯M',
    'F♭maj',
    'Jmin',
    'E♯m',
    'F♭aug',
    'J+',
    'E♯+',
    'E♯dim',
    'C♭°',
    'B♯6',
    'H6',
    'Z7',
    'C5',
    'A3',
    'Ddom8',
    'F9',
    'B2',
    'Bm♯6',
    'HM6',
    'Zm7',
    'CMaj5',
    'Am3',
    'DM8',
    'Fmin9',
    'BM2',
    'J+7',
    'E♯+7',
    'Jaug7',
    'E♯aug7',
    'Cdom6',
    'Ddom6',
    'F♭ø',
    'Fø6',
    'Fø8',
]
RE_PART_NAMES = [
    k for k, v in
    sorted(parse.RE.CHORD.groupindex.items(), key=lambda i: i[1])
]
RE_CHORD_TMPL = ''.join('{{{}}}'.format(n) for n in RE_PART_NAMES)


@pytest.mark.parametrize('input', CHALLENGE_CHORDS)
def test_chord_regex_challenge(input):
    match = parse.RE.CHORD.match(input)
    assert match
    groupdict = match.groupdict()
    ctx = {k: groupdict.get(k, '') or '' for k in RE_PART_NAMES}
    assert RE_CHORD_TMPL.format(**ctx) == input


# these words should NOT match the chord regex
# Am and Em will match - nothing we can do about that :(
@pytest.mark.parametrize('input', [
    'As',
    'Ag',
    'At',
    'Ac',
    'An',
    'am',
    'Be',
    'By',
    'Cut',
    'Can',
    'Do',
    'Day',
    'Dry',
    'Eh',
    'Eye',
    'Eat',
    'Far',
    'Fed',
    'Few',
    'Go',
    'God',
    'Got',
    # crazy german note letters
    'Ha',
    'Hi',
    'Ho',
    'Had',
    'Has',
    'Her',
    'His',
    'Hid',
    'How',
    'If',
    'It',
    'Is',
    'In',
    'Joy',
    'Job',
    'Jew',
])
def test_chord_regex_not_match(input):
    assert parse.RE.CHORD.match(input) is None


@pytest.mark.parametrize('input,tokens', [
    ('Abm7 |', ['Abm7', '|']),
    ('| Abm7', ['|', 'Abm7']),
    ('Abm7|',  ['Abm7', '|']),
    ('|Abm7',  ['|', 'Abm7']),
    ('A D(4) (To Pre-Chorus 1)', ['A', 'D(4)', '(To Pre-Chorus 1)'])
])
def test_tokenise_chords(input, tokens):
    assert parse.tokenise_chords(input) == tokens


@pytest.mark.parametrize('input,indices', [
    ('Abm7 |', [(0, 'Abm7'), (5, '|')]),
    ('| Abm7', [(0, '|'), (2, 'Abm7')]),
    ('Abm7|',  [(0, 'Abm7'), (4, '|')]),
    ('|Abm7',  [(0, '|'), (1, 'Abm7')]),
    ('A B (To Pre-Chorus)', [(0, 'A'), (2, 'B'), (4, '(To Pre-Chorus)')])
])
def test_chord_indicies(input, indices):
    assert list(parse.chord_indicies(input)) == indices


CHORD_LINES = {
    'Abm7': True,
    'B | E': True,
    'A E (To Pre-Chorus)': True,
    'A way': False,
}


@pytest.mark.parametrize('input,is_chords', CHORD_LINES.items())
def test_is_chord_line(input, is_chords):
    assert parse.is_chord_line(input.split()) == is_chords


def chordpro_line_testcases():
    yield None, "lyric", "lyric"
    yield "chord", None, "chord"
    yield (  # longer chords
        " A    Bm   Cm",
        " word",
        "[A]word [Bm]    [Cm]",
    )
    yield (  # longer words
        " A",
        " word other",
        "[A]word other",
    )
    yield (  # inserts before word start
        "A",
        "word ",
        "[A]word",
    )
    yield (  # inserts before word start with space
        " A",
        " word ",
        "[A]word",
    )
    yield (  # inserts mid word
        "  A",
        " word ",
        "w[A]ord",
    )
    yield (  # inserts after word and consumes space
        "     A",
        " word ",
        "word [A]",
    )
    yield (  # inserts before word consumes space
        "A",
        " word ",
        "[A]word",
    )
    yield (  # consumes spaces
        "    Am7add9",
        "word       other",
        "word [Am7add9]other",
    )
    yield (  # consumes space until word
        "Am7add9",
        "   word ",
        "[Am7add9]word",
    )
    yield (  # preserves bars when no lyrics until later
        " | A | Bm | Cm   |",
        "            word  ",
        "[|] [A] [|] [Bm] [|] [Cm]word [|]",
    )
    yield (  # splits chords next to | and inserts spaces before chords
        "|C#m7 B|E  F#|  C#m7",
        "               Word",
        "[|] [C#m7] [B] [|] [E]  [F#] [|] W[C#m7]ord",
    )


@pytest.mark.parametrize('chords,lyrics,expected', chordpro_line_testcases())
def test_chordpro_line(chords, lyrics, expected):
    assert parse.chordpro_line(chords, lyrics) == expected
