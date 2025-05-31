import datetime
from enum import StrEnum
from typing import List, Optional

import aiohttp
from pydantic import BaseModel

from abgeordnetenwatch_python.models.parliament import Parliament


class ParliamentPeriodType(StrEnum):
    ELECTION = 'election'
    LEGISLATURE = 'legislature'


class ParliamentPeriod(BaseModel):
    id: int
    label: str
    parliament: Parliament
    start_date_period: datetime.date
    end_date_period: datetime.date
    type: ParliamentPeriodType

    def __repr__(self):
        return 'ParliamentPeriod(id={} label="{}" parliament={} period={} - {})'.format(
            self.id, self.label, self.parliament.id, self.start_date_period, self.end_date_period
        )

    def is_legislature(self) -> bool:
        return self.type == ParliamentPeriodType.LEGISLATURE

    def is_election(self) -> bool:
        return self.type == ParliamentPeriodType.ELECTION


async def get_parliament_periods(
        session: aiohttp.ClientSession, id: Optional[int] = None, parliament_id: Optional[int] = None, limit: int = 100
) -> List[ParliamentPeriod]:
    """
    Calls the abgeordnetenwatch API to retrieve the ParliamentPeriod with the given id.

    :param session: aiohttp session to use for making the request.
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
    url = 'https://www.abgeordnetenwatch.de/api/v2/parliament-periods'
    async with session.get(url, raise_for_status=True, params=params) as r:
        data = await r.json()
        return [ParliamentPeriod.model_validate(par_per_data) for par_per_data in data['data']]


async def get_parliament_period(
        session: aiohttp.ClientSession, id: Optional[int] = None, parliament_id: Optional[int] = None, limit: int = 100
) -> ParliamentPeriod:
    pps = await get_parliament_periods(session, id, parliament_id, limit)
    assert len(pps) == 1, 'Expected 1 parliament period, but found {}'.format(len(pps))
    return pps[0]
