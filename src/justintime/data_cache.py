from itertools import groupby
import datetime
import rich
import numpy as np
import logging
import collections
from .cruncher import signal

from rawdatautils.unpack.dataclasses import dts_to_datetime

class TriggerRecordCache:
    
    max_cache_size = 10
    
    def __init__(self, engine):
        self.engine = engine
        self.raw_data_files = {}
        self.tr_age = []
        self.shown_plots = []

    def update_shown_plots(self, new_shown_plots):
        self.shown_plots = new_shown_plots

    def get_trigger_record_data(self, trigger_record, raw_data_file):
        logging.debug(f"Getting {raw_data_file} {trigger_record}")
        try:
            tr = self.raw_data_files[raw_data_file][trigger_record]
            # Mark tr as fresh
            i = self.tr_age.index( (raw_data_file, trigger_record) )
            self.tr_age.insert(0, self.tr_age.pop(i))
            logging.debug(f"\tAlready found in cache. Returning.")
            return tr
        except KeyError:
            logging.debug(f"\tKeyError --> not found in cache. Will add.")
            pass

        return self.add_trigger_record_to_file(trigger_record, raw_data_file)
            

    def add_trigger_record_to_file(self, trigger_record, raw_data_file):
        logging.debug(f"Adding {raw_data_file} {trigger_record}")

        self.raw_data_files.setdefault(raw_data_file,{})[trigger_record] = TriggerRecordData(self.engine, trigger_record, raw_data_file)

        self.tr_age.insert(0, (raw_data_file, trigger_record) )
        # Clear the cache if needed
        logging.debug(f"Current cache size = {len(self.tr_age)}, watermark = {self.max_cache_size}")
        if len(self.tr_age) > self.max_cache_size:
            old_rdf, old_tr = self.tr_age.pop()
            logging.debug(f"Clearing cache {old_rdf}, {old_tr}")

            del self.raw_data_files[old_rdf][old_tr]
            if len(self.raw_data_files[old_rdf]) == 0:
                del self.raw_data_files[old_rdf]

        l = 0
        for f in self.raw_data_files.values():
            l += len(f)
        logging.debug(f"Current Cache size: {l}")
        return self.raw_data_files[raw_data_file][trigger_record]



class TriggerRecordData:
    
    def __init__(self, engine, trigger_record, raw_data_file):
        logging.debug(f"__init__ TriggerRecordData {raw_data_file} {trigger_record}")
        self.engine     = engine
        self.df_dict    = engine.load_entry(raw_data_file, int(trigger_record))
        self.keys       = self.df_dict.keys()

        logging.debug(f"Found df_dict keys {self.keys}")

        indexies = np.array(self.df_dict["trh"].index[0]).astype(int)
        self.run        = indexies[0]
        self.trigger    = indexies[1]
        self.seq        = indexies[2]

        self.tpc_datkey     = f"detd_k{self.engine.det_name}_kWIBEth"
        # FIXME: Hardocded HD formats!
        self.pds_datkey     = f"detd_kVD_MembranePDS_kDAPHNE"
        self.pdss_datkey    = f"detd_kVD_CathodePDS_kDAPHNEStream"
        

        logging.info(f"Trigger timestamp (ticks): {self.get_trigger_ts()}")
        logging.info(f"Trigger timestamp (sec from epoc): {dts_to_datetime(self.get_trigger_ts()).strftime('%b-%d-%Y, %H:%M:%S')}")

    def get_trigger_ts(self):
        return self.df_dict['trh'].trigger_timestamp_dts.iloc[0]

    def get_trigger_ts_string(self):
        return dts_to_datetime(self.get_trigger_ts()).strftime('%b-%d-%Y, %H:%M:%S')

    def get_df(self, data_key):
        return self.df_dict[data_key]

    def get_adcs_per_planes(self, key=None):
        """
        TPC planes map:     
            0   : U;
            1   : V;
            2   : Z.
        """
        if key is None:
            return (self.df_dict[self.tpc_datkey].query("plane == 0"),
                    self.df_dict[self.tpc_datkey].query("plane == 1"),
                    self.df_dict[self.tpc_datkey].query("plane == 2"))
        else:
            return (self.df_dict[self.tpc_datkey].query("plane == 0")[key],
                    self.df_dict[self.tpc_datkey].query("plane == 1")[key],
                    self.df_dict[self.tpc_datkey].query("plane == 2")[key])
        
    def get_pds_adcs_per_link(self, key=None):

        print(self.df_dict.keys())
        print(f"{self.pdss_datkey} in dataframes", self.pdss_datkey in self.df_dict)
        print(self.df_dict[self.pdss_datkey])
        
        if key is None:
            return (self.df_dict[self.pdss_datkey],
                    self.df_dict[self.pdss_datkey],
                    self.df_dict[self.pdss_datkey])
        else:
            # return (self.df_dict[self.pdss_datkey].query("src_id < 4")[key],
            #         self.df_dict[self.pdss_datkey].query("src_id in [4, 5, 6, 8]")[key],
            #         self.df_dict[self.pdss_datkey].query("src_id in [7, 9]")[key])
            return (self.df_dict[self.pdss_datkey][key],
                    self.df_dict[self.pdss_datkey][key],
                    self.df_dict[self.pdss_datkey][key])