from dash import html, dcc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import rich
import logging
import numpy as np
from .. import plot_class
from ... plotting_functions import add_dunedaq_annotation, add_runinfo_annotation, selection_line, tp_hist_for_mean_std,nothing_to_plot

from dqmtools.dqmplots import *


def return_obj(dash_app, engine, storage,theme):
    plot_id = "05_std_plot"
    plot_div = html.Div(id = plot_id)
    
    plot = plot_class.plot("std_plot", plot_id, plot_div, engine, storage,theme)
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
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State('trigger_record_select_ctrl', "value"),
        State('file_select_ctrl', "value"),
        State(plot_id, "children")
    )
    def plot_std_graph(n_clicks,refresh, partition,run,trigger_record, raw_data_file,original_state):

        load_figure_template(theme)
        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div(""))
                
                if data.df_dict["trh"].size != 0:

                    try:
                        det_keys = [ key for key in data.df_dict if key.startswith('detd') and 'TPC' in key ]
                        fig_std  = plot_TPCData_by_channel(df_dict=data.df_dict,var="adc_rms",
                                                           det_keys=det_keys,
                                                           tpc_chmap=storage.engine.tpc_ch_map,
                                                           facet_by_plane=True,
                                                           title=None,ylabel="ADC RMS")
                    except KeyError:
                        return( html.Div([html.H6("No relevant TPC data found"),
                                          html.H6(nothing_to_plot())]))

                    if fig_std is None:
                        return( html.Div([html.H6("No relevant TPC data found"),
                                          html.H6(nothing_to_plot())]))

                    """if "tp_multiplicity" in tps:
                        data.init_tp()
                        fig_std = make_subplots(rows=2, cols=3,shared_xaxes=True,row_heights=[1.4,0.4],
                        vertical_spacing=0.04,
                        subplot_titles=("STD U-Plane", "STD V-Plane", "STD Z-Plane"))

                        fig_std.add_trace(tp_hist_for_mean_std(data.tp_df_U,data.xmin_U,data.xmax_U,  data.info),row=2,col=1)
                        fig_std.add_trace(tp_hist_for_mean_std(data.tp_df_V,data.xmin_V,data.xmax_V,  data.info),row=2,col=2)
                        fig_std.add_trace(tp_hist_for_mean_std(data.tp_df_Z,data.xmin_Z,data.xmax_Z,  data.info),row=2,col=3)
                    """

                    fig_std.update_layout(
                        # autosize=False,
                        # width=1200,
                        # height=600,
                        margin=dict(
                            l=50,
                            r=50,
                            b=60,
                            t=60,
                            pad=4
                        )
                        # showlegend=False
                    )
                    add_dunedaq_annotation(fig_std)
                    add_runinfo_annotation(fig_std, partition, run, trigger_record)

                    fig_std.update_layout(font_family="Lato", title_font_family="Lato")
                    if theme=="flatly":
                        fig_std.update_layout(plot_bgcolor='lightgrey')
                    return(html.Div([html.Br(),html.H4("STD by plane"),dcc.Graph(figure=fig_std,style={"marginTop":"10px"})]))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
