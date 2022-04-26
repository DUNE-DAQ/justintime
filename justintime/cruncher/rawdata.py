# DUNE DAQ includes
import daqdataformats
import detdataformats.wib
import detchannelmaps
import hdf5libs
import logging

import re
import rich
import numpy as np
import pandas as pd

trig_rec_hdr_regex = re.compile(r"\/\/TriggerRecord(\d{5})\/TriggerRecordHeader")
ch_map = detchannelmaps.make_map('VDColdboxChannelMap')

# Get the list of trigger records
def get_trigger_record_list(file_path: str) -> list:
    dd = hdf5libs.HDF5RawDataFile(file_path)

    records = dd.get_all_record_ids()
    print(records)

    return [ rid[0] for rid in records ]


# Read a trigger record and build a pandas dataframe
def read_trigger_record(file_path: str, tr_num: int, ch_map: detchannelmaps.TPCChannelMap):
    dd = hdf5libs.HDF5RawDataFile(file_path)

    # TODO: replace with regex?
    frag_datasets = dd.get_fragment_dataset_paths(tr_num)
    trghdr_datasets = dd.get_trigger_record_header_dataset_path(tr_num)

    if len(trghdr_datasets) != 1:
        logging.warning(f"Multiple trigger record headers found {trghdr_datasets}")

    trghdr = dd.get_trh(trghdr_datasets[0])

    tr_info = {
        'run_number': trghdr.get_run_number(),
        'trigger_number': trghdr.get_trigger_number(),
        'trigger_timestamp': trghdr.get_trigger_timestamp(),
    }

    links = {}
    for d in frag_datasets:
        frag = dd.get_frag(d)
        frag_hdr = frag.get_header()

        logging.debug(f"Inspecting {d}")
        logging.debug(f"Run number : {frag.get_run_number()}")
        logging.debug(f"Trigger number : {frag.get_trigger_number()}")
        logging.debug(f"Trigger TS    : {frag.get_trigger_timestamp()}")
        logging.debug(f"Window begin  : {frag.get_window_begin()}")
        logging.debug(f"Window end    : {frag.get_window_end()}")
        logging.debug(f"Fragment type : {frag.get_fragment_type()}")
        logging.debug(f"Fragment code : {frag.get_fragment_type_code()}")
        logging.debug(f"Size          : {frag.get_size()}")

        n_frames = (frag.get_size()-frag_hdr.sizeof())//detdataformats.wib.WIBFrame.sizeof()
        if not n_frames:
            continue

        wf = detdataformats.wib.WIBFrame(frag.get_data())
        wh = wf.get_wib_header()

        logging.debug(f"crate: {wh.crate_no}, slot: {wh.slot_no}, fibre: {wh.fiber_no}")
        crate_no = wh.crate_no 
        slot_no = wh.slot_no
        fiber_no = wh.fiber_no

        ts = np.zeros(n_frames, dtype='uint64')
        adcs = np.zeros(n_frames, dtype=('uint16', 256))
        off_chans = [ch_map.get_offline_channel_from_crate_slot_fiber_chan(crate_no, slot_no, fiber_no, c) for c in range(256)]

        for i in range(n_frames):
        #     # progress.update(task2, advance=1)

            wf = detdataformats.wib.WIBFrame(frag.get_data(i*detdataformats.wib.WIBFrame.sizeof())) 
            ts[i] = wf.get_timestamp()
            adcs[i] = [wf.get_channel(c) for c in range(256)]
        logging.debug(f"Unpacking {d} completed")
        links[d] = (ts, adcs)

    return tr_info, links

if __name__ == '__main__':

    from rich.logging import RichHandler

    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    file_path = '/data0/np02_bde_coldbox_run011913_0011_20211028T161244.hdf5.copied'
    rich.print(file_path)

    tr_list = get_trigger_record_list(file_path)
    rich.print(tr_list)
    
    links = read_trigger_record(file_path, tr_list[0])
