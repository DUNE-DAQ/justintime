from dash import html, dcc
from dash.dependencies import Input, Output, State

from .. import ctrl_class

def return_obj(dash_app, engine, storage):

    ctrl_id = "06_trigger_record_select_ctrl"

    ctrl_div = html.Div([
        
        html.Label("Select a Trigger Record: ",style={"fontSize":"12px"}),
        html.Div([
        dcc.Dropdown(placeholder="Trigger Record",
            id="trigger_record_select_ctrl"
        )
    ],style={"marginBottom":"1.5em"})],id=ctrl_id)

    ctrl = ctrl_class.ctrl("trigger_record_select", ctrl_id, ctrl_div, engine)
    ctrl.add_ctrl("05_file_select_ctrl")

    init_callbacks(dash_app, engine)
    return(ctrl)

def init_callbacks(dash_app, engine):

    @dash_app.callback(
        Output('trigger_record_select_ctrl', 'options'),
        Input('file_storage_id', 'data')
        )
    
    def update_trigger_record_select(raw_data_file):
        if not raw_data_file:
            return []
        tr_nums = [{'label':str(n), 'value':str(n)} for n in sorted(engine.get_trigger_record_list(raw_data_file), reverse=True)]
        return(tr_nums)
