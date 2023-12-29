from typing import List

import requests
from party import Party


class Politician:
    def __init__(self, id, first_name, last_name, party=None, residence=None):
        """
        Creates a new politician.
        :type id: int
        :type first_name: str
        :type last_name: str
        :type party: Party
        :type residence: str
        """
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        assert isinstance(party, Party)
        self.party = party
        self.residence = residence

    @staticmethod
    def from_json(data):
        return Politician(
            id=data['id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            party=Party.from_json(data.get('party')),
            residence=data.get('residence')
        )

    def get_api_url(self):
        return 'https://www.abgeordnetenwatch.de/api/v2/politicians/{}'.format(self.id)

    def get_url(self):
        first_name = self.first_name.lower().replace(' ', '-')
        last_name = self.last_name.lower().replace(' ', '-')
        return 'https://www.abgeordnetenwatch.de/profile/{}-{}'.format(first_name, last_name)

    def get_label(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def __repr__(self):
        return 'Politician(id={}, first_name={} last_name={}, party={}, residence={})' \
               .format(self.id, self.first_name, self.last_name, self.party, self.residence)


def get_politicians(id=None, first_name=None, last_name=None, party=None, residence=None) -> List[Politician]:
    """
    Calls the abgeordnetenwatch API to retrieve all politicians matching the given parameters.

    :param id: Id or list of ids to use for filtering
    :param first_name: First name or list of first names to use for filtering
    :param last_name: Last name or list of last names to use for filtering
    :param party: Porty or list of parties to use for filtering
    :param residence: Residence or list of residences to use for filtering
    :return: A list of Politicians. Can be empty.
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
    if r.ok:
        return [Politician.from_json(pol_data) for pol_data in r.json()['data']]
    else:

