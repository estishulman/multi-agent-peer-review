from abc import ABC, abstractmethod
from ..models.review_result import ReviewResult, ReviewMode

class BaseReviewer(ABC):

    @abstractmethod
    def review(
        self,
        *,
        question: str,
        answer: str | None,
        mode: ReviewMode
    ) -> ReviewResult:
        pass
