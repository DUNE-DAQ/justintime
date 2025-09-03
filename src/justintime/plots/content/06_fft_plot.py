from dash import html, dcc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import numpy.fft as fft
import rich
import logging
import pandas as pd
from ... plotting_functions import add_dunedaq_annotation, add_runinfo_annotation, selection_line, nothing_to_plot
from .. import plot_class


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
    def plot_fft_graph(n_clicks, refresh, op_env, run, trigger_record, raw_data_file, original_state):

        load_figure_template(theme)
        if trigger_record and raw_data_file:
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))


                det_keys = [ key for key in data.df_dict if key.startswith('detw') and 'TPC' in key ]
                print(det_keys)


                # # FIXME: HORRROR!!!
                # element_id = int(elem_name[3]) #assuming APAX or CRPX

                # Find all datasets for the selected element
                # df_sel = {k:data.df_dict[k] for k in det_keys if element_id in data.df_dict[k].element.unique()}

                # if len(df_sel) == 0:
                #     raise RuntimeError(f"No dataset matching {elem_name} found")
                # elif len(df_sel) > 1:
                #     raise RuntimeError(f"Found multiple datasets matching {elem_name}")
                

                # import IPython
                # IPython.embed(colors='neutral')

                df_elems = {}
                for key in det_keys:
                    df_els = {el:df_el for el, df_el in data.df_dict[key].groupby(by='element')}
                    overlap = (set(df_elems.keys()) & set(df_els.keys()))
                    if overlap:
                        raise RuntimeError(f'Found duplicated elements in different detector datasets {overlap}')
                    df_elems.update(df_els)



                children = [
                    selection_line(op_env,run,raw_data_file, trigger_record),
                ]
                for elem_id, df in df_elems.items():
                    freqs = fft.rfftfreq(len(df.iloc[0].adcs), 512e-9)

                    df_fft = pd.DataFrame(df.groupby('plane').fft_mag.mean()).T.explode([0,1,2]).reset_index()
                    # df_fft.columns = ['Frequency', 'Plane U', 'Plane V', 'Plane Z']
                    df_fft['freq'] = freqs


                    # FIXME: hardcoded CRP
                    title=f"FFT CRP {elem_id}: Run {run}: {trigger_record}" 

                    fig = px.line(
                        df_fft.iloc[1:],
                        # x='Frequency', 
                        # y=['Plane U', 'Plane V', 'Plane Z'], 
                        x='freq', 
                        y=[0,1,2], 
                        log_y=True, 
                        title=title, 
                        labels={
                        "value": "Magnitude",
                        "freq": "Frequency (Hz)",
                        },
                    )
                    add_dunedaq_annotation(fig)
                    add_runinfo_annotation(fig, op_env, run, trigger_record)
                    fig.update_layout(font_family="Lato", title_font_family="Lato")

                    children += [
                            html.B("FFT by plane"),
                            dcc.Graph(figure=fig),     
                         ]
                return(html.Div(children))
            else:
                return(html.Div(html.H6(nothing_to_plot())))
            return(original_state)
        return(html.Div())
