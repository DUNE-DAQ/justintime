from dash import html, dcc
from dash.dependencies import Input, Output, State

from .. import ctrl_class

def return_obj(dash_app, engine, storage):
    ctrl_id = "91_run_tests_button_ctrl"

    ctrl_div = html.Div([
        html.Button(
            "Run tests",
            id=ctrl_id,
            n_clicks = 0
        )
    ])

    ctrl = ctrl_class.ctrl("run_tests_button", ctrl_id, ctrl_div, engine)

    return(ctrl)