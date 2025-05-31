from typing import List, Optional, Dict, Any

import aiohttp
from pydantic import BaseModel

from abgeordnetenwatch_python.models.parliament_period import ParliamentPeriod, get_parliament_period
from abgeordnetenwatch_python.models.politicians import Politician, get_politician


class CandidacyMandate(BaseModel):
    id: int
    label: str
    politician_id: int
    parliament_period_id: int

    async def get_politician(self, session: aiohttp.ClientSession) -> Politician:
        return await get_politician(session, id=self.politician_id)

    async def get_parliament_period(self, session: aiohttp.ClientSession) -> ParliamentPeriod:
        return await get_parliament_period(session, id=self.parliament_period_id)

    def __repr__(self) -> str:
        return 'CandidacyMandate(id={}, label={} politician_id={}, parliament_period_id={})' \
            .format(self.id, self.label, self.politician_id, self.parliament_period_id)


async def get_candidacy_mandates(
        session: aiohttp.ClientSession, id: Optional[int] = None, politician_id: Optional[int] = None,
        parliament_period_id: Optional[int] = None, limit: int = 100
) -> List[CandidacyMandate]:
    """
    Calls the abgeordnetenwatch API to retrieve all parliaments matching the given parameters.

    :param session: aiohttp session to use for making the request.
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

    url = 'https://www.abgeordnetenwatch.de/api/v2/candidacies-mandates'
    async with session.get(url, raise_for_status=True, params=params) as r:
        data = _adapt_candidacy_mandate_data((await r.json())['data'])
        return [CandidacyMandate.model_validate(par_data) for par_data in data]


def _adapt_candidacy_mandate_data(d: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            'id': par_data['id'],
            'label': par_data['label'],
            'politician_id': par_data['politician']['id'],
            'parliament_period_id': par_data['parliament_period']['id'],
        } for par_data in d
    ]
