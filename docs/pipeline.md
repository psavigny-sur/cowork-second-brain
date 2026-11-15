# Pipeline

See the README for the overview. Details that matter in practice:

## Inputs
Raw screenshots stay untouched in one folder. A batch is a date range, chosen by me. A preparation script copies the files of that range into a working folder, computes checksums and writes a manifest, and the count is checked against a plan table.

## Review with contact sheets
A script lays out 6 previews per sheet image, numbered globally. Subagents on a small model read about 6 sheets each (36 previews) in parallel and answer one line per preview. The stronger model then checks only uncertain cases:
- duplicate or defect candidates (found by comparing neighbouring images as small grayscale versions, plus visual pair comparison),
- author attribution where badges such as "Author" appear,
- shortened-link codes in the original image,
- a small sample of sheets.

## Mapping
A Python file declares threads as `t(author, topic, folder, type, tags, files, description)`, where `files` are preview numbers in thread order, plus a `DEFECT` list. A completeness assertion over all preview numbers runs before anything is renamed.

## Archive and finalize
`archive` renames, moves, makes thumbnails and writes Markdown. `finalize` updates the SQLite database (always on a local copy, never directly on a network mount), the HTML browser data line and the folder indexes. Before finalizing, backups of the database, the browser file and the ratings file are made.

## Links
OCR (Tesseract) scans every image; very tall images are scanned in strips; the scan is resumable. Only complete, readable URLs are kept; truncated ones, one-time access links and password links are dropped.

## Browser
The archive browser is one HTML file. Search and filters run in the page. Ratings (1-3 stars plus a short note) and the readable toggle are saved by `server/archive_server.py`; without the server they only live in the browser.

## Lessons
- Never regenerate the whole HTML file; only replace the data line, or the interface functions are lost.
- Do not rename threads without renaming their keys in the ratings and settings files.
- Write the handoff file after every batch, so a fresh conversation can continue.
