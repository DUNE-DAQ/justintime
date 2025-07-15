from dash import html, dcc
from dash.dependencies import Input, Output, State

from .. import ctrl_class

def return_obj(dash_app, engine, storage):
    ctrl_id = "22_tests_selection_ctrl"
    comp_id = "tests_selection_item_comp"

    ctrl_div = html.Div([
        dcc.Checklist(["WIB Pulser", "PDS"], ["WIB Pulser", "PDS"], id=comp_id, inline=True)
    ], id = ctrl_id)

    ctrl = ctrl_class.ctrl("tests_selection", ctrl_id, ctrl_div, engine)

    return(ctrl)