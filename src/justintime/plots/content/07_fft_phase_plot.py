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

import dqmtools.dataframe_creator as dfc


def _vstack_common_length(arrays):
    """np.vstack that tolerates per-channel sample-count jitter: real hardware data can
    have a handful of channels within the same det_key off by a few tens of samples
    (confirmed on real VD TopTPC data: lengths of 9472/9536/9600 all present together).
    Truncating to the shortest length present is a lot better than dropping the whole
    det_key on a plain vstack ValueError."""
    n = min(len(a) for a in arrays)
    return np.vstack([a[:n] for a in arrays])


def get_channel_phase_df(data, fmin, fmax):
    """Per-channel mean FFT phase in the [fmin, fmax] band, across every TPC channel.

    Computed directly from each det_key's waveform matrix with numpy (FFT along the
    sample axis per channel) rather than a wide per-channel pandas reshape -- at
    whole-detector channel counts a pandas-level reshape does not scale (see 06_fft_plot.py)."""

    det_keys = [k for k in data.df_dict if k.startswith("detw") and "TPC" in k]
    if not det_keys:
        return pd.DataFrame()

    rows = []
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

        freq = np.fft.fftfreq(adcs_matrix.shape[1], 0.512e-6)
        band = (freq > fmin) & (freq < fmax)
        if not band.any():
            continue

        fft = np.fft.fft(adcs_matrix, axis=1)
        phase = np.angle(fft[:, band]).mean(axis=1)

        rows.append(pd.DataFrame({
            "channel": df_tmp["channel"].astype(int).values,
            "plane": df_tmp["plane"].values,
            "element": df_tmp["element"].values,
            "phase": phase,
        }))

    if not rows:
        return pd.DataFrame()

    return pd.concat(rows, ignore_index=True)


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

                if fmin is None or fmax is None:
                    return(html.Div(html.H6("Please enter both fmin and fmax")))

                if data.df_dict["trh"].size != 0:

                    phase_df = get_channel_phase_df(data, fmin, fmax)
                    if phase_df.empty:
                        return(html.Div(html.H6(nothing_to_plot())))

                    fig = px.scatter(phase_df, x="channel", y='phase', color=phase_df['element'].astype(str),
                                     labels={'color':'APA/CRP'}, facet_col='plane', facet_col_wrap=2,
                                     facet_col_spacing=0.03, facet_row_spacing=0.07,
                                     title=f"Trigger record: Run {data.run}, {data.trigger} fmin = {fmin}, fmax = {fmax}")
                    fig.update_xaxes(matches=None, showticklabels=True)
                    fig.update_yaxes(matches=None, showticklabels=True)
                    fig.update_layout(height=900)
                    add_dunedaq_annotation(fig)
                    fig.update_layout(font_family="Lato", title_font_family="Lato")
                    return(html.Div([
                        selection_line(partition,run,raw_data_file, trigger_record),
                        html.B("Noise phase by channel"),
                        #html.Hr(),
                        dcc.Graph(figure=fig)]))
                else:
                    return(html.Div(html.H6(nothing_to_plot())))

            return(original_state)

        return(html.Div())
