from typing import List

import requests
from pydantic import BaseModel

from .parliament import Parliament


class ParliamentPeriod(BaseModel):
    id: int
    label: str
    parliament: Parliament

    def __repr__(self):
        return 'ParliamentPeriod(id={} label="{}" parliament={})'.format(self.id, self.label, self.parliament_id)


def get_parliament_periods(id=None, parliament_id=None, limit=100) -> List[ParliamentPeriod]:
    """
    Calls the abgeordnetenwatch API to retrieve the ParliamentPeriod with the given id.

    :param id: Identifier to use for filtering
    :param parliament_id: The id of the parliament
    :param limit: Maximal number of entries to get
    :return: The ParliamentPeriod with the given id.
    """
    params = {}
    if id is not None:
        params['id'] = id
    if parliament_id is not None:
        params['parliament'] = parliament_id
    params['range_end'] = str(limit)
    r = requests.get('https://www.abgeordnetenwatch.de/api/v2/parliament-periods', params=params)
    r.raise_for_status()
    return [ParliamentPeriod.model_validate(par_per_data) for par_per_data in r.json()['data']]


def get_parliament_period(id=None, parliament_id=None, limit=100) -> ParliamentPeriod:
    pps = get_parliament_periods(id, parliament_id, limit)
    assert len(pps) == 1, 'Expected 1 parliament period, but found {}'.format(len(pps))
    return pps[0]
