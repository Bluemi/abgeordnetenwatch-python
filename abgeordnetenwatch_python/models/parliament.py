from typing import List, Optional

import aiohttp
from pydantic import BaseModel


class Parliament(BaseModel):
    id: int
    label: str
    api_url: str
    abgeordnetenwatch_url: str

    async def get_politician_ids(self, session: aiohttp.ClientSession, verbose: bool = True) -> List[int]:
        # local imports to prevent cyclic import
        from abgeordnetenwatch_python.models.parliament_period import get_parliament_periods
        from abgeordnetenwatch_python.models.candidacy_mandate import get_candidacy_mandates

        politician_ids = set()

        parliament_periods = await get_parliament_periods(session, parliament_id=self.id, limit=1000)

        # skip election periods
        parliament_periods = [pp for pp in parliament_periods if pp.is_legislature()]

        for index, pp in enumerate(parliament_periods):
            if verbose:
                print('loading parliament period [{}/{}]: {}'.format(index+1, len(parliament_periods), pp.label),
                      end='', flush=True)
            candidacy_mandates = await get_candidacy_mandates(session, parliament_period_id=pp.id, limit=1000)
            if verbose:
                print(' (found {} politicians)'.format(len(candidacy_mandates)), flush=True)
            politician_ids.update(cm.politician_id for cm in candidacy_mandates)
        return sorted(politician_ids)

    def __repr__(self) -> str:
        return 'Parliament(id={}, label={})'.format(self.id, self.label)


async def get_parliaments(
        session: aiohttp.ClientSession, id: Optional[int] = None, label: Optional[str] = None
) -> List[Parliament]:
    """
    Calls the abgeordnetenwatch API to retrieve all parliaments matching the given parameters.

    :param session: aiohttp session to use for making the request.
    :param id: Identifier to use for filtering
    :param label: label to use for filtering
    :return: A (possibly empty) list of Parliaments.
    """
    params = {}
    if id is not None:
        params['id'] = id
    if label is not None:
        params['label'] = label

    url = 'https://www.abgeordnetenwatch.de/api/v2/parliaments'
    async with session.get(url, params=params, raise_for_status=True) as r:
        data = await r.json()
        return [Parliament.model_validate(par_data) for par_data in data['data']]


async def get_parliament(
        session: aiohttp.ClientSession, id: Optional[int] = None, label: Optional[str] = None
) -> Parliament:
    parliaments = await get_parliaments(session, id, label)
    assert len(parliaments), 'Expected 1 parliament, but found {}'.format(len(parliaments))
    return parliaments[0]
