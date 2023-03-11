#!/usr/bin/env python

from justintime.cruncher.datamanager import DataManager
import sys
import rich
import logging
import click
from rich import print
from pathlib import Path

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('channel_map_id', type=click.Choice(['VDColdbox', 'ProtoDUNESP1', 'PD2HD', 'VST']))
@click.argument('frame_type', type=click.Choice(['ProtoWIB', 'WIB']))
@click.option('-i', '--interactive', is_flag=True, default=False)
@click.argument('file_path', type=click.Path(exists=True))

def cli(channel_map_id: str, frame_type: str, interactive: bool, file_path: str) -> None:

    channel_map_id += 'ChannelMap'

    dp = Path(file_path)
    print(dp.parent)
    print(dp.name)


    # rdm = DataManager(dp.parent, 'ProtoWIB', 'VDColdbox')
    rdm = DataManager(dp.parent, frame_type, channel_map_id)
    # data_files = sorted(rdm.list_files(), reverse=True)
    # rich.print(data_files)
    f = dp.name
    rich.print(f)
    trl = rdm.get_entry_list(f)
    rich.print(trl)

    rich.print(f"Reading entry {trl[0]}")
    info, tpc_df, tp_df, fwtp_df = rdm.load_entry(f, trl[0])
    rich.print(info)
    rich.print(tpc_df)
    rich.print(tp_df)
    if interactive:
        import IPython
        IPython.embed(colors="neutral")



if __name__ == "__main__":
    from rich.logging import RichHandler

    logging.basicConfig(
        level="WARNING",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    cli()