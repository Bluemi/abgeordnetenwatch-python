import json
import warnings
from pathlib import Path
from typing import Optional, List

import aiohttp
from pydantic import BaseModel, ValidationError
from tqdm.asyncio import tqdm

from abgeordnetenwatch_python.cache import CacheInfo
from abgeordnetenwatch_python.questions_answers.load_qa import load_questions_answers, sort_questions_answers
from abgeordnetenwatch_python.models.candidacy_mandate import get_candidacy_mandates
from abgeordnetenwatch_python.models.politicians import Politician
from abgeordnetenwatch_python.models.questions_answers import QuestionsAnswers, TqdmArgs


class PoliticianDossier(BaseModel):
    politician: Politician
    mandate_ids: List[int]
    questions_answers: QuestionsAnswers

    def sort_questions_answers(self, sort_by: str):
        self.questions_answers = sort_questions_answers(
            self.questions_answers, sort_by
        )

    @staticmethod
    def from_file(filename: Path) -> Optional['PoliticianDossier']:
        if filename.is_file():
            with open(filename, 'r') as f:
                data = json.load(f)
                try:
                    return PoliticianDossier.model_validate(data)
                except ValidationError:
                    warnings.warn(f'Unsupported file format in {filename} - skipping file.')
                    return None
        return None

    def dump_to_file(self, filename: Path):
        filename.parent.mkdir(exist_ok=True, parents=True)
        with open(filename, 'w') as f:
            data = self.model_dump(mode='json')
            json.dump(data, f, indent=2, sort_keys=True)


async def load_politician_dossier(
        politician: Politician, session: aiohttp.ClientSession, cache: Optional[PoliticianDossier] = None,
        verbose: bool = True, threads: int = 1, url_threads: int = -1, tqdm_args: TqdmArgs = None,
) -> PoliticianDossier:
    """
    Loads all questions and answers for a politician together with the current candidacy mandate.

    :param politician: The politician for which to load the dossier.
    :param session: The aiohttp session to use for making the request.
    :param cache: An optional cache to use for caching the dossier. If None, no caching will be used.
    :param verbose: Output progress information.
    :param threads: The number of threads to use for loading the questions and answers.
    :param url_threads: The number of threads to use for loading individual question and answer pages.
                        If -1, the argument "threads" is used.
    :param tqdm_args: Additional arguments to pass to tqdm.
    """
    tqdm_obj = None
    if verbose:
        tqdm_obj = tqdm(desc=f"preparing {politician.get_full_name()}", bar_format='{desc}', leave=None)
        tqdm_obj.refresh()
    candidacy_mandates = await get_candidacy_mandates(session, politician_id=politician.id)

    mandate_ids = [cm.id for cm in candidacy_mandates]

    cache_info = None
    if cache is not None:
        if cache.politician.id != politician.id:
            raise ValueError(
                f'Cache politician id {cache.politician.id} does not match requested politician id {politician.id}'
            )
        cache_info = CacheInfo(questions_answers=cache.questions_answers, lookup=None)
        if set(cache.mandate_ids) == set(mandate_ids):
            cache_info.num_questions_missing =\
                (politician.statistic_questions or 0) - (cache.politician.statistic_questions or 0)
            cache_info.num_answers_missing =\
                (politician.statistic_questions_answered or 0) - (cache.politician.statistic_questions_answered or 0)

    if verbose:
        tqdm_obj.close()

    questions_answers = await load_questions_answers(
        politician.abgeordnetenwatch_url, session=session, verbose=verbose, threads=threads, url_threads=url_threads,
        cache_info=cache_info, tqdm_args=tqdm_args, politician_name=politician.get_full_name()
    )

    return PoliticianDossier(politician=politician, mandate_ids=mandate_ids, questions_answers=questions_answers)


async def load_politician_dossier_with_cache_file(
        politician: Politician, filename: Path, session: aiohttp.ClientSession, sort_by: Optional[str] = None,
        verbose: bool = False, threads: int = 1, url_threads: int = -1, tqdm_args: TqdmArgs = None
):
    cache = PoliticianDossier.from_file(filename)
    politician_dossier = await load_politician_dossier(
        politician, session=session, verbose=verbose, threads=threads, url_threads=url_threads, cache=cache,
        tqdm_args=tqdm_args
    )
    politician_dossier.sort_questions_answers(sort_by)
    politician_dossier.dump_to_file(filename)
