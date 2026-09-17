from app.retrieval.base import RetrievalChunk
from datetime import datetime

def chunk_notice_version(
    notice_id: int,
    version_id: int,
    source_id: str,
    raw_text: str,
    title: str,
    publication_date: datetime | None,
    canonical_url: str | None,
    is_latest_version: bool
) -> list[RetrievalChunk]:
    """
    Deterministic paragraph/line-aware chunking preserving exact offsets.
    """
    chunks = []
    lines = raw_text.split('\n')
    
    current_start = 0
    current_chunk_lines = []
    current_chunk_length = 0
    
    # Simple chunking by paragraph (double newline) or max lines/length
    chunk_index = 0
    
    start_char = 0
    
    for i, line in enumerate(lines):
        line_len = len(line)
        
        # If line is empty, it might be a paragraph break
        is_break = (line.strip() == "")
        
        if not is_break:
            if not current_chunk_lines:
                start_char = current_start
            current_chunk_lines.append(line)
            current_chunk_length += line_len
            
        # We break if we hit a paragraph break and we have content, or if chunk gets too big
        if (is_break and current_chunk_lines) or current_chunk_length > 500 or (i == len(lines) - 1 and current_chunk_lines):
            end_char = current_start + line_len if (i == len(lines) - 1 and not is_break) else current_start
            
            chunk_text = '\n'.join(current_chunk_lines)
            
            # Recalculate exact end_char based on start_char and chunk_text
            exact_end_char = start_char + len(chunk_text)
            
            chunk = RetrievalChunk(
                chunk_id=f"{version_id}_{chunk_index}",
                notice_id=notice_id,
                version_id=version_id,
                source_id=source_id,
                start_char=start_char,
                end_char=exact_end_char,
                text=chunk_text,
                title=title,
                publication_date=publication_date,
                canonical_url=canonical_url,
                is_latest_version=is_latest_version
            )
            chunks.append(chunk)
            chunk_index += 1
            current_chunk_lines = []
            current_chunk_length = 0
            
        current_start += line_len + 1 # +1 for the \n that was split
        
    return chunks
