from pathlib import Path
from typing import List, Optional, Union

import aiohttp
from pydantic import BaseModel

from abgeordnetenwatch_python.models.party import Party
from abgeordnetenwatch_python.models.questions_answers import QuestionsAnswers
from abgeordnetenwatch_python.questions_answers.load_qa import load_questions_answers
from abgeordnetenwatch_python.cache import CacheInfo


class Politician(BaseModel):
    id: int
    first_name: str
    last_name: str
    api_url: str
    statistic_questions: Optional[int] = None
    statistic_questions_answered: Optional[int] = None
    abgeordnetenwatch_url: str
    party: Optional[Party] = None
    residence: Optional[str] = None

    async def load_questions_answers(
            self, session: aiohttp.ClientSession, verbose: bool = False, threads: int = 1,
            cache_info: Optional[CacheInfo] = None
    ) -> QuestionsAnswers:
        return await load_questions_answers(
            self.abgeordnetenwatch_url, session=session, verbose=verbose, threads=threads, cache_info=cache_info,
            politician_name=self.get_full_name()
        )

    def get_label(self) -> str:
        return '{} {}'.format(self.first_name, self.last_name)

    def __repr__(self) -> str:
        return 'Politician(id={}, first_name={} last_name={}, party={}, residence={})' \
               .format(self.id, self.first_name, self.last_name, self.party, self.residence)

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name} {self.id} ({self.party.label if self.party else "unknown"})'

    def get_full_name(self) -> str:
        """
        :return: the full name of the politician ("firstname lastname").
        """
        return '{} {}'.format(self.first_name, self.last_name)


async def get_politicians(
        session: aiohttp.ClientSession, id: Optional[int] = None, first_name: Optional[str] = None,
        last_name: Optional[str] = None, party: Optional[str] = None, residence: Optional[str] = None
) -> List[Politician]:
    """
    Calls the abgeordnetenwatch API to retrieve all politicians matching the given parameters.

    :param session: aiohttp session to use for making the request.
    :param id: Identifier or list of identifiers to use for filtering.
    :param first_name: First name or list of first names to use for filtering.
    :param last_name: Last name or list of last names to use for filtering.
    :param party: Porty or list of parties to use for filtering.
    :param residence: Residence or list of residences to use for filtering.
    :return: A (possibly empty) list of Politicians.
    """
    params = {}
    if id is not None:
        params['id'] = id
    if first_name is not None:
        params['first_name'] = first_name
    if last_name is not None:
        params['last_name'] = last_name
    if party is not None:
        params['party'] = party
    if residence is not None:
        params['residence'] = residence
    url = 'https://www.abgeordnetenwatch.de/api/v2/politicians'
    async with session.get(url, raise_for_status=True, params=params) as r:
        data = await r.json()
        return [Politician.model_validate(pol_data) for pol_data in data['data']]


async def get_politician(
        session: aiohttp.ClientSession, id: Optional[int] = None, first_name: Optional[str] = None,
        last_name: Optional[str] = None, party: Optional[str] = None, residence: Optional[str] = None
) -> Politician:
    """
    Retrieve a single politician based on specified parameters. The function filters
    politicians according to the provided criteria and ensures that exactly one
    politician satisfies these conditions. If more or fewer politicians are found,
    an assertion error will occur.

    :param session: aiohttp session to use for making the request.
    :param id: Optional. The unique identifier of the politician to retrieve.
    :param first_name: Optional. The first name of the politician to retrieve.
    :param last_name: Optional. The last name of the politician to retrieve.
    :param party: Optional. The political party of the politician to retrieve.
    :param residence: Optional. The residence location of the politician to
        retrieve.
    :return: The politician that matches the specified criteria.
    """
    politicians = await get_politicians(session, id, first_name, last_name, party, residence)
    if len(politicians) != 1:
        raise ValueError('Expected 1 politician, but found {}'.format(len(politicians)))
    return politicians[0]


def get_default_filename(politician: Union[Politician, str], outdir: Path) -> Path:
    """
    Creates the default filename for a politician.
    :param politician: The politician for which the filename should be created. Can also be the url of the politician.
    :param outdir: The directory where the file should be located.
    :return: A Path object with the filename.
    """
    if isinstance(politician, str):
        u = [u for u in politician.split('/') if u][-1]
        return outdir / f'{u}.json'
    elif isinstance(politician, Politician):
        return outdir / f'{politician.id:0>6}_{politician.first_name}_{politician.last_name}.json'
    raise TypeError(f'Invalid type for politician: {type(politician)}')
