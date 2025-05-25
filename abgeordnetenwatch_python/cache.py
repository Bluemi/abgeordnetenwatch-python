import datetime
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

from platformdirs import user_cache_dir
from pydantic import BaseModel, Field

from abgeordnetenwatch_python.questions_answers.models import QuestionAnswerResult

MAX_WAIT_TIME_DELTA = datetime.timedelta(days=365)


@dataclass
class CacheIdentifier:
    identifier: str

    @staticmethod
    def from_politician_url(url: str) -> 'CacheIdentifier':
        """
        Returns an identifier for the given politician url.
        For https://www.abgeordnetenwatch.de/profile/abc-def/fragen-antworten/12345 this would be:
        "abc-def"

        :param url: The url of the politician.
        :return: An identifier distinguishing the politician.
        """
        parts = url.split('/')
        profile_index = parts.index('profile')
        identifier = parts[profile_index + 1]
        return CacheIdentifier(identifier)


class QuestionsAnswerCache(BaseModel):
    """Cache for storing question/answer results"""
    questions_answers: List[QuestionAnswerResult]
    lookup: Optional[Dict[str, QuestionAnswerResult]] = Field(None, exclude=True)

    @staticmethod
    def new(questions_answers: List[QuestionAnswerResult]) -> 'QuestionsAnswerCache':
        return QuestionsAnswerCache(questions_answers=questions_answers, lookup=None)

    def get_by_url(self, url: str) -> Optional[QuestionAnswerResult]:
        if self.lookup is None:
            self.lookup = {qa.url: qa for qa in self.questions_answers}
        return self.lookup.get(url)


@dataclass
class CacheSettings:
    dir: Path
    level: int

    @staticmethod
    def default(level: int = 1) -> 'CacheSettings':
        directory = Path(user_cache_dir('aw-python'))
        return CacheSettings(
            dir=directory,
            level=level
        )

    def get_cache_path(self, identifier: CacheIdentifier) -> Path:
        return self.dir / f'{identifier.identifier}.bin'

    def load_cache(self, identifier: CacheIdentifier) -> Optional[BaseModel]:
        path = self.get_cache_path(identifier)
        if self.level > 0 and path.exists():
            with open(path, 'rb') as f:
                return pickle.load(f)
        return None

    def dump_cache(self, identifier: CacheIdentifier, cache: BaseModel):
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.get_cache_path(identifier), 'wb') as f:
            # noinspection PyTypeChecker
            pickle.dump(cache, f)

    def cache_urls(self) -> bool:
        return self.level >= 3

    def cache_url(self, result: Optional[QuestionAnswerResult]) -> bool:
        if self.level == 0 or result is None:
            return False
        elif self.level == 1:
            # cache, if the question was answered
            if result.answer is not None:
                return True
            # cache, if the question was not answered for more than a year
            if result.question_date is not None:
                return datetime.date.today() - result.question_date > MAX_WAIT_TIME_DELTA
            else:
                # don't cache if we don't know when the question was asked
                return False
        elif self.level >= 2:
            return True
        else:
            raise ValueError(f'Invalid cache level: {self.level}')


def load_questions_answers_cache(
        cache_settings: Optional[CacheSettings], politician_url: str
) -> Optional[QuestionsAnswerCache]:
    cache_settings = cache_settings or CacheSettings.default()
    cache_identifier = CacheIdentifier.from_politician_url(politician_url)
    return cache_settings.load_cache(cache_identifier)


def dump_questions_answers_cache(
        cache_settings: Optional[CacheSettings], politician_url: str, cache: QuestionsAnswerCache
):
    cache_settings = cache_settings or CacheSettings.default()
    cache_identifier = CacheIdentifier.from_politician_url(politician_url)
    return cache_settings.dump_cache(cache_identifier, cache)
