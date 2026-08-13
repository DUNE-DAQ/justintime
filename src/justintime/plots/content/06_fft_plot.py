from dash import html, dcc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import rich
import logging
import pandas as pd
from ... plotting_functions import add_dunedaq_annotation, selection_line, nothing_to_plot
from .. import plot_class

import dqmtools.dataframe_creator as dfc


PLANE_NAMES = {0: "U-plane", 1: "V-plane", 2: "Z-plane"}


def _add_same_length(a, b):
    n = min(len(a), len(b))
    return a[:n] + b[:n]


def _vstack_common_length(arrays):
    """np.vstack that tolerates per-channel sample-count jitter: real hardware data can
    have a handful of channels within the same det_key off by a few tens of samples
    (confirmed on real VD TopTPC data: lengths of 9472/9536/9600 all present together).
    Truncating to the shortest length present is a lot better than dropping the whole
    det_key on a plain vstack ValueError."""
    n = min(len(a) for a in arrays)
    return np.vstack([a[:n] for a in arrays])


def get_plane_sum_df(data):
    """Sum every TPC channel's pedestal-subtracted waveform per-plane, per time tick.

    We only ever need the per-plane SUM (not the individual channels). At whole-detector
    channel counts (order 10k+), doing this via pandas explode/pivot/groupby means
    processing every one of the ~10k channels x ~10k samples as individual Python-level
    rows, which is far too slow (tested: 100s+ and counting). Channels within one det_key
    share a common sample count in practice (synchronized readout), so instead this
    vstacks each det_key's waveforms straight into a numpy matrix and sums with numpy --
    C-level vectorized, not row-by-row."""

    det_keys = [k for k in data.df_dict if k.startswith("detw") and "TPC" in k]
    if not det_keys:
        return pd.DataFrame()

    plane_totals = {0: None, 1: None, 2: None}
    time_axis = None

    for det_key in det_keys:
        df_tmp = data.df_dict[det_key]
        df_tmp = df_tmp.merge(data.df_dict["frh"]["trigger_timestamp_dts"], left_index=True, right_index=True)
        df_tmp = df_tmp.merge(data.df_dict["detd"+det_key[4:]]["adc_median"], left_index=True, right_index=True)
        df_tmp, index = dfc.select_record(df_tmp)
        df_tmp = df_tmp.reset_index()

        if df_tmp.empty:
            continue

        adcs_matrix = _vstack_common_length(df_tmp["adcs"].values).astype(np.float64)
        adcs_matrix -= df_tmp["adc_median"].values.astype(np.float64)[:, None]

        det_time_axis = df_tmp["timestamps"].iloc[0].astype(np.int64)[:adcs_matrix.shape[1]] - int(df_tmp["trigger_timestamp_dts"].iloc[0])
        if time_axis is None or len(det_time_axis) < len(time_axis):
            time_axis = det_time_axis

        planes = df_tmp["plane"].values
        for p in (0, 1, 2):
            mask = planes == p
            if not mask.any():
                continue
            plane_total = adcs_matrix[mask].sum(axis=0)
            plane_totals[p] = plane_total if plane_totals[p] is None else _add_same_length(plane_totals[p], plane_total)

    if time_axis is None:
        return pd.DataFrame()

    n = len(time_axis)
    data_cols = {}
    for p, name in PLANE_NAMES.items():
        total = plane_totals[p]
        if total is None:
            data_cols[name] = np.zeros(n)
        else:
            data_cols[name] = total[:n]

    return pd.DataFrame(data_cols, index=time_axis)


def calc_fft_power_by_plane(df_sums):
    """FFT power spectrum of each plane's summed waveform (positive frequencies only)."""
    df_fft = df_sums.apply(np.fft.fft)
    df_fft2 = np.abs(df_fft) ** 2
    freq = np.fft.fftfreq(df_sums.index.size, 0.512e-6)
    df_fft2['Freq'] = freq
    df_fft2 = df_fft2[df_fft2['Freq'] > 0]
    df_fft2 = df_fft2.set_index('Freq')
    return df_fft2.sort_index()


def return_obj(dash_app, engine, storage,theme):
    plot_id = "06_fft_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("fft_plot", plot_id, plot_div, engine, storage,theme)
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
        State(plot_id, "children"),
    )
    def plot_fft_graph(n_clicks, refresh,partition,run,trigger_record, raw_data_file, original_state):

        load_figure_template(theme)
        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))

                if data.df_dict["trh"].size != 0:

                    plane_sum_df = get_plane_sum_df(data)
                    if plane_sum_df.empty:
                        return(html.Div(html.H6(nothing_to_plot())))

                    df_fft2 = calc_fft_power_by_plane(plane_sum_df)

                    title_U=f"FFT U-plane: Run {data.run}: {data.trigger}"
                    title_V=f"FFT V-plane: Run {data.run}: {data.trigger}"
                    title_Z=f"FFT Z-plane: Run {data.run}: {data.trigger}"

                    fig_U = px.line(df_fft2, y="U-plane", log_y=True, title=title_U)
                    add_dunedaq_annotation(fig_U)
                    fig_V = px.line(df_fft2, y="V-plane", log_y=True, title=title_V)
                    add_dunedaq_annotation(fig_V)
                    fig_Z = px.line(df_fft2, y="Z-plane", log_y=True, title=title_Z)
                    add_dunedaq_annotation(fig_Z)
                    fig_U.update_layout(font_family="Lato", title_font_family="Lato")
                    fig_V.update_layout(font_family="Lato", title_font_family="Lato")
                    fig_Z.update_layout(font_family="Lato", title_font_family="Lato")
                    return(html.Div([
                        selection_line(partition,run,raw_data_file, trigger_record),
                        html.B("FFT U-Plane"),
                        #html.Hr(),
                        dcc.Graph(figure=fig_U),
                        html.B("FFT V-Plane"),
                        #html.Hr(),
                        dcc.Graph(figure=fig_V),
                        html.B("FFT Z-Plane"),
                        #html.Hr(),
                        dcc.Graph(figure=fig_Z)]))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
