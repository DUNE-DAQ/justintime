from .. import page_class

def return_obj():
    text="Scatter and 2D-density plot of trigger primitives for each plane. The histograms count how many trigger primitives there are to understand the presence of a hot spot. They display the level of activity per channel."
    page = page_class.page("Trigger Primitive Display", "05_tp_display_page",text)
    page.add_plot("02_tp_display_plot")
    return(page)