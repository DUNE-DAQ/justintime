from dash import html, dcc
from dash.dependencies import Input, Output, State
import rich
from .. import ctrl_class
from ... data_cache import TriggerRecordData
import numpy as np
import pandas as pd

def return_obj(dash_app, engine, storage):
    ctrl_id = "16_channel_number_ctrl"
    
    ctrl_div =html.Div([
        html.Div([
        html.Label("Select a Channel Number : ",style={"fontSize":"12px"}), html.Div([dcc.Dropdown(placeholder="Channel",
        id="channel_number_ctrl",multi=True)],style={"marginBottom":"1em","marginTop":"1em"},)])],id=ctrl_id)
    
    ctrl = ctrl_class.ctrl("channel_num", ctrl_id, ctrl_div, engine)
    ctrl.add_ctrl("08_adc_map_selection_ctrl")
    ctrl.add_ctrl("06_file_select_ctrl")
    ctrl.add_ctrl("07_trigger_record_select_ctrl")
    ctrl.add_ctrl("23_apa_select_ctrl")
    
    init_callbacks(dash_app, engine, storage )
    return(ctrl)

def init_callbacks(dash_app, engine, storage):
    @dash_app.callback(
        Output('channel_number_ctrl', 'options'),
        Input('adc_map_selection_ctrl', 'value'),
        Input("trigger_record_select_ctrl", 'value'),
        Input('file_select_ctrl', 'value'),
        Input('apa_select_ctrl', 'value')
        )
    def update_select(plane, trigger_record, raw_data_file, apa):
        if not plane:
            return [""]

        if not trigger_record or not raw_data_file or not apa:
            return [""]
            
        try: 
            data = storage.get_trigger_record_data(trigger_record, raw_data_file)
        except RuntimeError:
            return [""]

        try:
            tpc_wvfm_keys = [ key for key in data.df_dict if key.startswith('detw') and 'TPC' in key ]
            df_all = []
            for key in tpc_wvfm_keys:
                df_tmp = data.df_dict[key].reset_index()
                df_tmp = df_tmp[["element","plane","channel"]]
                df_tmp = df_tmp.loc[df_tmp["element"]==int(apa[3])] #should be APAX or CRPX
                df_all.append(df_tmp)
            df_tmp = pd.concat(df_all,ignore_index=True)

            channel_num=np.array([])
            if "Z" in plane:
                plane_no = 2
                channel_num = np.append(channel_num,df_tmp.loc[df_tmp["plane"]==plane_no]["channel"])
            if "V" in plane:
                plane_no = 1
                channel_num = np.append(channel_num,df_tmp.loc[df_tmp["plane"]==plane_no]["channel"])
            if "U" in plane:
                plane_no = 0
                channel_num = np.append(channel_num,df_tmp.loc[df_tmp["plane"]==plane_no]["channel"])
            return(list(np.sort(np.unique(channel_num))))
        except RuntimeError : return([""])
        except TypeError: return([""])
        except KeyError: return([""])
