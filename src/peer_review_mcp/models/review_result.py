from dataclasses import dataclass
from typing import List, Literal
#from enum import Enum

#class ReviewMode(str, Enum):
#    VALIDATE = "validate"
#    POLISH = "polish"

ReviewMode = Literal["validate", "polish"]

@dataclass
class ReviewResult:
    mode: ReviewMode
    items: List[str]
