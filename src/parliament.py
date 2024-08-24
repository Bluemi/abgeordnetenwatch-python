from typing import List

import requests

from candidacy_mandate import get_candidacy_mandates
from parliament_period import get_parliament_periods


class Parliament:
    def __init__(self, iden, label):
        """
        Creates a new politician.
        :type iden: int
        """
        self.iden = iden
        self.label = label

    @staticmethod
    def from_json(data):
        return Parliament(
            iden=data['id'],
            label=data['label'],
        )

    def to_json(self):
        return dict(
            id=self.iden,
            label=self.label,
        )

    def get_api_url(self):
        return 'https://www.abgeordnetenwatch.de/api/v2/parliaments/{}'.format(self.iden)

    def get_url(self):
        return 'https://www.abgeordnetenwatch.de/{}'.format(self.label.lower())

    def get_politician_ids(self, verbose=True) -> List[int]:
        politician_ids = set()

        parliament_periods = get_parliament_periods(parliament_id=self.iden, limit=1000)
        for index, pp in enumerate(parliament_periods):
            if verbose:
                print('loading parliament period [{}/{}]: {}'.format(index+1, len(parliament_periods), pp.label),
                      end='', flush=True)
            candidacy_mandates = get_candidacy_mandates(parliament_period_id=pp.iden, limit=1000)
            if verbose:
                print(' (found {} politicians)'.format(len(candidacy_mandates)), flush=True)
            politician_ids.update(cm.politician_id for cm in candidacy_mandates)
        return sorted(politician_ids)

    def __repr__(self):
        return 'Parliament(id={}, label={})'.format(self.iden, self.label)


def get_parliaments(iden=None, label=None) -> List[Parliament]:
    """
    Calls the abgeordnetenwatch API to retrieve all parliaments matching the given parameters.

    :param iden: Id to use for filtering
    :param label: label to use for filtering
    :return: A list of Parliaments. Can be empty.
    """
    params = {}
    if iden is not None:
        params['id'] = iden
    if label is not None:
        params['label'] = label
    r = requests.get('https://www.abgeordnetenwatch.de/api/v2/parliaments', params=params)
    if r.ok:
        return [Parliament.from_json(par_data) for par_data in r.json()['data']]


def get_parliament(iden=None, label=None) -> Parliament:
    parliaments = get_parliaments(iden, label)
    assert len(parliaments), 'Expected 1 parliament, but found {}'.format(len(parliaments))
    return parliaments[0]
