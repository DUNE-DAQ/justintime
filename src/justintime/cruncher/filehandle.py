"""
This is the version of the DataManager that adopts existing unpacking tools,
avaliable with rawdatautils (/unpack/utils.py and /unpack/dataclasses.py).
"""
import os.path
import fnmatch
from os import walk
import re
import logging

import numpy as np
import pandas as pd
import collections
from collections import defaultdict
from itertools import groupby

import hdf5libs
import h5py
import dqmtools.dataframe_creator as dfc
import detchannelmaps
    

class FileHandle:

    match_exprs = ['*.hdf5', '*.hdf5.copied']
    max_cache_size = 10
    
    @staticmethod
    def get_det_name(channel_map_name):
        if channel_map_name == 'PD2HD':
            return 'HD_TPC'
        if channel_map_name == 'PD2VDTPC':
            return 'VD_BottomTPC'
        else:
            return channel_map_name

    def __init__(self, data_path: str,
                 tpc_channel_map_name: str,
                 pds_channel_map_name: str) -> None:

        if not os.path.isdir(data_path):
            raise ValueError(f"Directory {data_path} does not exist")

        self.data_path       = data_path
        self.tpc_ch_map_name = tpc_channel_map_name+"ChannelMap"
        self.pds_ch_map_name = pds_channel_map_name+"ChannelMap"
        try:
            self.tpc_ch_map      = detchannelmaps.make_tpc_map(self.tpc_ch_map_name)
        except:
            raise ValueError(f"Failed to create {self.tpc_channel_map_name}")
        try:
            self.pds_ch_map      = detchannelmaps.make_pds_map(self.pds_ch_map_name)
        except:
            raise ValueError(f"Failed to create {self.pds_channel_map_name}")

        self.det_name        = self.get_det_name(tpc_channel_map_name)

        self.cache = collections.OrderedDict()

    def list_files(self) -> list:
        files = []
        for m in self.match_exprs:
            files += fnmatch.filter(next(walk(self.data_path), (None, None, []))[2], m)  # [] if no file

        return sorted(files, reverse=True, key=lambda f: os.path.getmtime(os.path.join(self.data_path, f)))
    
    def get_session_run_files_map(self) -> defaultdict:
        re_app_run = re.compile(r'(.*)_run(\d*)')

        # List files
        lf = sorted(self.list_files())

        def extract_session_run( fname : str ):
            m = re_app_run.match(fname)
            if not m:
                return ('none', '0')
            else:
                return m.groups()

        # Group by regex
        gf_it = groupby(lf, extract_session_run)
        gf = {k: [x for x in d if x] for k,d in gf_it}
        srf_map = defaultdict(dict)

        # Populate the map
        for k,v in gf.items():
            srf_map[k[0]][int(k[1])]=v

        return srf_map

    def has_trigger_records(self, file_name: str) -> list:
        file_path = os.path.join(self.data_path, file_name)
        rdf = hdf5libs.HDF5RawDataFile(file_path) # number of events = 10000 is not used
        try:
            _ = rdf.get_all_trigger_record_ids()
            return True
        except RuntimeError:
            return False

    def has_timeslices(self, file_name: str) -> list:
        file_path = os.path.join(self.data_path, file_name)
        rdf = hdf5libs.HDF5RawDataFile(file_path) # number of events = 10000 is not used
        try:
            return [ n for n,_ in rdf.get_all_timeslice_ids()]
        except RuntimeError:
            return []

    def get_trigger_record_list(self, file_name: str) -> list:
        file_path = os.path.join(self.data_path, file_name)
        rdf = hdf5libs.HDF5RawDataFile(file_path) # number of events = 10000 is not used
        try:
            return [ n for n,_ in rdf.get_all_trigger_record_ids()]
        except RuntimeError:
            return []

    def get_timeslice_list(self, file_name: str) -> list:
        file_path = os.path.join(self.data_path, file_name)
        rdf = hdf5libs.HDF5RawDataFile(file_path) # number of events = 10000 is not used
        try:
            return [ n for n,_ in rdf.get_all_timeslice_ids()]
        except RuntimeError:
            return []


    def get_entry_list(self, file_name: str) -> list:
        trl = self.get_trigger_record_list(file_name)
        tsl = self.get_timeslice_list(file_name)

        return trl if trl else tsl

    def get_tpc_element_names(self, file_name: str) -> list:
        file_path = os.path.join(self.data_path, file_name)
        op_env = None
        with h5py.File(file_path, 'r') as f:
            op_env = f.attrs["operational_environment"]
        if op_env is None:
            return [""]
        if op_env=="np04hd":
            return ["APA1","APA2","APA3","APA4"]
        if op_env=="np02vd":
            return ["CRP2","CRP3","CRP4","CRP5"]
        if op_env=="np02vdcoldbox":
            return ["CRPX"]
        if op_env=="iceberghd" or op_env=="iceberg" or "icebergvd":
            return ["TPC-0-N","TPC-0-S"]
        return [""]

    def load_entry(self, file_name: str, entry: int):
        uid = (file_name, entry)

        if uid in self.cache:
            logging.info(f"{file_name}:{entry} already loaded. returning cached dataframe")    
            df_dict = self.cache[uid]
            self.cache.move_to_end(uid, False)

            return df_dict
        
        file_path = os.path.join(self.data_path, file_name)
        h5_file   = hdf5libs.HDF5RawDataFile(file_path)
        

        df_dict = {}
        df_dict = dfc.process_record(h5_file,(entry, 0),df_dict,MAX_WORKERS=10,ana_data_prescale=1,wvfm_data_prescale=1)
        df_dict = dfc.concatenate_dataframes(df_dict)

        self.cache[uid] = df_dict

        if len(self.cache) > self.max_cache_size:
            old_uid, _ = self.cache.popitem(False)
            logging.info(f"Removing {old_uid[0]}:{old_uid[1]} from cache")

        return df_dict
