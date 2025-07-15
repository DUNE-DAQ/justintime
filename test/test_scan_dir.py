#!/usr/bin/env python

from justintime.cruncher.datamanager import DataManager
import sys
import rich
import logging
import click
import re
from rich import print
from pathlib import Path
from itertools import groupby
from collections import defaultdict

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--interactive', is_flag=True, default=False)
@click.argument('dir_path', type=click.Path(exists=True))

def cli(interactive: bool, dir_path: str) -> None:

    rdm = DataManager(dir_path, 'PD2HD')

    # re_app_run = re.compile(r'(.*)_run(\d*)')

    # lf = rdm.list_files()
    # gf_it = groupby(lf, lambda x: re_app_run.match(x).groups())
    # gf = {k: [x for x in d if x] for k,d in gf_it}
    # a = defaultdict(dict)

    # for k,v in gf.items():
    #     a[k[0]][int(k[1])]=v

    a = rdm.get_session_run_files_map()
    print(a)

    if interactive:
        import IPython
        IPython.embed(colors="neutral")



if __name__ == "__main__":
    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    cli()
