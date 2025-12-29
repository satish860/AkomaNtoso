"""Line information model for tracking document lines with page numbers."""
from pydantic import BaseModel


class LineInfo(BaseModel):
    """Metadata for a single line in the extracted document."""
    line_num: int   # 1-indexed, sequential across document
    page: int       # PDF page number (from [PAGE:N] markers)
    text: str       # Line content
