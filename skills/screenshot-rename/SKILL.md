---
name: screenshot-rename
description: Rename and organise batches of screenshots into the "Author - Topic - N" scheme, group them into threads, sort them into topic folders and write thread and folder Markdown files.
---

# Screenshot rename and organise (generalised)

## Naming
`Author - Topic - N.jpg`
- **Author:** post author (never a commenter); company name for company posts; the featured person for videos; the publication for articles.
- **Topic:** short, specific, in the language of the content, without the platform name.
- **N:** 1..N within the thread, in reading order. LinkedIn profiles follow a fixed order: header, connections, experience, other sections, recommendations.

## Modes
1. **Raw batch:** files have device names such as `Screenshot_YYYYMMDD_HHMMSS_App.jpg`. Read content, group into threads, name, sort, write Markdown.
2. **Verify and fix:** files are named already. Check for wrong people in a series, wrong order, redundant platform names, numbering gaps; regenerate affected Markdown.

## Principles
- Image reading happens in subagents on a small model; only compact summaries return to the main conversation.
- Threads are decided by visual content, not by timestamp gaps alone.
- Dry run before any rename; check that sources exist and destinations do not.
- Flag uncertain files for a stronger model to check.

## Thread Markdown
```
# {Author} - {Topic}
**Folder:** {folder}
**Screenshots:** {N}

## Content
{max 5 lines}

## Links
- Screenshot 2: {url}

## Screenshots in this thread
- `{Author} - {Topic} - 1.jpg` - {one line}
```

## Folder index Markdown
Prose overview (2-4 sentences), threads grouped under 3-6 themes with one-line summaries, and a flat full-index table.
