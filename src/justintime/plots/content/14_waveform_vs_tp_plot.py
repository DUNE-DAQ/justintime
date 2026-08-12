from dash import html, dcc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import rich
import pandas as pd
import logging
from .. import plot_class
from ... plotting_functions import add_dunedaq_annotation, selection_line,waveform_tps,nothing_to_plot

from dqmtools.dqmplots import *

def return_obj(dash_app, engine, storage,theme):
    plot_id = "14_waveform_vs_tp_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("waveform_tp_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("08_adc_map_selection_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("16_channel_number_ctrl")
    plot.add_ctrl("17_offset_ctrl")
    plot.add_ctrl("19_tp_overlay_ctrl")
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
        State("adc_map_selection_ctrl", "value"),
        State('channel_number_ctrl',"value"),
        State('17_offset_ctrl',"value"),
        State('19_tp_overlay_ctrl',"value"),
        State('file_select_ctrl', "value"),
        State(plot_id, "children"),
    )
    def plot_fft_graph(n_clicks,refresh, trigger_record,partition,run,plane,channel_num,offset,overlay_tps,raw_data_file,original_state):
    
        load_figure_template(theme)
        
        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:

                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))

                #logging.info(f"Initial Time Stamp: {data.ts_min}")
                #logging.info(" ")
                #logging.info("Initial Dataframe:")
                #logging.info(data.df_tsoff)

                if data.df_dict["trh"].size != 0:

                    if channel_num:

                        #figs = []
                        #for ch in channel_num:
                            #fig = plot_WIBEth_waveform(df_dict=data.df_dict,
                            #                           tpc_det_key=data.tpc_datkey,channel=ch,
                            #                           offset=offset,overlay_tps=overlay_tps)
                            #if fig is not None:
                            #    figs += wrap_figure(fig,run,trigger_record,ch)
                            #else:
                            #    figs.append(html.H6(nothing_to_plot()))
                        det_keys = [ key for key in data.df_dict if key.startswith('detw') and 'TPC' in key ]
                        return(html.Div(selection_line(partition,run,raw_data_file, trigger_record)),
                               html.Div([ wrap_figure(plot_TPC_waveform(df_dict=data.df_dict, det_keys=det_keys,channel=ch,
                                                                        offset=offset,
                                                                        make_tp_overlay=("tp_overlay" in overlay_tps),
                                                                        make_ta_overlay=("ta_overlay" in overlay_tps)),
                                                                        run_number=run,trigger_number=trigger_record[0],channel_num=ch) for ch in channel_num]))
#                               html.Div(figs))

                    else:
                        return(html.Div(html.H6("No Channel Selected")))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))
                    
            return(original_state)
        return(html.Div())

def wrap_figure(fig,run_number,trigger_number,channel_num):
    fig.update_layout(xaxis_title="Time Ticks", yaxis_title="ADC Waveform",
                      #height=fig_h,
                      title_text=f"Run {run_number}: {trigger_number} - Channel {channel_num}",
                      legend=dict(x=0,y=1),
                      )

    add_dunedaq_annotation(fig)
    fig.update_layout(font_family="Lato", title_font_family="Lato")
    return(html.Div([html.B(f"Waveform and TPs for channel {channel_num}"),dcc.Graph(id='graph-{}'.format(channel_num), figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]))


def graph(partition,run,raw_data_file, trigger_record,data,offset,plane,overlay_tps,channel_num):
                   
    if int(channel_num) in data.channels:
        logging.info(f"Channel number selected: {channel_num}")

        if "offset_removal" in offset:
                                        
            if "Z" in plane:
                try:
                    logging.info(f"Dataframe for Z-Plane for channel: {channel_num} :")
                    logging.info(data.df_Z.T.loc[channel_num])
                    fig=px.line((data.df_Z - data.df_Z_mean),y=channel_num)
               
                    if  "tp_overlay" in overlay_tps :
                        waveform_tps(fig, data.tp_df_Z, channel_num)
                except KeyError: pass
                                            
            if "V" in plane:
                try:
                    logging.info(f"Dataframe for V-Plane for channel: {channel_num} :")
                    logging.info(data.df_V.T.loc[channel_num])
                    fig=px.line((data.df_V - data.df_V_mean),y=channel_num)
                    if  "tp_overlay" in overlay_tps :
                        waveform_tps(fig,data.tp_df_V,channel_num)
                except KeyError:pass
            
            if "U" in plane:
                try:
                    logging.info(f"Dataframe for U-Plane for channel: {channel_num} :")
                    logging.info(data.df_U.T.loc[channel_num])
                    fig=px.line((data.df_U - data.df_U_mean),y=channel_num)
                    if  "tp_overlay" in overlay_tps :
                        waveform_tps(fig, data.tp_df_U, channel_num)
                except KeyError:pass                       
                                    
        else:

            fig=px.line(data.df_tsoff,y=channel_num)
            if  "tp_overlay" in overlay_tps :
                waveform_tps(fig, data.tp_df_tsoff, channel_num)                     

        fig.update_layout(xaxis_title="Time Ticks", yaxis_title="ADC Waveform",
                                            #height=fig_h,
                                            title_text=f"Run {data.info['run_number']}: {data.info['trigger_number']} - Channel {channel_num}",
                                            legend=dict(x=0,y=1),
                                            )
                                        
        add_dunedaq_annotation(fig)
        fig.update_layout(font_family="Lato", title_font_family="Lato")
        return(html.Div([html.B(f"Waveform and TPs for channel {channel_num}"),dcc.Graph(id='graph-{}'.format(channel_num), figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]))
    else:
        return(html.Div())   
                                            
