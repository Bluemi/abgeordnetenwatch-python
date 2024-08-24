from typing import List

import requests

from politicians import Politician


class Parliament:
    def __init__(self, id, label):
        """
        Creates a new politician.
        :type id: int
        """
        self.id = id
        self.label = label

    @staticmethod
    def from_json(data):
        return Parliament(
            id=data['id'],
            label=data['label'],
        )

    def to_json(self):
        return dict(
            id=self.id,
            label=self.label,
        )

    def get_api_url(self):
        return 'https://www.abgeordnetenwatch.de/api/v2/parliaments/{}'.format(self.id)

    def get_url(self):
        return 'https://www.abgeordnetenwatch.de/{}'.format(self.label.lower())

    def get_politicians(self) -> List[Politician]:
        raise NotImplementedError()

    def __repr__(self):
        return 'Parliament(id={}, label={})'.format(self.id, self.label)


def get_parliaments(id=None, label=None) -> List[Parliament]:
    """
    Calls the abgeordnetenwatch API to retrieve all parliaments matching the given parameters.

    :param id: Id to use for filtering
    :param label: label to use for filtering
    :return: A list of Parliaments. Can be empty.
    """
    params = {}
    if id is not None:
        params['id'] = id
    if label is not None:
        params['label'] = label
    r = requests.get('https://www.abgeordnetenwatch.de/api/v2/parliaments', params=params)
    if r.ok:
        return [Parliament.from_json(par_data) for par_data in r.json()['data']]
