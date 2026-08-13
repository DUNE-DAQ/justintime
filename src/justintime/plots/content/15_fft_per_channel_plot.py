from .. import plot_class
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
from ... plotting_functions import add_dunedaq_annotation, selection_line,waveform_tps,nothing_to_plot
from ... cruncher import signal

import dqmtools.dataframe_creator as dfc


def get_channel_waveform(data, channel):
    det_keys = [k for k in data.df_dict if k.startswith("detw") and "TPC" in k]

    for det_key in det_keys:
        df = data.df_dict[det_key]
        idx_names = df.index.names
        df = df.reset_index()
        df = df.loc[df["channel"] == int(channel)]
        if len(df) == 0:
            continue
        df = df.set_index(idx_names)
        df, index = dfc.select_record(df)
        df = df.reset_index()
        return df["adcs"].values[0]

    return None


def return_obj(dash_app, engine, storage,theme):
    plot_id = "15_fft_per_channel_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("FFT_Channel_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("16_channel_number_ctrl")
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
        State('file_select_ctrl', "value"),
        State(plot_id, "children"),
    )
    def plot_fft_graph(n_clicks, refresh,trigger_record,partition,run,plane,channel_num,raw_data_file, original_state):

        load_figure_template(theme)

        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))

                if data.df_dict["trh"].size != 0:
                    if channel_num:

                        return(html.Div(selection_line(partition,run,raw_data_file, trigger_record)),html.Div([graph(partition,run,raw_data_file, trigger_record,data,val) for val in channel_num]
                                            ))

                    else:
                        return(html.Div(html.H6("No Channel Selected")))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))

            return(original_state)
        return(html.Div())

def graph(partition,run,raw_data_file, trigger_record,data,channel_num):

    waveform = get_channel_waveform(data, channel_num)

    if waveform is not None:

        logging.info(f"Channel number selected: {channel_num}")
        df_wave = pd.DataFrame({channel_num: waveform})
        _, df_fft_sq = signal.calc_fft_fft_sq(df_wave)
        logging.info("FFT for the selected channel values:")
        logging.info(df_fft_sq[channel_num])
        fig=px.line(df_fft_sq,y=channel_num)
        fig.update_layout(
        xaxis_title="Frequency",
        yaxis_title="FFT",
        #height=fig_h,
        title_text=f"Run {data.run}: {data.trigger}",
        legend=dict(x=0,y=1),
        width=950,
        )

        add_dunedaq_annotation(fig)
        fig.update_layout(font_family="Lato", title_font_family="Lato")
        return(html.Div([
                html.B(f"FFT for channel {channel_num}",style={"marginTop":"10px"}),#html.Hr(),
                dcc.Graph(id='graph-{}'.format(channel_num), figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]))

    else:
        return(html.Div())
