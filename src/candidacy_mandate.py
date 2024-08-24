from typing import List

import requests

from parliament_period import ParliamentPeriod, get_parliament_period
from politicians import Politician, get_politician


class CandidacyMandate:
    def __init__(self, iden, label, politician_id, parliament_period_id):
        self.iden = iden
        self.label = label
        self.politician_id = politician_id
        self.parliament_period_id = parliament_period_id

    @staticmethod
    def from_json(data):
        return CandidacyMandate(
            iden=data['id'],
            label=data['label'],
            politician_id=data['politician']['id'],
            parliament_period_id=data['parliament_period']['id'],
        )

    def to_json(self):
        return dict(
            id=self.iden,
            label=self.label,
            politician_id=self.politician_id,
            parliament_period_id=self.parliament_period_id,
        )

    def get_politician(self) -> Politician:
        return get_politician(iden=self.politician_id)

    def get_parliament_period(self) -> ParliamentPeriod:
        return get_parliament_period(iden=self.parliament_period_id)

    def __repr__(self):
        return 'CandidacyMandate(id={}, label={} politician_id={}, parliament_period_id={})' \
            .format(self.iden, self.label, self.politician_id, self.parliament_period_id)


def get_candidacy_mandates(iden=None, politician_id=None, parliament_period_id=None, limit=100) -> List[CandidacyMandate]:
    """
    Calls the abgeordnetenwatch API to retrieve all parliaments matching the given parameters.

    :param iden: Id to use for filtering
    :param politician_id: id for the politician
    :param parliament_period_id: id for the parliament period
    :param limit: The maximal number of items to return
    :return: A list of CandidacyMandates. Can be empty.
    """
    params = {}
    if iden is not None:
        params['id'] = iden
    if politician_id is not None:
        params['politician'] = politician_id
    if parliament_period_id is not None:
        params['parliament_period'] = parliament_period_id
    params['range_end'] = str(limit)
    r = requests.get('https://www.abgeordnetenwatch.de/api/v2/candidacies-mandates', params=params)
    if r.ok:
        return [CandidacyMandate.from_json(par_data) for par_data in r.json()['data']]
