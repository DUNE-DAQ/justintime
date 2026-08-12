from dash import html, dcc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import rich
import logging
from .. import plot_class
from ... plotting_functions import add_dunedaq_annotation, selection_line,nothing_to_plot

def return_obj(dash_app, engine, storage,theme):
    plot_id = "07_fft_phase_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("fft_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("13_fft_phase_fmin_fmax_ctrl")
    plot.add_ctrl("90_plot_button_ctrl")

    init_callbacks(dash_app, storage, plot_id, engine,theme)
    return(plot)

def init_callbacks(dash_app, storage, plot_id, engine,theme):

    @dash_app.callback(
        Output(plot_id, "children"),
        Input("90_plot_button_ctrl", "n_clicks"),
        State('07_refresh_ctrl', "n_clicks"),
        State('trigger_record_select_ctrl', "value"),
        State('file_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State('13_fft_phase_fmin_comp', "value"),
        State('13_fft_phase_fmax_comp', "value"),
        State(plot_id, "children"),
    )
    def plot_fft_phase_graph(n_clicks,refresh, trigger_record, raw_data_file,partition,run, fmin, fmax, original_state):

        load_figure_template(theme)
        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))

                logging.info(f"Initial Time Stamp: {data.ts_min}")
                logging.info(" ")
                logging.info("Initial Dataframe:")
                logging.info(data.df_tsoff)
                
                if fmin is None or fmax is None:
                    return(html.Div(html.H6("Please enter both fmin and fmax")))

                if len(data.df)!=0 and len(data.df.index!=0):

                    data.init_fft_phase(fmin, fmax)
                    #rich.print(data.fft_phase)

                    fig = px.scatter(data.fft_phase[f"{fmin}-{fmax}"], y='phase', color=data.fft_phase[f"{fmin}-{fmax}"]['femb'].astype(str),labels={'color':'FEMB ID'}, facet_col='plane', facet_col_wrap=2, facet_col_spacing=0.03, facet_row_spacing=0.07, title=f"Trigger record: Run {data.info['run_number']}, {data.info['trigger_number']} fmin = {fmin}, fmax = {fmax}")
                    fig.update_xaxes(matches=None, showticklabels=True)
                    fig.update_yaxes(matches=None, showticklabels=True)
                    fig.update_layout(height=900)
                    add_dunedaq_annotation(fig)
                    fig.update_layout(font_family="Lato", title_font_family="Lato")
                    return(html.Div([
                        selection_line(partition,run,raw_data_file, trigger_record),
                        html.B("Noise phase by FEMB peak"),
                        #html.Hr(),
                        dcc.Graph(figure=fig)]))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))

            return(original_state)

        return(html.Div())