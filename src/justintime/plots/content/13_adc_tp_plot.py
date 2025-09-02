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
from ... plotting_functions import add_dunedaq_annotation, selection_line, make_static_img, nothing_to_plot, make_tp_plot,make_tp_overlay, make_ta_overlay

from dqmtools.dqmplots import *

def return_obj(dash_app, engine, storage,theme):
    plot_id = "13_adc_tp_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("fft_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("23_apa_select_ctrl")
    plot.add_ctrl("90_plot_button_ctrl")
    plot.add_ctrl("08_adc_map_selection_ctrl")
    plot.add_ctrl("09_colorscale_ctrl")
    plot.add_ctrl("10_tr_colour_range_slider_ctrl")
    plot.add_ctrl("12_static_image_ctrl")
    plot.add_ctrl("19_tp_overlay_ctrl")
    plot.add_ctrl("17_offset_ctrl")
    plot.add_ctrl("20_orientation_height_ctrl")
    #plot.add_ctrl("18_cnr_ctrl")

    init_callbacks(dash_app, storage, plot_id, engine,theme)
    return(plot)


def formate_figure(fig, height, plane_id):
    fig.update_layout(
        height=height,
        showlegend=True
    )

    add_dunedaq_annotation(fig)
    fig.update_layout(font_family="Lato", title_font_family="Lato")

    fig.update_layout(legend=dict(yanchor="top", y=0.01, xanchor="left", x=1))

    children = [
        html.B(f"ADC Counts: {plane_id}-plane"),#, Initial TS: {str(data.ts_min)}"),
        #html.Hr(),
        dcc.Graph(figure=fig,style={"marginTop":"10px","marginBottom":"10px"}),
    ]

    return children

def init_callbacks(dash_app, storage, plot_id, engine, theme):

    @dash_app.callback(
        Output(plot_id, "children"),
        Input("90_plot_button_ctrl", "n_clicks"),
        State('07_refresh_ctrl', "value"),
        State('apa_select_ctrl', "value"),
        State('trigger_record_select_ctrl', "value"),
        State('file_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State("adc_map_selection_ctrl", "value"),
        State("colorscale_ctrl", "value"),
        State("10_tr_colour_range_slider_comp", "value"),
        State("12_static_image_ctrl", "value"),
        State("17_offset_ctrl", "value"),
        #State("18_cnr_ctrl", "value"),
        State("19_tp_overlay_ctrl","value"),
        State("orientation_ctrl","value"),
        State("height_select_ctrl","value"),
        State(plot_id, "children"),
    )

    def plot_trd_graph(n_clicks, refresh, apa_name, trigger_record, raw_data_file, partition, run, adcmap_selection, colorscale, tr_color_range, static_image, offset, overlay_tps, orientation, height, original_state):
        
        load_figure_template(theme)
        orientation = orientation
        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))

                if data.df_dict["trh"].size != 0:
                    det_keys = [ key for key in data.df_dict if key.startswith('detw') and 'TPC' in key ]
                    children = []
                    logging.debug(f"Making plot with adcmap_selection {adcmap_selection}, {apa_name}, overlay_tps {overlay_tps}")
                    if 'Z' in adcmap_selection:
                        logging.info("Z Plane selected")
                        fig = plot_TPC_adc_map(df_dict=data.df_dict, 
                                               det_keys=det_keys,
                                               plane=2, 
                                               ele=apa_name,
                                               make_static=static_image,
                                               make_tp_overlay=("tp_overlay" in overlay_tps),
                                               orientation=orientation, 
                                               colorscale=colorscale,
                                               color_range=tr_color_range,
                                               )
                        if fig is not None:
                            children += formate_figure(fig,height,"Z")
                        else:
                            children += html.H6(nothing_to_plot())
                    if 'V' in adcmap_selection:
                        logging.info("V Plane selected")
                        fig = plot_TPC_adc_map(df_dict=data.df_dict, det_keys=det_keys,
                                               plane=1,
                                               ele=apa_name,
                                               make_static=static_image,
                                               make_tp_overlay=overlay_tps,
                                               orientation=orientation,
                                               colorscale=colorscale,
                                               color_range=tr_color_range,
                                               )
                        if fig is not None:
                            children += formate_figure(fig,height,"V")
                        else:
                            children += html.H6(nothing_to_plot())
                    if 'U' in adcmap_selection:
                        logging.info("U Plane selected")
                        fig = plot_TPC_adc_map(df_dict=data.df_dict, det_keys=det_keys,
                                               plane=0, ele=apa_name,
                                               make_static=static_image,
                                               make_tp_overlay=overlay_tps,
                                               orientation=orientation, colorscale=colorscale, color_range=tr_color_range,)
                        if fig is not None:
                            children += formate_figure(fig,height,"U")
                        else:
                            children += html.H6(nothing_to_plot())

                    if adcmap_selection:
                        return(html.Div((
                            selection_line(partition,run,raw_data_file, trigger_record),
                            html.Div(children))))
                        return (html.Div(html_divs))
                    else:
                        return(html.Div(html.H6("No ADC map selected")))
                    
                else:
                    return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
