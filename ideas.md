Flow
----

So, the initial basic idea is as follows:

1. Worship leaders sends email out with attachments
   (pdfs/onsong/chordpro). They cc: the setalight email address, or
   someone else forwards it to that email.

2. That email (probably Amazon SES) triggers a lambda function, which
   grabs the email and attachments, and builds a stand alone HTML page
   and puts it in S3.

3. It then replies to that email with a link to the S3 url.

4. Any further updates to that email thread result in the HTML document
   being updated with any later attachments.


Using serverless means this should be ~free to run, assuming we clean up
the S3 files a month after they were created.

Basing the flow on a given service/set makes things nice and clean. We
do not need any long term state.


HTML Document
-------------

Regards the HTML document, the idea is:

1. Stand alone. Embed all CSS/JS and data inside the one document. This
   provides:
   
     a) offline support (w/o needing service workers), just save the
     html.
   
     b) single atomic data to store/download/delete. No external links.

2. The first 'page' of the document is a summary, showing details about
   the set. It should include who sent it and the email text, as these
   may have important relevant details in. Any email replies should also
   be included when updated.

3. All songs are embedded in the document as strings in chordpro format,
   and rendered into the DOM via JS.

4. As a fallback, if a pdf cannot be converted to chordpro, then we can
   embed it and use pdf.js to render it.

5. Songs are ordered in order of attachments in email.

6. Current thinking on front end stack:

   - minimal dependencies
   - vanilla js (es6), no babel, for now.
   - https://github.com/martijnversluis/ChordJS
   - https://github.com/martijnversluis/ChordSheetJS
   - https://github.com/developit/preact for UI
   - https://github.com/developit/htm for runtime JSX templating
   - pdf.js


UI Ideas
--------

1. The interface should be touch based, with assumption of tablet usage.
   Swipe left right to change song, up/down to move within a song.

2. Optimised for screen space. Ideas include:

   - No uneeded author or ccli information. Or even title?
   - Can turn off chords (per section?)
   - Can hide whole sections (most people know the chorus lyrics, for
     example)
   - Attempt to optimise font size per song to display as much
     information as possible without needing to scroll down.
   - no page-breaks across sections?
   - Optimise for quick action mid playing, e.g. tap to scroll down?
     Double tap to scroll to top? Two finger tap next song?

3. Dark mode option?

4. Transpose/Capo option.

5. Can re-order songs via drag and drop or similar.

6. Can edit songs, storing local version in localStorage.

7. All the above UI state should be persisted in browser localStorage,
   so that preferences remain across reloads and updates.


Dealing with PDFs
-----------------

The main legal source of music is CCLI's SongSelect, which only provides
a PDF version for download. Which sucks.

However, most PDFs on SongSelect are textual in nature, and the raw data
can be extracted, to some degree.

Some are older image based PDFs though, and Setalight will likely have
to fall back to pdf rendering with pdf.js, which sucks.


Future ideas
------------

Use https://peerjs.com/ or similar to link sets together for
synchronised songs changes?

