from .. import page_class

def return_obj():
    text="Mean ADC values for the Photo-detetction system."
    page = page_class.page("PDS stats plots", "17_pds_stats_page",text)
    page.add_plot("17_pds_stats_plot")
    return(page)