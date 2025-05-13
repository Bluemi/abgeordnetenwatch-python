from typing import List, Optional
from pydantic import BaseModel

import requests
from .party import Party
from abgeordnetenwatch_python.questions_answers import QuestionAnswerResult, load_questions_answers


class Politician(BaseModel):
    id: int
    first_name: str
    last_name: str
    party: Optional[Party] = None
    residence: Optional[str] = None

    def get_api_url(self):
        return 'https://www.abgeordnetenwatch.de/api/v2/politicians/{}'.format(self.id)

    def get_url(self):
        first_name = self.first_name.lower().replace(' ', '-')
        last_name = self.last_name.lower().replace(' ', '-')
        return 'https://www.abgeordnetenwatch.de/profile/{}-{}'.format(first_name, last_name)

    async def load_questions_answers(self, verbose: bool = False, threads: int = 1) -> List[QuestionAnswerResult]:
        politician_url = self.get_url()
        return await load_questions_answers(politician_url, verbose=verbose, threads=threads)

    def get_label(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def __repr__(self):
        return 'Politician(id={}, first_name={} last_name={}, party={}, residence={})' \
               .format(self.id, self.first_name, self.last_name, self.party, self.residence)

    def get_full_name(self):
        """
        :return: the full name of the politician ("firstname lastname").
        """
        return '{} {}'.format(self.first_name, self.last_name)


def get_politicians(id=None, first_name=None, last_name=None, party=None, residence=None) -> List[Politician]:
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


def get_politician(id=None, first_name=None, last_name=None, party=None, residence=None) -> Politician:
    politicians = get_politicians(id, first_name, last_name, party, residence)
    assert len(politicians) == 1, 'Expected 1 politician, but found {}'.format(len(politicians))
    return politicians[0]
