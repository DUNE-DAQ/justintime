from .. import page_class

def return_obj():
    text="Baseline per Channel"
    page = page_class.page("PDS: Baseline per Channel", "18_pds_baseline_per_channel_page",text)
    page.add_plot("18_pds_baseline_per_channel_plot")
    return(page)