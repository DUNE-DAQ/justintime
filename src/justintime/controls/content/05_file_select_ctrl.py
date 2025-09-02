from dash import html, dcc
from dash.dependencies import Input, Output, State
import rich

from .. import ctrl_class
from ... cruncher.datamanager import DataManager

def return_obj(dash_app, engine, storage):

    ctrl_id = "05_file_select_ctrl"

    ctrl_div = html.Div([
        html.Div([
        html.Label("Select a Data File: ",style={"fontSize":"12px"}),
        html.Div([
        
        dcc.Dropdown(placeholder="Data File",
            id="file_select_ctrl"
        ),
        dcc.Store("file_storage_id")
    ],style={"marginBottom":"1.0em"})])],id=ctrl_id)

    ctrl = ctrl_class.ctrl("file_select", ctrl_id, ctrl_div, engine)
    ctrl.add_ctrl("04_partition_run_select_ctrl")

    init_callbacks(dash_app, engine)
    return(ctrl)

def init_callbacks(dash_app, engine):

    @dash_app.callback(
        Output('file_select_ctrl', 'options'),
        Input('run_storage_id', 'data')
        )
    
    def update_select(stored_value):

        if not stored_value:
            return []
        options = [{'label':str(n), 'value':str(n)} for n in sorted(stored_value, reverse=True)]
        return(options)
        
    @dash_app.callback(
        Output('file_storage_id', 'data'),
        Input('file_select_ctrl', 'value'),
        State('run_storage_id', 'data')
        )
    
    def store_subset(selection, parent_stored_value):
        if not selection:
            return {}
        
        rich.print("Data File Selection:",selection)

        return(selection)