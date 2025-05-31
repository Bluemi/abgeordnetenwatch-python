import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class QuestionAnswerResult(BaseModel):
    url: Optional[str]
    question_date: Optional[datetime.date] = None
    question: Optional[str] = None
    question_addition: Optional[str] = None
    answer_date: Optional[datetime.date] = None
    answer: Optional[str] = None
    errors: List[str] = []

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'QuestionAnswerResult':
        new_data = data.copy()
        new_data['question_date'] = str_to_date(data['question_date']) if data['question_date'] else None
        new_data['answer_date'] = str_to_date(data['answer_date']) if data['answer_date'] else None
        return QuestionAnswerResult.model_validate(new_data)

    def get_question_date(self) -> str:
        return date_to_str(self.question_date)

    def get_answer_date(self) -> str:
        return date_to_str(self.answer_date)

    def __repr__(self) -> str:
        return ('QuestionAnswerResult(url={}, question_date={}, question={}, question_addition={}, '
                'answer_date={}, answer={})').format(
            self.url, self.get_question_date(), self.question, self.question_addition, self.get_answer_date(),
            self.answer
        )

    def __str__(self) -> str:
        return ('url={}\n  question_date={}\n  question={}\n  question_addition={}\n  answer_date={}\n  answer={}'
                .format(self.url, self.get_question_date(), self.question, self.question_addition,
                        self.get_answer_date(), self.answer)
                )


class QuestionsAnswers(BaseModel):
    questions_answers: List[QuestionAnswerResult]

    def __len__(self):
        return len(self.questions_answers)

    @staticmethod
    def empty() -> 'QuestionsAnswers':
        return QuestionsAnswers(questions_answers=[])


def str_to_date(date_text: str) -> datetime.date:
    return datetime.datetime.strptime(date_text, "%d.%m.%Y")


def date_to_str(date: Optional[datetime.date]) -> str:
    return date.strftime('%d.%m.%Y') if date is not None else 'XX.XX.XXXX'


type TqdmArgs = Optional[Dict[str, Any]]


def normalize_tqdm_args(tqdm_args: TqdmArgs, default_desc: Optional[str] = None) -> TqdmArgs:
    if tqdm_args is None:
        tqdm_args = {}
    else:
        tqdm_args = tqdm_args.copy()
    if 'desc' not in tqdm_args:
        tqdm_args['desc'] = default_desc
    return tqdm_args
