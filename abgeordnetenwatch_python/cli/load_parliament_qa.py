import argparse
import asyncio
from pathlib import Path
from typing import Optional

import aiohttp
from tqdm import tqdm

from abgeordnetenwatch_python.models.parliament import get_parliament
from abgeordnetenwatch_python.models.politicians import get_politician, get_default_filename
from abgeordnetenwatch_python.models.politician_dossier import load_politician_dossier_with_cache_file


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download questions/answers from politicians from abgeordnetenwatch.de and export to csv, txt or '
                    'json.'
    )
    parser.add_argument(
        'parliament', type=str,
        help='Name of the parlament to download'
    )

    parser.add_argument(
        '--sort-by', type=str, default='question', choices=['answer', 'question'],
        help='Sort by date of question or answer. Can be one of the following: answer question. Defaults to answer.'
    )
    parser.add_argument('--threads', '-t', type=int, default=1, help='Number of threads to use for downloading.')

    parser.add_argument(
        '--outdir', '-o', type=Path, default=Path('data') / 'json', help='The directory to save the file to.'
    )
    parser.add_argument('--quiet', '-q', action='store_true', help='Do not show progress.')

    return parser.parse_args()


async def async_main():
    args = parse_args()

    verbose = not args.quiet

    outdir: Path = args.outdir / args.parliament.lower()
    outdir.mkdir(exist_ok=True, parents=True)

    timeout = aiohttp.ClientTimeout(total=60 * 60 * 24 * 2)  # run 2 days max
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=args.threads), timeout=timeout) as session:
        # load parliament
        if verbose:
            print('loading politicians to scan:')
        parliament = await get_parliament(session, label=args.parliament)
        politician_ids = await parliament.get_politician_ids(session, verbose=verbose)
        if verbose:
            print('found {} politicians'.format(len(politician_ids)))

        # load politicians
        queue = asyncio.Queue()
        overall_progress = None
        if verbose:
            overall_progress = tqdm(desc='Progress', total=len(politician_ids))

        for p_id in politician_ids:
            await queue.put(p_id)

        workers = [
            asyncio.create_task(worker(session, queue, overall_progress, outdir, args.sort_by, verbose, args.threads))
            for _ in range(args.threads)
        ]

        await queue.join()
        for w in workers:
            w.cancel()
        worker_errors = await asyncio.gather(*workers, return_exceptions=True)

        if overall_progress is not None:
            overall_progress.close()

        errors = [e for worker_error in worker_errors for e in worker_error]

        print(f'{len(errors)} errors occurred during loading')
        for e in errors:
            print(e)


async def worker(
        session: aiohttp.ClientSession, queue: asyncio.Queue, overall_progress: Optional[tqdm], outdir: Path,
        sort_by: str, verbose: bool = False, threads: int = 1
) -> list:
    errors = []
    while True:
        try:
            politician_id = await queue.get()
        except asyncio.CancelledError:
            break

        try:
            tqdm_obj = None
            if verbose:
                tqdm_obj = tqdm(desc=f"preparing {politician_id}", bar_format='{desc}', leave=None)
                tqdm_obj.refresh()
            politician = await get_politician(session, id=politician_id)
            if verbose:
                tqdm_obj.close()

            filename = get_default_filename(politician, outdir)
            tqdm_args = {
                'leave': False, 'colour': '#777777'
            }
            await load_politician_dossier_with_cache_file(
                politician, filename, session=session, threads=threads, url_threads=1, verbose=verbose, sort_by=sort_by,
                tqdm_args=tqdm_args
            )

            if overall_progress is not None:
                overall_progress.update(1)

            queue.task_done()
        except Exception as e:
            print('failed to load politician {}'.format(politician_id))
            print(e)
            errors.append(e)
    return errors


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
