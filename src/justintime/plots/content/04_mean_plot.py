from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import rich
import logging

from ... plotting_functions import add_dunedaq_annotation, selection_line,nothing_to_plot,tp_hist_for_mean_std
from .. import plot_class

from dqmtools.dqmplots import *

def return_obj(dash_app, engine, storage,theme):
    plot_id = "04_mean_plot"
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
        State(plot_id, "children")
    )
    def plot_mean_graph(n_clicks,refresh, trigger_record,partition,run,raw_data_file,original_state):

        load_figure_template(theme)
        if trigger_record and raw_data_file:
            
            if plot_id in storage.shown_plots:
                    try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                    except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))
                    
                    logging.info(f"Trigger Time Stamp: {data.get_trigger_ts()}")
                    logging.info(" ")
                    logging.info("Initial Dataframe:")
                    logging.info(data.df_dict)

                    if data.df_dict["trh"].size != 0:

                        try:
                            det_keys = [ key for key in data.df_dict if key.startswith('detd') and 'TPC' in key ]
                            fig_mean = plot_TPCData_by_channel(df_dict=data.df_dict,var="adc_mean",
                                                               det_keys=det_keys,
                                                               tpc_chmap=storage.engine.tpc_ch_map,
                                                               facet_by_plane=True,
                                                               title=None,ylabel="ADC Mean")
                        except KeyError:
                            return( html.Div([html.H6("No relevant TPC data found"),
                                              html.H6(nothing_to_plot())]))

                        if fig_mean is None:
                            return( html.Div([html.H6("No relevant TPC data found"),
                                              html.H6(nothing_to_plot())]))

                        fig_mean.update_layout(
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
                        add_dunedaq_annotation(fig_mean)
                        fig_mean.update_layout(font_family="Lato", title_font_family="Lato")
                        if theme=="flatly":
                            fig_mean.update_layout(plot_bgcolor='lightgrey')
                        return(html.Div([selection_line(partition,run,raw_data_file, trigger_record),html.H4("Mean by plane"),dcc.Graph(figure=fig_mean,style={"marginTop":"10px"})]))
            else:
                return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
