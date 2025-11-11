#!/usr/bin/env python

import rich
import detchannelmaps

m = detchannelmaps.make_map('VDColdboxChannelMap')

def is_cruA_Z(off_chans):
    return any([ (1904  <= o <= 2487) for o in off_chans])

def is_cruB_Z(off_chans):
    return any([ (2488  <= o <= 3071) for o in off_chans])

for crate_no in range(6,7):
    for slot_no in range(0,6):
        for fiber_no in range(0,2):
            for block_no in range(0,2):
                # First half
                off_chans = [ m.get_offline_channel_from_crate_slot_fiber_chan(crate_no, slot_no, fiber_no, ch) for ch in range(128*block_no,128*(block_no+1))]
                is_A = is_cruA_Z(off_chans)
                is_B = is_cruB_Z(off_chans)
                rich.print(f" crate {crate_no}, slot {slot_no}, fibre {fiber_no}, block {block_no}: A={is_A}, B={is_B}")

# is_cru_aU = any([ ((0 <= o <= 475) or  (952  <= o <= 1427) or (1904  <= o <= 2487)) for o in off_chans])
# is_cru_aU = any([ (0 <= o <= 475) for o in off_chans])
# is_cru_aV = any([ (952  <= o <= 1427) for o in off_chans])
# is_cru_aZ = any([ (1904  <= o <= 2487) for o in off_chans])
# is_cru_b= any([ ((476 <= o <= 951) or  (1428  <= o <= 1903) or (2488  <= o <= 3071)) for o in off_chans])



