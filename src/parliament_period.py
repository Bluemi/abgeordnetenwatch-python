from typing import List

import requests


class ParliamentPeriod:
    def __init__(self, id, label, parliament_id):
        self.id = id
        self.label = label
        self.parliament_id = parliament_id

    @staticmethod
    def from_json(data):
        return ParliamentPeriod(
            id=data['id'],
            label=data['label'],
            parliament_id=data['parliament']['id'],
        )

    def __repr__(self):
        return 'ParliamentPeriod(id={} label="{}" parliament={})'.format(self.id, self.label, self.parliament_id)


def get_parliament_periods(id=None, parliament_id=None, limit=100) -> List[ParliamentPeriod]:
    """
    Calls the abgeordnetenwatch API to retrieve the ParliamentPeriod with the given id.

    :param id: Id to use for filtering
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
    if r.ok:
        return [ParliamentPeriod.from_json(par_per_data) for par_per_data in r.json()['data']]


def get_parliament_period(id=None, parliament_id=None, limit=100) -> ParliamentPeriod:
    pps = get_parliament_periods(id, parliament_id, limit)
    assert len(pps) == 1, 'Expected 1 parliament period, but found {}'.format(len(pps))
    return pps[0]
