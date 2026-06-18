# import pathlib
import collections
import fddetdataformats
import trgdataformats
import daqdataformats
import detchannelmaps

import logging

import pandas as pd
import numpy as np

import rawdatautils.unpack.wibeth as wibeth_unpack

from rich import print


class FragmentUnpacker:

    def __init__(self):
        pass

    def match(self, frag_type, subsys):
        return None
    
    def unpack(self, frag):
        return {}


class WIBEthFragmentNumpyUnpacker(FragmentUnpacker):
    
    def __init__(self):
        super().__init__()
    
    def match(self, frag_type, subsys):
        return (frag_type == daqdataformats.FragmentType.kWIBEth) and (subsys == daqdataformats.SourceID.kDetectorReadout)
    
    def unpack(self, frag):
        frag_hdr = frag.get_header()

        if not frag.get_data_size():
            return None, None
        
        if True:
            wf = fddetdataformats.WIBEthFrame(frag.get_data())
            dh = wf.get_daqheader()
            wh = wf.get_wibheader()
            ts, det_id, crate_no, slot_no, stream_no = (dh.timestamp, dh.det_id, dh.crate_id, dh.slot_id, dh.stream_id)

            logging.info(f"ts: 0x{ts:016x} (15 lsb: 0x{ts&0x7fff:04x}) cd_ts_0: 0x{wh.colddata_timestamp_0:04x} cd_ts_1: 0x{wh.colddata_timestamp_1:04x} crate: {crate_no}, slot: {slot_no}, stream: {stream_no}")

        ts = wibeth_unpack.np_array_timestamp(frag)
        adcs = wibeth_unpack.np_array_adc(frag)

        return ts, adcs
    
    
class WIBEthFragmentPandasUnpacker(WIBEthFragmentNumpyUnpacker):

    def __init__(self, channel_map):
        super().__init__()
        # self.chan_map = detchannelmaps.make_map(f'{channel_map}ChannelMap') if not channel_map is None else None
        if isinstance(channel_map, str):
            self.chan_map = detchannelmaps.make_map(f'{channel_map}ChannelMap') if not channel_map is None else None
        else:
            self.chan_map = channel_map

    def unpack(self, frag):

        payload_size = frag.get_data_size()
        # print(f"fragment payload size {payload_size}")
        if not payload_size:
            return None
        
        wf = fddetdataformats.WIBEthFrame(frag.get_data())
        dh = wf.get_daqheader()
        wh = wf.get_wibheader()
        ts, det_id, crate_no, slot_no, stream_no = (dh.timestamp, dh.det_id, dh.crate_id, dh.slot_id, dh.stream_id)
        n_chan_per_stream = 64
        n_streams_per_link = 4

        logging.info(f"ts: 0x{ts:016x} (15 lsb: 0x{ts&0x7fff:04x}) cd_ts_0: 0x{wh.colddata_timestamp_0:04x} cd_ts_1: 0x{wh.colddata_timestamp_1:04x} crate: {crate_no}, slot: {slot_no}, stream: {stream_no}")

        # link_no = stream_no >> 6;
        # substream_no = stream_no & 0x3f;

        # first_chan = n_chan_per_stream*substream_no
        if self.chan_map:
            # off_chans = [self.chan_map.get_offline_channel_from_crate_slot_fiber_chan(crate_no, slot_no, link_no, c) for c in range(first_chan,first_chan+n_chan_per_stream)]
            off_chans = [self.chan_map.get_offline_channel_from_crate_slot_stream_chan(crate_no, slot_no, stream_no, c) for c in range(n_chan_per_stream)]
        else:
            first_chan += link_no*n_chan_per_stream*n_streams_per_link
            off_chans = [c for c in range(first_chan,first_chan+n_chan_per_stream)]

        ts, adcs = super().unpack(frag)

        if ts is None or adcs is None:
            return None

        df = pd.DataFrame(collections.OrderedDict([('ts', ts)]+[(off_chans[c], adcs[:,c]) for c in range(64)]))
        df = df.set_index('ts')

        return df

# class WIBEthFragmentUnpacker(FragmentUnpacker):
    
#     def __init__(self, channel_map):
#         super().__init__()
#         self.chan_map = detchannelmaps.make_map(f'{channel_map}ChannelMap') if not channel_map is None else None
#         # self.dump = True
    
#     def match(self, frag_type, subsys):
#         return (frag_type == daqdataformats.FragmentType.kWIBEth) and (subsys == daqdataformats.SourceID.kDetectorReadout)
    
#     def unpack(self, frag):

#         payload_size = frag.get_data_size()
#         print(f"fragment payload size {payload_size}")
#         if not payload_size:
#             return None
        
#         wf = fddetdataformats.WIBEthFrame(frag.get_data())
#         dh = wf.get_daqheader()
#         wh = wf.get_wibheader()
#         ts, det_id, crate_no, slot_no, stream_no = (dh.timestamp, dh.det_id, dh.crate_id, dh.slot_id, dh.stream_id)
#         n_chan_per_stream = 64
#         n_streams_per_link = 4

#         logging.info(f"ts: 0x{ts:016x} (15 lsb: 0x{ts&0x7fff:04x}) cd_ts_0: 0x{wh.colddata_timestamp_0:04x} cd_ts_1: 0x{wh.colddata_timestamp_1:04x} crate: {crate_no}, slot: {slot_no}, stream: {stream_no}")

#         off_chans = [self.chan_map.get_offline_channel_from_crate_slot_stream_chan(crate_no, slot_no, stream_no, c) for c in range(n_chan_per_stream)]

#         ts = wibeth_unpack.np_array_timestamp(frag)
#         adcs = wibeth_unpack.np_array_adc(frag)

#         df = pd.DataFrame(collections.OrderedDict([('ts', ts)]+[(off_chans[c], adcs[:,c]) for c in range(n_chan_per_stream)]))
#         df = df.set_index('ts')

#         return df



class TPFragmentPandasUnpacker(FragmentUnpacker):

    def __init__(self, channel_map):
        super().__init__()
        if isinstance(channel_map, str):
            self.chan_map = detchannelmaps.make_map(f'{channel_map}ChannelMap') if not channel_map is None else None
        else:
            self.chan_map = channel_map
    
    def match(self, frag_type, subsys):
        return (frag_type == daqdataformats.FragmentType.kTriggerPrimitive) and (subsys == daqdataformats.SourceID.kTrigger)
    
    @classmethod
    def dtypes(cls):
        return [
                ('time_start', np.uint64), 
                ('time_peak', np.uint64), 
                ('time_over_threshold', np.uint64), 
                ('channel',np.uint32),
                ('adc_integral', np.uint32), 
                ('adc_peak', np.uint16), 
                ('flag', np.uint16),
                ('plane', np.uint8),
            ]
    
    @classmethod
    def empty(cls):
        return pd.DataFrame(np.empty(0, cls.dtypes()))

    def unpack(self, frag):

        tp_array = []
        tp_size = trgdataformats.TriggerPrimitive.sizeof()

        frag_hdr = frag.get_header()

        n_frames = (frag.get_size()-frag_hdr.sizeof())//tp_size
        logging.debug(f"Number of TP frames: {n_frames}")
        
        # Initialize the TP array buffer
        tp_array = np.zeros(
            n_frames, 
            dtype=self.dtypes()
        )

        
        # Populate the buffer
        for i in range(n_frames):
            tp = trgdataformats.TriggerPrimitive(frag.get_data(i*tp_size))
            tp_array[i] = (
                tp.time_start,
                tp.time_peak,
                tp.time_over_threshold,
                tp.channel,
                tp.adc_integral,
                tp.adc_peak,
                tp.flag,
                9999 # placeholder, not set
            )

        # Create the dataframe
        df = pd.DataFrame(tp_array)

        logging.debug(f"TP Dataframe size {len(df)}")
        # print(df)
        # Add plane information (here or in user code?)
        df['plane'] = df['channel'].apply(lambda x: self.chan_map.get_plane_from_offline_channel(x)).astype(np.uint8)
        return df


class TAFragmentPandasUnpacker(FragmentUnpacker):

    def __init__(self, channel_map):
        super().__init__()
        if isinstance(channel_map, str):
            self.chan_map = detchannelmaps.make_map(f'{channel_map}ChannelMap') if not channel_map is None else None
        else:
            self.chan_map = channel_map
    
    def match(self, frag_type, subsys):
        return (frag_type == daqdataformats.FragmentType.kTriggerActivity) and (subsys == daqdataformats.SourceID.kTrigger)
    
    @classmethod
    def dtypes(cls):
        return [
            ('time_start', np.uint64), 
            ('time_end', np.uint64), 
            ('time_peak', np.uint64), 
            ('time_activity', np.uint64), 
            ('channel_start', np.uint32), 
            ('channel_end', np.uint32), 
            ('channel_peak', np.uint32), 
            ('adc_integral', np.uint32), 
            ('adc_peak', np.uint16),
            ('plane', np.uint8),
        ]

    @classmethod
    def empty(cls):
        return pd.DataFrame(np.empty(0, cls.dtypes()))


    def test_wrapper(self, frag, offset):
        offset=0

        b = frag.get_data_bytes(offset)
        ta = trgdataformats.TriggerActivity(b)

        import rich
        rich.print('>'*80)
        rich.print(len(ta))
        rich.print(f"""
time [
    start={ta.data.time_start},
    end={ta.data.time_end},
    peak={ta.data.time_peak},
    act={ta.data.time_activity}], 
chan: [
    start={ta.data.channel_start},
    end={ta.data.channel_end},
    peak={ta.data.channel_peak}] ,
adc: [
    int={ta.data.adc_integral},
    peak={ta.data.adc_peak}
]"""
        )
        
        for i in range(len(ta)):
            rich.print(ta[i].time_start, ta[i].time_peak, ta[i].time_over_threshold)

        rich.print('<'*80)
        

    def unpack(self, frag):

        # self.test_wrapper(frag)
        data_size = frag.get_data_size()

        offset=0
        offsets = []
        n_entries = 0

        while(offset < data_size):
            offsets.append(offset)

            ta_o = trgdataformats.TriggerActivityOverlay(frag.get_data(offset))

            n_entries += 1
            offset += ta_o.sizeof()

        # Initialize the TA array buffer
        ta_array = np.zeros(
            n_entries, 
            dtype=self.dtypes()
        )

        offset=0
        for i, offset in enumerate(offsets):
            ta_o = trgdataformats.TriggerActivityOverlay(frag.get_data(offset))

            ta_array[i] = (
                ta_o.data.time_start,
                ta_o.data.time_end,
                ta_o.data.time_peak,
                ta_o.data.time_activity,
                ta_o.data.channel_start,
                ta_o.data.channel_end,
                ta_o.data.channel_peak,
                ta_o.data.adc_integral,
                ta_o.data.adc_peak,
                9999 # placeholder, not set
            )

            # self.test_wrapper(frag, offset)


        # Create the dataframe
        df = pd.DataFrame(ta_array)
        # logging.debug(f"TA Dataframe size {len(df)}")
        # print(df)
        # Add plane information (here or in user code?)
        df['plane'] = df['channel_peak'].apply(lambda x: self.chan_map.get_plane_from_offline_channel(x)).astype(np.uint8)
        return df


class TCFragmentPandasUnpacker(FragmentUnpacker):

    def __init__(self):
        super().__init__()

    def match(self, frag_type, subsys):
        return (frag_type == daqdataformats.FragmentType.kTriggerCandidate) and (subsys == daqdataformats.SourceID.kTrigger)

    @classmethod
    def dtypes(cls):
        return [
                ('time_start', np.uint64), 
                ('time_end', np.uint64), 
                ('time_candidate', np.uint64), 
            ]

    @classmethod
    def empty(cls):
        return pd.DataFrame(np.empty(0, cls.dtypes()))

    def unpack(self, frag):

        data_size = frag.get_data_size()

        offset=0
        offsets = []
        n_entries = 0

        while(offset < data_size):
            offsets.append(offset)

            tc = trgdataformats.TriggerCandidateOverlay(frag.get_data(offset))

            n_entries += 1
            offset += tc.sizeof()


        # Initialize the TA array buffer
        tc_array = np.zeros(
            n_entries, 
            self.dtypes()
        )

        offset=0
        for i, offset in enumerate(offsets):
            ta = trgdataformats.TriggerCandidateOverlay(frag.get_data(offset))

            tc_array[i] = (
                ta.data.time_start,
                ta.data.time_end,
                ta.data.time_candidate,
            )


        # Create the dataframe
        df = pd.DataFrame(tc_array)
        logging.debug(f"TC Dataframe size {len(df)}")
        return df
    
class DAPHNEStreamFragmentPandasUnpacker(FragmentUnpacker):
    
    def __init__(self):
        super().__init__()
    
    def match(self, frag_type, subsys):
        return (frag_type == daqdataformats.FragmentType.kDAPHNE) and (subsys == daqdataformats.SourceID.kDetectorReadout)
    
    def unpack(self, frag):
        frag_hdr = frag.get_header()

        payload_size = (frag.get_size()-frag_hdr.sizeof())
        if not payload_size:
            return None
        
        print(f"DAPHNE payload size {payload_size}")
        
        df = fddetdataformats.DAPHNEStreamFrame(frag.get_data())

        dh = df.get_daqheader()

        ts, det_id, crate_no, slot_no, stream_no = (dh.get_timestamp(), dh.det_id, dh.crate_id, dh.slot_id, dh.link_id)
        print(ts, det_id, crate_no, slot_no, stream_no)


        df = pd.DataFrame()
        return df



class UnpackerService:
    """Helper class to unpack Trigger Records"""
    
    def __init__(self):
        self.fragment_unpackers = {}


    def add_unpacker(self, name, unpacker):

        if name in self.fragment_unpackers:
            raise KeyError(f"UnpackerService {name} already registered")

        self.fragment_unpackers[name] = unpacker

    def get_unpacker(self, name):
        return self.fragment_unpackers[name]
        

    def unpack(self, raw_data_file, tr_id: int, seq_id: int=0) -> dict:

        res = {}

        trh = raw_data_file.get_trh((tr_id, seq_id))
        tr_source_ids = raw_data_file.get_source_ids((tr_id, seq_id))

        for sid in tr_source_ids:
            frag = raw_data_file.get_frag((tr_id, seq_id),sid)

            for n,up in self.fragment_unpackers.items():
                if not up.match(frag.get_fragment_type(), sid.subsystem):
                    # logging.debug(f"fragment {sid} (type {frag.get_fragment_type()}) and unpacker {n} - no match")
                    continue
                
                logging.debug(f"[{n}] Unpacking Subsys={sid.subsystem}, id={sid.id}")                
                r = up.unpack(frag)
                logging.debug(f"[{n}] Unpacking Subsys={sid.subsystem}, id={sid.id} completed ({len(r) if r is not None else 0})")
                res.setdefault(n,{})[sid.id] = r

        return res
