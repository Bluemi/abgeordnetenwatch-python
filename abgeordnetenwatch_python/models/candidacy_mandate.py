from typing import List

import requests
from pydantic import BaseModel

from .parliament_period import ParliamentPeriod, get_parliament_period
from .politicians import Politician, get_politician


class CandidacyMandate(BaseModel):
    id: int
    label: str
    politician_id: int
    parliament_period_id: int

    def get_politician(self) -> Politician:
        return get_politician(id=self.politician_id)

    def get_parliament_period(self) -> ParliamentPeriod:
        return get_parliament_period(id=self.parliament_period_id)

    def __repr__(self):
        return 'CandidacyMandate(id={}, label={} politician_id={}, parliament_period_id={})' \
            .format(self.id, self.label, self.politician_id, self.parliament_period_id)


def get_candidacy_mandates(
        id=None, politician_id=None, parliament_period_id=None, limit=100
) -> List[CandidacyMandate]:
    """
    Calls the abgeordnetenwatch API to retrieve all parliaments matching the given parameters.

    :param id: Identifier to use for filtering
    :param politician_id: id for the politician
    :param parliament_period_id: id for the parliament period
    :param limit: The maximal number of items to return
    :return: A (possibly empty) list of CandidacyMandates.
    """
    params = {}
    if id is not None:
        params['id'] = id
    if politician_id is not None:
        params['politician'] = politician_id
    if parliament_period_id is not None:
        params['parliament_period'] = parliament_period_id
    params['range_end'] = str(limit)
    r = requests.get('https://www.abgeordnetenwatch.de/api/v2/candidacies-mandates', params=params)
    r.raise_for_status()

    data = _adapt_candidacy_mandate_data(r.json()['data'])
    return [CandidacyMandate.model_validate(par_data) for par_data in data]


def _adapt_candidacy_mandate_data(d):
    return [
        {
            'id': par_data['id'],
            'label': par_data['label'],
            'politician_id': par_data['politician']['id'],
            'parliament_period_id': par_data['parliament_period']['id'],
        } for par_data in d
    ]
