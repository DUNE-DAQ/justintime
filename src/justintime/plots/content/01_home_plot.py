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
import rich
import logging

from ... plotting_functions import add_dunedaq_annotation, selection_line,nothing_to_plot,tp_hist_for_mean_std
from .. import plot_class

from dqmtools.dqmtools import *
from dqmtools.dqmtests import *
from rawdatautils.unpack.dataclasses import dts_to_seconds, dts_to_datetime
import dqmtools.dataframe_creator as dfc
import hdf5libs
     
def return_obj(dash_app, engine, storage,theme):
    plot_id = "01_home_plot"
    plot_div = html.Div(id = plot_id)
    plot = plot_class.plot("home_plot", plot_id, plot_div, engine, storage,theme)
    plot.add_ctrl("01_clickable_title_ctrl")
    plot.add_ctrl("07_refresh_ctrl")
    plot.add_ctrl("partition_select_ctrl")
    plot.add_ctrl("run_select_ctrl")
    plot.add_ctrl("06_trigger_record_select_ctrl")
    plot.add_ctrl("22_tests_selection_ctrl")
    plot.add_ctrl("91_run_tests_button_ctrl")
    

    init_callbacks(dash_app, storage, plot_id,theme)
    return(plot)

def init_callbacks(dash_app, storage, plot_id,theme):
    
    @dash_app.callback(
        Output(plot_id, "children"),
        #Input("90_plot_button_ctrl", "n_clicks"),
        Input("91_run_tests_button_ctrl", "n_clicks"),
        State('07_refresh_ctrl', "value"),
        State('trigger_record_select_ctrl', "value"),
        State("partition_select_ctrl","value"),
        State("run_select_ctrl","value"),
        State('file_select_ctrl', "value"),
        State('tests_selection_item_comp', "value"),
     
        State(plot_id, "children")
    )
    def plot_home_info(n_clicks,refresh, trigger_record,partition,run,raw_data_file ,original_state, tests_selection):

        load_figure_template(theme)

        if trigger_record and raw_data_file:
            
            if plot_id in storage.shown_plots:
                    try: data = storage.get_trigger_record_data(trigger_record, raw_data_file)
                    except RuntimeError: return(html.Div("Please choose both a run data file and trigger record"))

                    logging.info(f"Initial Time Stamp: {data.df_dict['frh'].window_begin_dts}")
                    logging.info(" ")
                    logging.info("Initial Dataframe:")
                    logging.info(data.df_dict['trh'].trigger_timestamp_dts)
                    
                    if data.df_dict['trh'].size != 0:

                        trigger_dts = data.df_dict["trh"].trigger_timestamp_dts
                        assert trigger_dts.size == 1, "More than one trigger record for selected"
                        
                        trigger_dts = trigger_dts.iloc[0]
                        tpc_det_name = storage.engine.det_name
                        
                        #tpc_rms_high_threshold=100
                        #tpc_rms_low_threshold=[20.,15.]
                        #tpc_det_id = 3
                        
                        """
                        Register all TPC related tests
                        """
                        dqm_test_suite = DQMTestSuite(name="WIBTests")
                        dqm_test_suite.register_test(CheckAllExpectedFragmentsTest())
                        dqm_test_suite.register_test(CheckNFrames_WIBEth())
                        dqm_test_suite.register_test(CheckTimestampDiffs_WIBEth(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_COLDDATA_Timestamp_0_Diff(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_COLDDATA_Timestamp_1_Diff(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_COLDDATA_Timestamps_Aligned(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_CRC_Err(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_Pulser(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_Calibration(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_Ready(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_Context(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_CD(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_LOL(tpc_det_name))        
                        dqm_test_suite.register_test(CheckWIBEth_Link_Valid(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_WIB_Sync(tpc_det_name))
                        dqm_test_suite.register_test(CheckWIBEth_FEMB_Sync(tpc_det_name))
                        """
                        Register all DAPHNE related tests
                        """
                        dqm_test_suite_daphne = DQMTestSuite(name="DAPHNETests")
                        dqm_test_suite_daphne.register_test(CheckTimestampsAligned(2),"CheckTimestampsAligned_PDS")
                        dqm_test_suite_daphne.register_test(CheckEmptyFragments_DAPHNE(), "CheckEmptyFragments_DAPHNE")
                        dqm_test_suite_daphne.register_test(CheckTimestampDiffs_DAPHNE())
                        dqm_test_suite_daphne.register_test(CheckADCData_DAPHNE())


                        dqm_test_suite.run_test(data.df_dict)
                        dqm_test_suite_daphne.run_test(data.df_dict)

                        results_tpc = dqm_test_suite.get_latest_results().astype(str)[["result","message","name"]]
                        results_dph = dqm_test_suite_daphne.get_latest_results().astype(str)[["result","message","name"]]
                        #results_tpc["result"] = results_tpc["result"][14:]
                        #results_dph["result"] = results_tpc["result"][14:]

                        mystyle_data_conditional=[
                                        {'if': {'filter_query': '{{result}} contains {}'.format("OK")},
                                        'backgroundColor': 'rgb(179, 226, 205)'},
                                        {'if': {'filter_query': '{{result}} contains {}'.format("WARNING")},
                                        'backgroundColor': 'rgb(253,244,152)'},
                                        {'if': {'filter_query': '{{result}} contains {}'.format("BAD")},
                                        'backgroundColor': 'rgb(251,180,174)'},
                                        {'if': {'filter_query': '{{result}} contains {}'.format("INVALID")},
                                        'backgroundColor': 'rgb(251,180,174)'},
                                        {'if': {'column_id':'{name}'},
                                         'minWidth': '120px', 'width': '120px', 'maxWidth': '120px',
                                         'font-family':'Open Sans'}
                            ]

                        #trigger info table
#                        table=pd.DataFrame({
#                            'TR Attribute': [
#                                'Run',
#                                'Trigger number',
#                                'Trigger sequence',
#                                'Trigger timestamp (dts ticks)', 
#                                'Trigger timestamp (sec from epoc)',
#                                'Trigger date',
#                                'Number of fragments',
#                                'Number of requested components',
#                                'Trigger type',
#                                'Total size (MB)'
#                            ],
#                            'Value': [
#                                data.df_dict["trh"]["run"].iloc[0],
#                                data.df_dict["trh"]["trigger"].iloc[0],
#                                data.df_dict["trh"]["sequence"].iloc[0],
#                                data.df_dict["trh"]["trigger_timestamp_dts"].iloc[0],
#                                data.df_dict["trh"]["trigger_timestamp_dts"].iloc[0]*16/1e9,
#                                data.df_dict["trh"]["trigger_time"].iloc[0],
#                                data.df_dict["trh"]["n_fragments"].iloc[0],
#                                data.df_dict["trh"]["n_requested_components"].iloc[0],
#                                data.df_dict["trh"]["trigger_type"].iloc[0],
#                                data.df_dict["trh"]["total_size_bytes"].iloc[0]/1e6
#                            ]
#                        })

                        table=data.df_dict["trh"]
                        children=([dash_table.DataTable(
                                id='table',
                                columns=[{"name": i, "id": i} for i in table.columns],
                                data=table.to_dict('records'),
                                style_header={'textAlign': 'left'},
                                style_cell={'textAlign': 'left'}
                                )
                                ])

                        children_tpc=([dash_table.DataTable(
                                    id='table_tpc',
                                    columns=[{"name": i, "id": i} for i in results_tpc.columns],
                                    data=results_tpc.to_dict('records'),
                                    style_header={'textAlign': 'left'},
                                    style_cell={'textAlign': 'left', 'height': 'auto',
                                                'minWidth': '80px', 'width': '100px', 'maxWidth': '120px',
                                                'whiteSpace': 'normal'},
                                    style_data_conditional=mystyle_data_conditional
                                    )])
                        children_dph=([ dash_table.DataTable(
                                    id='table_dph',
                                    columns=[{"name": i, "id": i} for i in results_dph.columns],
                                    data=results_dph.to_dict('records'),
                                    style_header={'textAlign': 'left'},
                                    style_cell={'textAlign': 'left', 'height': 'auto',
                                                'minWidth': '80px', 'width': '100px', 'maxWidth': '120px',
                                                'whiteSpace': 'normal'},
                                    style_data_conditional=mystyle_data_conditional
                                    )]
                                )
  
                        return(html.Div([
                                selection_line(partition,run,raw_data_file, trigger_record),
                                html.Div(children),
                                html.H4("TPC:"),
                                html.Div(children_tpc),
                                html.Hr(),
                                html.H4("DAPHNE:"),
                                html.Div(children_dph)
                                ]))
                    else:
                        return(html.Div([html.H6(nothing_to_plot())]))
            return(original_state)
        return(html.Div())
