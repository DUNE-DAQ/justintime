from .. import page_class

def return_obj():
    text="Waveforms per Channel"
    page = page_class.page("PDS: Waveforms per Channel", "20_pds_waveforms_per_channel_page",text)
    page.add_plot("20_pds_waveforms_per_channel_plot")
    return(page)