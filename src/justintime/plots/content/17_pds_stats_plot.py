from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from dash import dash_table
from plotly.subplots import make_subplots
import numpy as np
from ... plotting_functions import add_dunedaq_annotation, selection_line,nothing_to_plot
from .. import plot_class
import logging


def return_obj(dash_app, engine, storage,theme):
    plot_id = "17_pds_stats_plot"
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
        #State("21_tp_multiplicity_ctrl","value"),
        State(plot_id, "children")
    )

    def plot_pds_stats_graph(n_clicks,refresh, trigger_record,partition,run,raw_data_file,original_state):

        #load_figure_template(theme)
        load_figure_template("spacelab")
        if trigger_record and raw_data_file:
            
            if plot_id in storage.shown_plots:
                try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))
                    
                logging.info(f"Trigger Time Stamp: {data.get_trigger_ts()}")
                logging.info(" ")
                logging.info("Initial Dataframe:")
                logging.info(data.df_dict)

                #if data.df_dict["trh"].size == 0:
                #
                #     return(html.Div(html.H6(nothing_to_plot())))
                    
                try: 
                    mean1, mean2, mean3 = data.get_pds_adcs_per_link("adc_mean")
                    stdv1, stdv2, stdv3 = data.get_pds_adcs_per_link("adc_rms")
                    chns1, chns2, chns3 = data.get_pds_adcs_per_link("daphne_chan")
                    #srcs1, srcs2, srcs3 = data.get_pds_adcs_per_link("src_id")
                except KeyError:
                    return( html.Div([ html.H6("No relevant PDS data found"),
                                       html.H6(nothing_to_plot())
                                    ]))
                    
                fig_std = make_subplots(rows=2, cols=1,subplot_titles=("DAPHNE ADC stats", "DAPHNE streaming channels"))
                print(stdv1)

                fig_std.add_trace(
                    go.Scattergl(x=chns1, y=mean1, mode='markers',marker=dict(color="darkblue"), name="104"), #name=f"Run {data.run}: {data.trigger}"),
                    row=1, col=1
                )

                fig_std.add_trace(
                    go.Scattergl(x=chns2, y=mean2, mode='markers',marker=dict(color="darkred"), name="105"), #name=f"Run {data.run}: {data.trigger}"),
                    row=1, col=1
                )

                fig_std.add_trace(
                    go.Scattergl(x=chns3, y=mean3, mode='markers',marker=dict(color="darkgreen"), name="107"), #name=f"Run {data.run}: {data.trigger}"),
                    row=1, col=1
                )

                fig_std.update_layout(xaxis_title="Channels",
                    legend_title="Readout endpoint",
                    title=f'DAPHNE Streaming mode check: Run {data.run}, record {data.trigger}',
                    xaxis_title_font=dict(size=18), yaxis_title_font=dict(size=18), 
                    xaxis_range=[-0.5, 40.5], height=800,
                    xaxis = dict( tickmode = 'linear',
                                    tick0 = 0,
                                    dtick = 4
                                ))
                
                fig_std.add_trace(
                    go.Scattergl(x=chns1, y=stdv1, mode='markers',marker=dict(color="darkblue"), name=""), #name=f"Run {data.run}: {data.trigger}"),
                    row=2, col=1
                )

                fig_std.add_trace(
                    go.Scattergl(x=chns2, y=stdv2, mode='markers',marker=dict(color="darkred"), name=""), #name=f"Run {data.run}: {data.trigger}"),
                    row=2, col=1
                )

                fig_std.add_trace(
                    go.Scattergl(x=chns3, y=stdv3, mode='markers',marker=dict(color="darkgreen"), name=""), #name=f"Run {data.run}: {data.trigger}"),
                    row=2, col=1
                )

                fig_std.update_yaxes(title_text="Mean ADCs", title_font=dict(size=22), row=1, col=1)
                fig_std.update_yaxes(title_text="STDev ADCs", title_font=dict(size=22), row=2, col=1)
                fig_std.update_xaxes(title_text="Channels", title_font=dict(size=22), row=1, col=1)
                fig_std.update_xaxes(title_text="Channels", range=[-0.5, 40.5], title_font=dict(size=22), row=2, col=1)


                """fig_std.update_layout(xaxis_title="Channels",
                    yaxis_title="ADC STD",
                    legend_title="Readout endpoint",
                    title=f'DAPHNE Streaming mode check: Run {data.run}, record {data.trigger}',
                    xaxis_title_font=dict(size=18), yaxis_title_font=dict(size=18), 
                    xaxis_range=[-0.5, 40.5], height=800,
                    xaxis = dict( tickmode = 'linear',
                                    tick0 = 0,
                                    dtick = 4
                                ), row=2, col=1)"""

                a = list((chns1+chns2+chns3).index)
                chn = [a[i][4] for i in range(len(a))]
                print(chn)
                counts, bins = np.histogram(chn, 41, [0, 41])
                bins = 0.5 * (bins[:-1] + bins[1:])

                #fig_std.add_trace(
                #    px.bar(x=bins, y=counts, labels={'x':'Channels', 'y':'Count'}),
                #                  row=2, col=1)
                
                #fig_std.add_trace(
                #    go.Histogram(data.df_dict[data.pdss_datkey].index[4], xbins=40, labels={'x':'Channels', 'y':'Count'}),
                #                  row=2, col=1)

                add_dunedaq_annotation(fig_std)
                fig_std.update_layout(font_family="Lato", title_font_family="Lato")
                if theme=="flatly":
                    fig_std.update_layout(plot_bgcolor='lightgrey')
                return(html.Div([html.Br(),html.H4("STD by plane"),dcc.Graph(figure=fig_std,style={"marginTop":"10px"})]))
            
            return(original_state)
        return(html.Div())
                    


