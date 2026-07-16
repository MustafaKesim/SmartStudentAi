"""
Splits an uploaded document's pages into study-sized sections for the
paginated Summarize feature (read a few pages at a time, click Next).
"""

# Pages are stored joined by this marker so we can still split the document
# back into individual pages later (for page-range summaries), while /ask
# and /quiz can just strip it out and use the whole text.
PAGE_DELIMITER = "\n\n<<<PAGE_BREAK>>>\n\n"


def compute_chunks(total_pages):
    """Split a document's pages into study-sized chunks: 2 chunks if the
    whole thing is 20 pages or less, otherwise ~10 pages per chunk. Returns
    a list of (start_page, end_page) tuples, 0-indexed and end-exclusive."""
    if total_pages <= 20:
        chunk_count = 2
    else:
        chunk_count = -(-total_pages // 10)  # ceiling division, no math.ceil needed
    chunk_count = max(1, min(chunk_count, total_pages))

    base_size = total_pages // chunk_count
    remainder = total_pages % chunk_count

    # Spread any leftover pages across the first few chunks (one extra page
    # each) instead of dumping them all into a lopsided last chunk.
    chunks = []
    start = 0
    for i in range(chunk_count):
        size = base_size + (1 if i < remainder else 0)
        chunks.append((start, start + size))
        start += size
    return chunks
