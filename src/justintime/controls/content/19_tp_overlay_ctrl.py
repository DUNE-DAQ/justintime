from dash import html, dcc
from dash.dependencies import Input, Output, State

from .. import ctrl_class

def return_obj(dash_app, engine, storage):
    ctrl_id = "19_tp_overlay_ctrl"

    ctrl_div = html.Div(
        [dcc.Checklist(
            options=[
                {"label":"TP Overlay","value":"tp_overlay"},
                {"label":"TA Overlay","value":"ta_overlay"}
            ], 
            value = ["tp_overlay"],
            id=ctrl_id)],
            style={
                "marginBottom":"0.2em",
                "fontSize": "1.5rem"
            }
        )

    ctrl = ctrl_class.ctrl("tp", ctrl_id, ctrl_div, engine)

    return(ctrl)