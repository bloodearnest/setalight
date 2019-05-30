# setalight

A set list tool for musicians, focussed on a church worship setting.

Musicians need a way to have a prepared selection of song lyrics and
music available to them when playing in a band. Many musicians use
tablets, and either pdfs, OnSong, or chordpro based viewers. Current
options function, up to a point, but are lacking in various ways, and
their use is often fragmented amongst a team, with different people
using different things.


Setalight is designed to work a little differently, out of the authors'
observations and experiences playing and leading with many different
bands.


Some high level functional design goals:

1. Fit in with existing workflow for worship teams. This means working
   around emails with attachments, and dealing with PDFs.

2. Focus is managing a specific set, not a library of songs.

3. Optimise for live usage. This means maximising screen space, dark
   mode, and a good touch/swipe interface.

4. Optional usage - I can use it, even if others are using OnSong, etc.


Some technical goals:

1. Standalone web-app - there's no need for a platform specific app.

2. Offline use

3. Minimal backend, ideally serverless


# Usage

To build the js/css intro the dist/index.html template:

    make dist/index.html

To build a setlist from a directory of pdfs

    ./setalight <dir>

This will output setlist.html
