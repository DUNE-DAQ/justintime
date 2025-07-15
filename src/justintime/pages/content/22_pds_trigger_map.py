from .. import page_class

def return_obj():
    text="Trigger Map"
    page = page_class.page("PDS: Trigger Map", "22_pds_trigger_map_page",text)
    page.add_plot("22_pds_trigger_map_plot")
    return(page)