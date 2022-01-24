from dash import dcc
from dash import html
from dash.dependencies import Input, Output, ClientsideFunction

import numpy as np
import pandas as pd
import datetime
from datetime import datetime as dt
import pathlib
from os.path import splitext


def generate_tr_card(id: str, run: int, tr_num: int, date: str, filename: str):
    return html.Div(
        id=f"tr_card_{id}",
        children=[
            html.H4(f"Trigger Record {id}"),
            html.H2(f"Run: {run} Trigger: {tr_num}"),
            html.H5(f"{date}"),
            html.H6(f"{filename}"),
            ], 
        style={'display': 'inline-block', 'width': '50%'}
    )

def description_card():
    """

    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description-card",
        children=[
            html.H5("Just-in-Time"),
            html.H4("(Proto)DUNE"),
            html.H4("Prompt-Feedback"),
            html.Div(
                id="intro",
                children="Select data file and trigger record",
            ),
        ],
    )



def generate_control_card(brain):
    """

    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control-card",
        children=[
            html.P("Raw Data File A"),
            dcc.Dropdown(
                id="raw-data-file-select-A",
                # multi=True,
                options=[{'label': f, 'value':f} for f in sorted(brain.list_files(), reverse=True)]
            ),
            # html.Br(),
            html.P("Trigger Record A"),
            dcc.Dropdown(
                id="trigger-record-select-A",
                # multi=True,
            ),
            html.Br(),
            dcc.Checklist(
                id="add-second-graph-check",
                options=[{'label': 'Raw Data File Reference', 'value': 'Y'}],
                value=['Y']
            ),
            dcc.Dropdown(
                id="raw-data-file-select-B",
                # multi=True,
                options=[{'label': f, 'value':f} for f in sorted(brain.list_files(), reverse=True)]
            ),
            # html.Br(),
            html.P("Trigger Record Reference"),
            dcc.Dropdown(
                id="trigger-record-select-B",
                # multi=True,
            ),
            html.Br(),
            html.P("Plots"),
            dcc.Checklist(
                id='plot_selection',
                options=[
                    {'label': 'Mean & STD', 'value': 'Mean_STD'},
                    {'label': 'Fourier Transform', 'value': 'FFT'},
                    {'label': 'Fourier Transform Phase (22 kHz)', 'value': 'FFT_phase'},
                ],
                value=['Mean_STD', 'FFT']
            ),
            html.Br(),
            html.P("Trigger Record Display"),
            html.Div(
                'TR A planes :',
                style={'display': 'inline-block'}
            ),
            dcc.Checklist(
                id='adcmap-selection-a',
                options=[
                    {'label': 'Z', 'value': 'Z'},
                    {'label': 'V', 'value': 'V'},
                    {'label': 'U', 'value': 'U'},
               ],
                value=[],
                labelStyle={'display': 'inline-block'},
                style={'display': 'inline-block'},
            ),
            html.Br(),
            html.Div(
                'TR Reference (R) planes : ',
                style={'display': 'inline-block'}
            ),
            dcc.Checklist(
                id='adcmap-selection-b',
                options=[
                    {'label': 'Z', 'value': 'Z'},
                    {'label': 'V', 'value': 'V'},
                    {'label': 'U', 'value': 'U'},
               ],
                value=[],
                labelStyle={'display': 'inline-block'},
                style={'display': 'inline-block'},
            ),
            html.Br(),
            html.Div(
                'TR (A-R) planes : ',
                style={'display': 'inline-block'}
            ),
            dcc.Checklist(
                id='adcmap-selection-ab-diff',
                options=[
                    {'label': 'Z', 'value': 'Z'},
                    {'label': 'V', 'value': 'V'},
                    {'label': 'U', 'value': 'U'},
               ],
                value=[],
                labelStyle={'display': 'inline-block'},
                style={'display': 'inline-block'},
            ),
            html.Br(),
            html.Div(
                'TR A (Offset) planes : ',
                style={'display': 'inline-block'}
            ),
            dcc.Checklist(
                id='adcmap-selection-a-offset',
                options=[
                    {'label': 'Z', 'value': 'Z'},
                    {'label': 'V', 'value': 'V'},
                    {'label': 'U', 'value': 'U'},
               ],
                value=[],
                labelStyle={'display': 'inline-block'},
                style={'display': 'inline-block'},
            ),
            html.Br(),
            html.Div(
                'TR A (CNR) planes : ',
                style={'display': 'inline-block'}
            ),
            dcc.Checklist(
                id='adcmap-selection-a-cnr',
                options=[
                    {'label': 'Z', 'value': 'Z'},
                    {'label': 'V', 'value': 'V'},
                    {'label': 'U', 'value': 'U'},
               ],
                value=[],
                labelStyle={'display': 'inline-block'},
                style={'display': 'inline-block'},
            ),
            html.Br(),
            html.P("Color range"),
            dcc.RangeSlider(
                id='tr-color-range-slider',
                min=-1024,
                max=1024,
                step=64,
                value=[-192, 192],
                marks={ v:f"{v}" for v in range(-1024, 1025, 256) }
            ),
            html.Br(),
            html.Button('Refresh Files', id='refresh_files', n_clicks=0),
            html.Button('Plot', id='plot_button', n_clicks=0),
            html.Br(),
            html.Br(),

            html.Div(
                id="reset-btn-outer",
                children=html.Button(id="reset-btn", children="Reset", n_clicks=0),
            ),
        ],
    )

def generate(brain):
    return html.Div(
        id="app-container",
        children=[
            dcc.Location(id='url', refresh=False),
            # Left column
            html.Div(
                id="left-column",
                className="three columns",
                children=[description_card(), generate_control_card(brain)]
                + [
                    html.Div(
                        ["initial child"], id="output-clientside", style={"display": "none"}
                    )
                ],
            ),
            # Right column
            html.Div(
                id="right-column",
                className="nine columns",
                children=[
                    # Patient Volume Heatmap
                    html.Div(
                        id="plots_card",
                        children=[
    
                            html.H1("DUNE Prompt Feedback", className="display-3"),
                            html.P(
                                "Minimal plotting service to asses raw data quality just-in-time.",
                                className="lead",
                            ),
        
                        ],
                    ),
                ],
            ),
        ],
    )