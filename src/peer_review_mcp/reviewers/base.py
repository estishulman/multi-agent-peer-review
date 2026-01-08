from abc import ABC, abstractmethod
from ..models.review_result import ReviewResult, ReviewMode

class BaseReviewer(ABC):  # Base interface for reviewers

    @abstractmethod
    async def review(
        self,
        *,
        question: str,
        answer: str | None,
        context_summary: str | None,
        mode: ReviewMode
    ) -> ReviewResult:
        """
        Run a review pass.

        Args:
            question: The original user question.
            answer: In `mode=='polish'` this is the answer to inspect; otherwise None.
            context_summary: Optional prior context; used in validate and can be used in polish.
            mode: Either 'validate' or 'polish' (see concrete reviewers).

        Returns:
            ReviewResult instance containing items produced by the reviewer.
        """
        pass
