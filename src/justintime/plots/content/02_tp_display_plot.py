from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import load_figure_template
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import rich
import logging
import pandas as pd
from .. import plot_class
from ... cruncher import datamanager
from ... data_cache import TriggerRecordData
from ... plotting_functions import add_dunedaq_annotation, selection_line, make_static_img, make_tp_plot,make_tp_density,nothing_to_plot

import dqmtools.dataframe_creator as dfc

TP_KEY = "trgd_kDAQ_kTriggerPrimitive"
TA_KEY = "trgd_kDAQ_kTriggerActivity"

PLANES = {"Z": 2, "V": 1, "U": 0}


def _filter_by_plane(df, plane):
    if plane is None:
        return df
    if plane == "other":
        return df.loc[~df["plane"].isin(PLANES.values())]
    return df.loc[df["plane"] == plane]


def get_tp_df(data, plane=None):
    if TP_KEY not in data.df_dict:
        return pd.DataFrame()

    df = data.df_dict[TP_KEY]
    df = df.merge(data.df_dict["frh"]["trigger_timestamp_dts"], left_index=True, right_index=True)
    df, index = dfc.select_record(df)
    df = df.reset_index()

    df["time_peak"] = (df["time_start"].astype(np.int64) + df["samples_to_peak"] * 32) - df["trigger_timestamp_dts"]

    return _filter_by_plane(df, plane)


def get_ta_df(data, plane=None):
    if TA_KEY not in data.df_dict:
        return pd.DataFrame()

    df = data.df_dict[TA_KEY]
    df = df.merge(data.df_dict["frh"]["trigger_timestamp_dts"], left_index=True, right_index=True)
    df, index = dfc.select_record(df)
    df = df.reset_index()

    for col in ["time_start", "time_end", "time_peak"]:
        df[col] = df[col].astype(np.int64) - df["trigger_timestamp_dts"]

    return _filter_by_plane(df, plane)


def get_channel_range(data, plane):
    det_keys = [k for k in data.df_dict if k.startswith("detw") and "TPC" in k]

    mins, maxs = [], []
    for det_key in det_keys:
        df = data.df_dict[det_key]
        df = df.loc[df["plane"] == plane]
        if len(df) != 0:
            channels = df.index.get_level_values("channel")
            mins.append(channels.min())
            maxs.append(channels.max())

    if not mins:
        return 0, 0
    return min(mins), max(maxs)


def return_obj(dash_app, engine, storage,theme):
    plot_id = "02_tp_display_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("tp_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("90_plot_button_ctrl")
    plot.add_ctrl("08_adc_map_selection_ctrl")
    plot.add_ctrl("11_range_slider_pos_ctrl")
    plot.add_ctrl("14_density_plot_ctrl")
    plot.add_ctrl("20_orientation_height_ctrl")
    plot.add_ctrl('02_description_ctrl')

    init_callbacks(dash_app, storage, plot_id, engine,theme)
    return(plot)

def init_callbacks(dash_app, storage, plot_id, engine,theme):

    @dash_app.callback(
        Output(plot_id, "children"),
        Input("90_plot_button_ctrl", "n_clicks"),

        State('07_refresh_ctrl', "value"),
        State('trigger_record_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State('file_select_ctrl', "value"),
        State("adc_map_selection_ctrl","value"),
        State("11_range_slider_pos_comp", "value"),
        State('14_density_plot_ctrl', "value"),
        State('orientation_ctrl', "value"),
        State("height_select_ctrl","value"),
        State('02_description_ctrl',"style"),
        State(plot_id, "children"),
    )
    def plot_tp_graph(n_clicks, refresh, trigger_record, partition, run, raw_data_file,adcmap, tr_color_range, density, orientation, height, description,original_state):
        load_figure_template(theme)
        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))

                if data.df_dict["trh"].size != 0:

                    tp_df_all = get_tp_df(data)
                    if tp_df_all.empty:
                        return(html.Div(html.H6("No TPs found")))

                    fzmin, fzmax = tr_color_range
                    fig_w, fig_h = 2600, 600
                    info = {"run_number": data.run, "trigger_number": data.trigger}
                    children = []

                    if "density_plot" in density:
                        logging.info("2D Density plot chosen")

                        for plane_label, plane in PLANES.items():
                            if plane_label in adcmap:
                                xmin, xmax = get_channel_range(data, plane)
                                fig = make_tp_density(get_tp_df(data, plane), xmin, xmax, fzmin, fzmax, fig_w, fig_h, info)
                                add_dunedaq_annotation(fig)
                                children += [
                                    html.B(f"TPs: {plane_label}-plane, Initial TS:"+str(data.get_trigger_ts())),
                                    dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]

                        tp_df_o = get_tp_df(data, "other")
                        xmin_o, xmax_o = (tp_df_o["channel"].min(), tp_df_o["channel"].max()) if not tp_df_o.empty else (0, 0)
                        fig = make_tp_density(tp_df_o, xmin_o, xmax_o, fzmin, fzmax, fig_w, fig_h, info)
                        add_dunedaq_annotation(fig)
                        children += [
                            html.B("TPs: Others, Initial TS:"+str(data.get_trigger_ts())),
                            dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})]
                    else:
                        logging.info("Scatter Plot Chosen")

                        for plane_label, plane in PLANES.items():
                            if plane_label in adcmap:
                                xmin, xmax = get_channel_range(data, plane)
                                fig = make_tp_plot(get_tp_df(data, plane), get_ta_df(data, plane), xmin, xmax, fzmin, fzmax, fig_w, fig_h, info, orientation)
                                add_dunedaq_annotation(fig)
                                children += [
                                    html.B(f"TPs: {plane_label}-plane, Initial TS:"+str(data.get_trigger_ts())),
                                    dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})
                                ]

                        tp_df_o = get_tp_df(data, "other")
                        if not tp_df_o.empty:
                            xmin_o, xmax_o = tp_df_o["channel"].min(), tp_df_o["channel"].max()
                            fig = make_tp_plot(tp_df_o, get_ta_df(data, "other"), xmin_o, xmax_o, fzmin, fzmax, fig_w, fig_h, info, orientation)
                            add_dunedaq_annotation(fig)
                            children += [
                                html.B("TPs: Others, Initial TS:"+str(data.get_trigger_ts())),
                                dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"})
                            ]

                    if adcmap:
                        return(html.Div([
                            selection_line(partition,run,raw_data_file, trigger_record),
                            html.Div(children)]))
                    else:
                        return(html.Div(html.H6("No ADC map selected")))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
