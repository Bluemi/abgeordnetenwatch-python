import unicodedata
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel

import requests

from abgeordnetenwatch_python.cache import CacheSettings
from .party import Party
from abgeordnetenwatch_python.questions_answers.models import QuestionAnswerResult
from abgeordnetenwatch_python.questions_answers.load_qa import load_questions_answers


class Politician(BaseModel):
    id: int
    first_name: str
    last_name: str
    party: Optional[Party] = None
    residence: Optional[str] = None

    def get_api_url(self) -> str:
        return 'https://www.abgeordnetenwatch.de/api/v2/politicians/{}'.format(self.id)

    def get_url(self) -> str:
        first_name = normalize_for_url(self.first_name)
        last_name = normalize_for_url(self.last_name)
        return 'https://www.abgeordnetenwatch.de/profile/{}-{}'.format(first_name, last_name)

    async def load_questions_answers(
            self, verbose: bool = False, threads: int = 1, cache_settings: Optional[CacheSettings] = None
    ) -> List[QuestionAnswerResult]:
        cache_settings = cache_settings or CacheSettings.default()

        return await load_questions_answers(
            self.get_url(), verbose=verbose, threads=threads, cache_settings=cache_settings
        )

    def get_label(self) -> str:
        return '{} {}'.format(self.first_name, self.last_name)

    def __repr__(self) -> str:
        return 'Politician(id={}, first_name={} last_name={}, party={}, residence={})' \
               .format(self.id, self.first_name, self.last_name, self.party, self.residence)

    def get_full_name(self) -> str:
        """
        :return: the full name of the politician ("firstname lastname").
        """
        return '{} {}'.format(self.first_name, self.last_name)


def get_politicians(
        id: Optional[int] = None, first_name: Optional[str] = None, last_name: Optional[str] = None,
        party: Optional[str] = None, residence: Optional[str] = None
) -> List[Politician]:
    """
    Calls the abgeordnetenwatch API to retrieve all politicians matching the given parameters.

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
    r = requests.get('https://www.abgeordnetenwatch.de/api/v2/politicians', params=params)
    r.raise_for_status()
    return [Politician.model_validate(pol_data) for pol_data in r.json()['data']]


def get_politician(
        id: Optional[int] = None, first_name: Optional[str] = None, last_name: Optional[str] = None,
        party: Optional[str] = None, residence: Optional[str] = None
) -> Politician:
    """
    Retrieve a single politician based on specified parameters. The function filters
    politicians according to the provided criteria and ensures that exactly one
    politician satisfies these conditions. If more or fewer politicians are found,
    an assertion error will occur.

    :param id: Optional. The unique identifier of the politician to retrieve.
    :param first_name: Optional. The first name of the politician to retrieve.
    :param last_name: Optional. The last name of the politician to retrieve.
    :param party: Optional. The political party of the politician to retrieve.
    :param residence: Optional. The residence location of the politician to
        retrieve.
    :return: The politician that matches the specified criteria.
    """
    politicians = get_politicians(id, first_name, last_name, party, residence)
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


def normalize_for_url(text: str) -> str:
    text = text.lower()

    replacements = [
        (' ', '-'),
        ('ä', 'ae'),
        ('ö', 'oe'),
        ('ü', 'ue'),
        ('ß', 'ss'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    return text
