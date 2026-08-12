from dash import html, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
from ... plotting_functions import selection_line, nothing_to_plot
from .. import plot_class
import logging

import dqmtools.dataframe_creator as dfc
from dqmtools.dqmpds import df_channel_map, waveforms_plot

def return_obj(dash_app, engine, storage,theme):
    plot_id = "20_pds_waveforms_per_channel_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("Mean_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("90_plot_button_ctrl")

    init_callbacks(dash_app, storage, plot_id,theme)
    return(plot)

def init_callbacks(dash_app, storage, plot_id,theme):
    
    @dash_app.callback(
        Output(plot_id, "children"),
        Input("90_plot_button_ctrl", "n_clicks"),
        State('07_refresh_ctrl', "value"),
        State('trigger_record_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State('file_select_ctrl', "value"),
        #State("21_tp_multiplicity_ctrl","value"),
        State(plot_id, "children")
    )

    def plot_pds_baseline_per_channel_grap(n_clicks,refresh, trigger_record,partition,run,raw_data_file,original_state):

        if trigger_record and raw_data_file:

            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))
                    
                logging.info(f"Trigger Time Stamp: {data.get_trigger_ts()}")
                logging.info(" ")
                logging.info("Initial Dataframe:")
                logging.info(data.df_dict)  

                pds_keys = [k for k in data.df_dict if k.startswith("detw_k") and "PDS" in k]
                if not pds_keys:
                    return(html.Div(html.H6(nothing_to_plot())))

                df_list = []
                for k in pds_keys:
                    df_tmp, index = dfc.select_record(data.df_dict[k])
                    df_list.append(df_tmp.reset_index().filter(items=['src_id', 'channel', 'adcs']))

                df = pd.concat(df_list, axis=0)
                logging.info(df)
                df.columns = ['src_id', 'channel', 'waveforms']
                df = df_channel_map(df)
                
                try: fig_wf_channel = waveforms_plot(df)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))
                    
                return(html.Div([selection_line(partition,run,raw_data_file, trigger_record),html.H4("PDS: Waveforms per Channel"),dcc.Graph(figure=fig_wf_channel,style={"marginTop":"10px"})]))
            
           # else:
           #     return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
