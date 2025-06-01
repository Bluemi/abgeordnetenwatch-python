from typing import Optional, Dict

from pydantic import BaseModel, Field

from abgeordnetenwatch_python.models.questions_answers import QuestionAnswerResult, QuestionsAnswers


class CacheInfo(BaseModel):
    questions_answers: QuestionsAnswers
    num_questions_missing: int = -1
    num_answers_missing: int = -1
    lookup: Optional[Dict[str, QuestionAnswerResult]] = Field(None, exclude=True)

    def get_by_url(self, url: str) -> Optional[QuestionAnswerResult]:
        if self.lookup is None:
            self.lookup = {qa.url: qa for qa in self.questions_answers.questions_answers}
        return self.lookup.get(url)

    def should_cache(self, cache_qa: Optional[QuestionAnswerResult]) -> bool:
        # if we don't have something to cache, we don't do it
        if cache_qa is None:
            return False

        # never cache, if the question is missing
        if cache_qa.question is None:
            return False

        # always cache if the answer is given
        if cache_qa.answer is not None:
            return True

        # cache, if there is no answer anymore to expect
        return self.num_answers_missing == 0

    def is_question_missing(self) -> bool:
        return self.num_questions_missing != 0
