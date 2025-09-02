from dash import html, dcc
from dash.dependencies import Input, Output, State

from .. import ctrl_class

def return_obj(dash_app, engine, storage):
    ctrl_id = "99_read_record_ctrl"

    ctrl_div = html.Div([
        html.Button(
            "Read" \
            " Record",
            id=ctrl_id,
            n_clicks = 0
        )
    ])

    ctrl = ctrl_class.ctrl("load_data", ctrl_id, ctrl_div, engine)

    return(ctrl)