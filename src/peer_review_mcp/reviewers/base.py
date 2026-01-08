from abc import ABC, abstractmethod
from ..models.review_result import ReviewResult, ReviewMode

class BaseReviewer(ABC):  # Base interface for reviewers; `answer` param acts as context in validate mode

    @abstractmethod
    async def review(
        self,
        *,
        question: str,
        answer: str | None,
        mode: ReviewMode
    ) -> ReviewResult:
        """
        Run a review pass.

        Args:
            question: The original user question.
            answer: In `mode=='polish'` this is the answer to inspect; in `mode=='validate'`
                this parameter is used to pass a context summary (not a literal answer).
            mode: Either 'validate' or 'polish' (see concrete reviewers).

        Returns:
            ReviewResult instance containing items produced by the reviewer.
        """
        pass
