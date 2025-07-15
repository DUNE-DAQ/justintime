from dash import html, dcc
from dash.dependencies import Input, Output, State

from .. import ctrl_class

def return_obj(dash_app, engine, storage):

    ctrl_id = "23_apa_select_ctrl"

    ctrl_div = html.Div([

        html.Label("Select a Detector Unit (APA/CRP): ",style={"fontSize":"12px"}),
        html.Div([
            dcc.Dropdown(placeholder="APA/CRP",
                         id="apa_select_ctrl"
                         )
        ],style={"marginBottom":"1.5em"})],id=ctrl_id)

    ctrl = ctrl_class.ctrl("apa_select", ctrl_id, ctrl_div, engine)
    ctrl.add_ctrl("05_file_select_ctrl")
    ctrl.add_ctrl("06_trigger_record_select_ctrl")

    init_callbacks(dash_app, engine)
    return(ctrl)

def init_callbacks(dash_app, engine):

    @dash_app.callback(
        Output('apa_select_ctrl', 'options'),
        Input('file_storage_id', 'data')
    )

    def update_apa_select(raw_data_file):
        if not raw_data_file:
            return []
        apa_names = [{'label':str(n), 'value':str(n)} for n in engine.get_tpc_element_names(raw_data_file)]
        return(apa_names)
