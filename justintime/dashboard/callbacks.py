import dash
from dash import Dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import numpy as np
import pandas as pd
import datetime

import logging
from itertools import groupby
import rich

from . layout import generate_tr_card

from ..cruncher import signal





def attach(app: Dash, engine) -> None:

    @app.callback(
        Output('raw-data-file-select-A', 'options'),
        Output('raw-data-file-select-B', 'options'),
        Input('refresh_files', 'n_clicks')      
        )
    def update_file_list(pathname):
        fl = sorted(engine.list_files(), reverse=True)
        logging.debug(f"Updatd file list: {fl}")
        opts = [{'label': f, 'value':f} for f in engine.list_files()]
        return (
            opts,
            opts
            )


    @app.callback(
        Output('trigger-record-select-A', 'options'),
        Input('raw-data-file-select-A', 'value')
        )
    def update_trigger_record_select(raw_data_file):
        logging.debug(f'data file: {raw_data_file}')

        if not raw_data_file:
            return []
        tr_nums = [{'label':str(n), 'value':str(n)} for n in engine.get_trigger_record_list(raw_data_file)]
        logging.debug(f'Trigger nums: {tr_nums}')
        return tr_nums


    @app.callback(
        Output('trigger-record-select-B', 'options'),
        Input('raw-data-file-select-B', 'value')
        )
    def update_trigger_record_select(raw_data_file):
        logging.debug(f'data file: {raw_data_file}')

        if not raw_data_file:
            return []
        tr_nums = [{'label':str(n), 'value':str(n)} for n in engine.get_trigger_record_list(raw_data_file)]
        logging.debug(f'Trigger nums: {tr_nums}')
        return tr_nums


    # def calc_mean_std_by_plane(df, planes):
    #     df_std = df.std()
    #     df_mean = df.mean()
    #     logging.debug(f"Mean and standard deviation calculated")

    #     p = {k:list(set(v) & set(df.columns)) for k,v in planes.items()}
    #     df_p0_mean = df_mean[p[0]]
    #     df_p1_mean = df_mean[p[1]]
    #     df_p2_mean = df_mean[p[2]]

    #     df_p0_std = df_std[p[0]]
    #     df_p1_std = df_std[p[1]]
    #     df_p2_std = df_std[p[2]]

    #     return (df_std, df_mean, df_p0_mean, df_p1_mean, df_p2_mean, df_p0_std, df_p1_std, df_p2_std)
   

    # def calc_fft(df):
    #     df_fft = df.apply(np.fft.fft)
    #     df_fft_sq = np.abs(df_fft) ** 2
    #     freq = np.fft.fftfreq(df.index.size, 0.5e-6)
    #     df_fft['Freq'] = freq
    #     df_fft_sq['Freq'] = freq
    #     # Cleanup fft2 for plotting
    #     df_fft_sq = df_fft_sq[df_fft_sq['Freq']>0]
    #     df_fft_sq = df_fft_sq.set_index('Freq')
    #     return df_fft, df_fft_sq


    # def calc_fft_sum_by_plane(df, planes):
    #     p = {k:list(set(v) & set(df.columns)) for k,v in planes.items()}

    #     df_sum_U = df[p[0]].sum(axis=1).to_frame()
    #     df_sum_U = df_sum_U.rename(columns= {0: 'U-plane'})
    #     df_sum_V = df[p[1]].sum(axis=1).to_frame()
    #     df_sum_V = df_sum_V.rename(columns= {0: 'V-plane'})
    #     df_sum_Z = df[p[2]].sum(axis=1).to_frame()
    #     df_sum_Z = df_sum_Z.rename(columns= {0: 'Z-plane'})
    #     df_sums = pd.concat([df_sum_U, df_sum_V, df_sum_Z], axis=1)


    #     df_fft = df_sums.apply(np.fft.fft)
    #     df_fft2 = np.abs(df_fft) ** 2
    #     freq = np.fft.fftfreq(df_sums.index.size, 0.5e-6)
    #     df_fft2['Freq'] = freq
    #     df_fft2 = df_fft2[df_fft2['Freq']>0]
    #     df_fft2 = df_fft2.set_index('Freq')

    #     return df_fft2.sort_index()


    # def calc_diffs(df_a, df_b):

    #     # value_offset=4096
    #     dt_a_rst = df_a.reset_index().drop('ts', axis=1)
    #     dt_b_rst = df_b.reset_index().drop('ts', axis=1)
    #     dt_ab_diff = (dt_a_rst.astype('int')-dt_b_rst.astype('int'))

    #     return dt_ab_diff

    @app.callback(
        Output('plots_card', 'children'),
        Input('plot_button', 'n_clicks'),
        State('raw-data-file-select-A', 'value'),
        State('trigger-record-select-A', 'value'),
        State('raw-data-file-select-B', 'value'),
        State('trigger-record-select-B', 'value'),
        State('plot_selection', 'value'),
        State('adcmap-selection-a', 'value'),
        State('adcmap-selection-b', 'value'),
        State('adcmap-selection-ab-diff', 'value'),
        State('adcmap-selection-a-offset', 'value'),
        State('adcmap-selection-a-cnr', 'value'),
        State('tr-color-range-slider', 'value'),
        )
    def update_plots(
        n_clicks,
        raw_data_file_a,
        trig_rec_num_a,
        raw_data_file_b,
        trig_rec_num_b,
        plot_selection,
        adcmap_selection_a,
        adcmap_selection_b,
        adcmap_selection_ab_diff,
        adcmap_selection_a_offset,
        adcmap_selection_a_cnr,
        tr_color_range
        ):
        # ctx = dash.callback_context


        children = []

        if not trig_rec_num_a or not trig_rec_num_b:
            raise PreventUpdate
        # #----


        # Load records
        info_a, df_a = engine.load_trigger_record(raw_data_file_a, int(trig_rec_num_a))
        # Timestamp information
        ts_a = info_a['trigger_timestamp']*20/1000000000
        dt_a = datetime.datetime.fromtimestamp(ts_a).strftime('%c')

        # #----
        info_b, df_b = engine.load_trigger_record(raw_data_file_b, int(trig_rec_num_b))
        # Timestamp information
        ts_b = info_b['trigger_timestamp']*20/1000000000
        dt_b = datetime.datetime.fromtimestamp(ts_b).strftime('%c')

        channels = list(set(df_a.columns) | set(df_b.columns))

        group_planes = groupby(channels, lambda ch: engine.ch_map.get_plane_from_offline_channel(int(ch)))
        planes = {k: [x for x in d if x] for k,d in group_planes}

        # Splitting by plane
        planes_a = {k:sorted(set(v) & set(df_a.columns)) for k,v in planes.items()}
        df_aU = df_a[planes_a[0]]
        df_aV = df_a[planes_a[1]]
        df_aZ = df_a[planes_a[2]]

        df_aU_mean, df_aU_std = df_aU.mean(), df_aU.std()
        df_aV_mean, df_aV_std = df_aV.mean(), df_aV.std()
        df_aZ_mean, df_aZ_std = df_aZ.mean(), df_aZ.std()

        logging.debug(f"Trigger record {trig_rec_num_a} from {raw_data_file_a} loaded")


        # Splitting by plane
        planes_b = {k:list(set(v) & set(df_b.columns)) for k,v in planes.items()}
        df_bU = df_b[planes_b[0]]
        df_bV = df_b[planes_b[1]]
        df_bZ = df_b[planes_b[2]]
        logging.debug(f"Trigger record {trig_rec_num_b} from {raw_data_file_b} loaded")

        df_bU_mean, df_bU_std = df_bU.mean(), df_bU.std()
        df_bV_mean, df_bV_std = df_bV.mean(), df_bV.std()
        df_bZ_mean, df_bZ_std = df_bZ.mean(), df_bZ.std()

        if 'Mean_STD' in plot_selection:

            fig_mean = make_subplots(rows=1, cols=3,
                                subplot_titles=("Mean U-Plane", "Mean V-Plane", "Mean Z-Plane"))
            fig_mean.add_trace(
                go.Scattergl(x=df_aU_mean.index.astype(int), y=df_aU_mean, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=1
            )
            fig_mean.add_trace(
                go.Scattergl(x=df_bU_mean.index.astype(int), y=df_bU_mean, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                row=1, col=1
            )

            fig_mean.add_trace(
                go.Scattergl(x=df_aV_mean.index.astype(int), y=df_aV_mean, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=2
            )
            fig_mean.add_trace(
                go.Scattergl(x=df_bV_mean.index.astype(int), y=df_bV_mean, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                row=1, col=2
            )

            fig_mean.add_trace(
                go.Scattergl(x=df_aZ_mean.index.astype(int), y=df_aZ_mean, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=3
            )
            fig_mean.add_trace(
                go.Scattergl(x=df_bZ_mean.index.astype(int), y=df_bZ_mean, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                row=1, col=3
            )

            fig_mean.update_layout(
                # autosize=False,
                # width=1200,
                # height=600,
                margin=dict(
                    l=50,
                    r=50,
                    b=100,
                    t=100,
                    pad=4
                ),
                # showlegend=False
            )

            logging.debug(f"Mean plots created")


            fig_std = make_subplots(rows=1, cols=3,
                                subplot_titles=("STD U-Plane", "STD V-Plane", "STD Z-Plane"))
            fig_std.add_trace(
                go.Scattergl(x=df_aU_std.index.astype(int), y=df_aU_std, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=1
            )
            fig_std.add_trace(
                go.Scattergl(x=df_bU_std.index.astype(int), y=df_bU_std, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                row=1, col=1
            )

            fig_std.add_trace(
                go.Scattergl(x=df_aV_std.index.astype(int), y=df_aV_std, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=2
            )
            fig_std.add_trace(
                go.Scattergl(x=df_bV_std.index.astype(int), y=df_bV_std, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                row=1, col=2
            )

            fig_std.add_trace(
                go.Scattergl(x=df_aZ_std.index.astype(int), y=df_aZ_std, mode='markers', name=f"Run {info_a['run_number']}: {info_a['trigger_number']}"),
                row=1, col=3
            )
            fig_std.add_trace(
                go.Scattergl(x=df_bZ_std.index.astype(int), y=df_bZ_std, mode='markers', name=f"Run {info_b['run_number']}: {info_b['trigger_number']}"),
                row=1, col=3
            )

            fig_std.update_layout(
                # autosize=False,
                # width=1200,
                # height=600,
                margin=dict(
                    l=50,
                    r=50,
                    b=100,
                    t=100,
                    pad=4
                ),
                # showlegend=False
            )

            logging.debug(f"STD plots created")

            children += [
                    html.B("Mean by plane"),
                    html.Hr(),
                    dcc.Graph(figure=fig_mean),
                    html.B("STD by plane"),
                    html.Hr(),
                    dcc.Graph(figure=fig_std),
            ]

        if 'FFT' in plot_selection:

            df_a_fft2 = signal.calc_fft_sum_by_plane(df_a, planes)
            df_b_fft2 = signal.calc_fft_sum_by_plane(df_b, planes)

            df_U_plane = pd.concat([df_a_fft2['U-plane'], df_b_fft2['U-plane']], axis=1, keys=["A", "B"])
            df_V_plane = pd.concat([df_a_fft2['V-plane'], df_b_fft2['V-plane']], axis=1, keys=["A", "B"])
            df_Z_plane = pd.concat([df_a_fft2['Z-plane'], df_b_fft2['Z-plane']], axis=1, keys=["A", "B"])

            logging.debug(f"FFT plots created")

            children += [
                html.B("FFT U-Plane"),
                html.Hr(),
                dcc.Graph(figure=px.line(df_U_plane, log_y=True, title=f"FFT U-plane, A vs B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}")),
                html.B("FFT V-Plane"),
                html.Hr(),
                dcc.Graph(figure=px.line(df_V_plane, log_y=True, title=f"FFT V-plane, A vs B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}")),
                html.B("FFT Z-Plane"),
                html.Hr(),
                dcc.Graph(figure=px.line(df_Z_plane, log_y=True, title=f"FFT Z-plane, A vs B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}")),
            ]

        if 'FFT_phase' in plot_selection:

            def find_plane(offch):
                m={0:'U', 1:'V', 2:'Z'}
                p = engine.ch_map.get_plane_from_offline_channel(offch)
                if p in m:
                    return m[p]
                else:
                    return 'D'

            logging.debug(f"Calculating FFT")

            df_a_fft = signal.calc_fft(df_a)

            logging.debug(f"Extracting FFT phase (22kHz) peak ")
            fmin = 21000
            fmax = 24000
            df_a_phase_22 = signal.calc_fft_phase(df_a_fft, fmin, fmax)

            logging.debug(f"FFT phase calculated")

            df_a_phase_22['femb'] = df_a_phase_22.index.map(engine.femb_id_from_offch)
            df_a_phase_22['plane'] = df_a_phase_22.index.map(find_plane)
            logging.debug(f"FFT phase - femb and plane added")


            fig_22 = px.scatter(df_a_phase_22, y='phase', color=df_a_phase_22['femb'].astype(str), labels={'color':'FEMB ID'}, facet_col='plane', facet_col_wrap=2, facet_col_spacing=0.03, facet_row_spacing=0.07, title=f"Trigger record A: Run {info_a['run_number']}, {info_a['trigger_number']} 22kHz")

            fig_22.update_xaxes(matches=None, showticklabels=True)
            fig_22.update_yaxes(matches=None, showticklabels=True)
            fig_22.update_layout(height=900)
            logging.debug(f"FFT phase plots created")


            logging.debug(f"Extracting FFT phase (210kHz) peak ")
            fmin = 129000
            fmax = 220000
            df_a_phase_210 = signal.calc_fft_phase(df_a_fft, fmin, fmax)

            logging.debug(f"FFT phase calculated")

            df_a_phase_210['femb'] = df_a_phase_210.index.map(engine.femb_id_from_offch)
            df_a_phase_210['plane'] = df_a_phase_210.index.map(find_plane)
            logging.debug(f"FFT phase - femb and plane added")


            fig_210 = px.scatter(df_a_phase_210, y='phase', color=df_a_phase_210['femb'].astype(str), labels={'color':'FEMB ID'}, facet_col='plane', facet_col_wrap=2, facet_col_spacing=0.03, facet_row_spacing=0.07, title=f"Trigger record A: Run {info_a['run_number']}, {info_a['trigger_number']} 210kHz")

            fig_210.update_xaxes(matches=None, showticklabels=True)
            fig_210.update_yaxes(matches=None, showticklabels=True)
            fig_210.update_layout(height=900)
            logging.debug(f"FFT phase plots created")


            logging.debug(f"Extracting FFT phase (430kHz) peak ")
            fmin=405000
            fmax=435000
            df_a_phase_430 = signal.calc_fft_phase(df_a_fft, fmin, fmax)

            logging.debug(f"FFT phase calculated")

            df_a_phase_430['femb'] = df_a_phase_430.index.map(engine.femb_id_from_offch)
            df_a_phase_430['plane'] = df_a_phase_430.index.map(find_plane)
            logging.debug(f"FFT phase - femb and plane added")


            fig_430 = px.scatter(df_a_phase_430, y='phase', color=df_a_phase_430['femb'].astype(str), labels={'color':'FEMB ID'}, facet_col='plane', facet_col_wrap=2, facet_col_spacing=0.03, facet_row_spacing=0.07, title=f"Trigger record A: Run {info_a['run_number']}, {info_a['trigger_number']} 430kHz")

            fig_430.update_xaxes(matches=None, showticklabels=True)
            fig_430.update_yaxes(matches=None, showticklabels=True)
            fig_430.update_layout(height=900)
            logging.debug(f"FFT phase plots created")


            children += [
                html.B("Noise phase by FEMB (22 Khz) peak"),
                html.Hr(),
                dcc.Graph(figure=fig_22),
                html.B("Noise phase by FEMB (210 Khz) peak"),
                html.Hr(),
                dcc.Graph(figure=fig_210),
                html.B("Noise phase by FEMB (430 Khz) peak"),
                html.Hr(),
                dcc.Graph(figure=fig_430),
            ]

        #-------------
        # Trigger Record Displays
        fig_w, fig_h = 1500, 1000
        # Waveforms A
        if 'Z' in adcmap_selection_a:
            fig = px.imshow(df_aZ, title=f"Z-plane, A - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: Z-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'V' in adcmap_selection_a:
            fig = px.imshow(df_aV, title=f"V-plane, A - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: V-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'U' in adcmap_selection_a:
            fig = px.imshow(df_aU, title=f"U-plane, A - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: U-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]


        # Waveforms B
        if 'Z' in adcmap_selection_b:
            fig = px.imshow(df_bZ, title=f"Z-plane, B - B: Run {info_b['run_number']}: {info_b['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: Z-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'V' in adcmap_selection_b:
            fig = px.imshow(df_bV, title=f"V-plane, B - B: Run {info_b['run_number']}: {info_b['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: V-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'U' in adcmap_selection_b:
            fig = px.imshow(df_bU, title=f"U-plane, B - B: Run {info_b['run_number']}: {info_b['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: U-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        dt_ab_U_diff = signal.calc_diffs(df_aU, df_bU)
        dt_ab_V_diff = signal.calc_diffs(df_aV, df_bV)
        dt_ab_Z_diff = signal.calc_diffs(df_aZ, df_bZ)

        if 'Z' in adcmap_selection_ab_diff:
            fig = px.imshow(dt_ab_Z_diff, title=f"Z-plane, A-B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: Z-plane A-B"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'V' in adcmap_selection_ab_diff:
            fig = px.imshow(dt_ab_V_diff, title=f"V-plane, A-B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: V-plane A-B"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'U' in adcmap_selection_ab_diff:
            fig = px.imshow(dt_ab_U_diff, title=f"U-plane, A-B - A: Run {info_a['run_number']}: {info_a['trigger_number']}, B: Run {info_b['run_number']}: {info_b['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: U-plane A-B"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        #-------------
        # Trigger Record Displays
        fig_w, fig_h = 1500, 1000
        fzmin, fzmax = tr_color_range
        
        # Waveforms A
        if 'Z' in adcmap_selection_a_offset:
            fig = px.imshow(df_aZ-df_aZ.mean(), zmin=fzmin, zmax=fzmax, title=f"Z-plane (offset removal), A - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: Z-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'V' in adcmap_selection_a_offset:
            fig = px.imshow(df_aV-df_aV.mean(), zmin=fzmin, zmax=fzmax, title=f"V-plane (offset removal), A - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: V-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'U' in adcmap_selection_a_offset:
            fig = px.imshow(df_aU-df_aU.mean(), zmin=fzmin, zmax=fzmax, title=f"U-plane (offset removal), A - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: U-plane"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]


        df_a_cnr = df_a.copy()
        df_a_cnr = df_a_cnr-df_a_cnr.mean()
        for p, p_chans in planes_a.items():
            for f,f_chans in engine.femb_to_offch.items():
                chans = list(set(p_chans) & set(f_chans))
                df_a_cnr[chans] = df_a_cnr[chans].sub(df_a_cnr[chans].mean(axis=1), axis=0)

        fzmin, fzmax = tr_color_range
        if 'Z' in adcmap_selection_a_cnr:
            fig = px.imshow(df_a_cnr[planes_a[2]], zmin=fzmin, zmax=fzmax, title=f"Z-plane, A (CNR) - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: Z-plane A (CNR)"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'V' in adcmap_selection_a_cnr:
            fig = px.imshow(df_a_cnr[planes_a[1]], zmin=fzmin, zmax=fzmax, title=f"V-plane, A (CNR) - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: V-plane A (CNR)"),
                html.Hr(),
                dcc.Graph(figure=fig),
            ]

        if 'U' in adcmap_selection_a_cnr:
            fig = px.imshow(df_a_cnr[planes_a[0]], zmin=fzmin, zmax=fzmax, title=f"U-plane, A (CNR) - A: Run {info_a['run_number']}: {info_a['trigger_number']}", aspect='auto')
            fig.update_layout(
                width=fig_w,
                height=fig_h,
            )
            children += [
                html.B("ADC Counts: U-plane A (CNR)"),
                html.Hr(),
                dcc.Graph(figure=fig),
                ]

        return [
                html.Div(
                    children=[
                        generate_tr_card("A", info_a['run_number'], info_a['trigger_number'], dt_a, raw_data_file_a),
                        generate_tr_card("B", info_b['run_number'], info_b['trigger_number'], dt_b, raw_data_file_b),
                    ]
                )
                ] + children

        
