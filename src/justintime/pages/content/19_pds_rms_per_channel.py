from .. import page_class

def return_obj():
    text="RMS per Channel"
    page = page_class.page("PDS: RMS per Channel", "19_pds_rms_per_channel_page",text)
    page.add_plot("19_pds_rms_per_channel_plot")
    return(page)