from dataclasses import dataclass
from typing import List, Literal

from peer_review_mcp.models.review_point import ReviewPoint

ReviewMode = Literal["validate", "polish"]

@dataclass
class ReviewResult:
    mode: ReviewMode
    items: List[ReviewPoint | str]

