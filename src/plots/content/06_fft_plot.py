from .. import plot_class
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
from dash_bootstrap_templates import load_figure_template
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State
import numpy as np
import pandas as pd
from plotting_functions import add_dunedaq_annotation, selection_line, nothing_to_plot


def return_obj(dash_app, engine, storage):
	plot_id = "06_fft_plot"
	plot_div = html.Div(id = plot_id)
	load_figure_template("COSMO")
	plot = plot_class.plot("fft_plot", plot_id, plot_div, engine, storage)
	plot.add_ctrl("04_trigger_record_select_ctrl")
	plot.add_ctrl("90_plot_button_ctrl")

	init_callbacks(dash_app, storage, plot_id)
	return(plot)

def init_callbacks(dash_app, storage, plot_id):
	@dash_app.callback(
		Output(plot_id, "children"),
		Input("90_plot_button_ctrl", "n_clicks"),
		State('04_trigger_record_select_ctrl', "value"),
		State('03_file_select_ctrl', "value"),
		State(plot_id, "children"),
	)
	def plot_fft_graph(n_clicks, trigger_record, raw_data_file, original_state):
		if trigger_record and raw_data_file:
			if plot_id in storage.shown_plots:
				data = storage.get_trigger_record_data(trigger_record, raw_data_file)
				if len(data.df)!=0:
					data.init_fft2()

					title_U=f"FFT U-plane: Run {data.info['run_number']}: {data.info['trigger_number']}" 
					title_V=f"FFT V-plane: Run {data.info['run_number']}: {data.info['trigger_number']}" 
					title_Z=f"FFT Z-plane: Run {data.info['run_number']}: {data.info['trigger_number']}" 

					fig_U = px.line(data.df_U_plane, log_y=True, title=title_U)
					add_dunedaq_annotation(fig_U)
					fig_V = px.line(data.df_V_plane, log_y=True, title=title_V)
					add_dunedaq_annotation(fig_V)
					fig_Z = px.line(data.df_Z_plane, log_y=True, title=title_Z)
					add_dunedaq_annotation(fig_Z)

					return(html.Div([
						selection_line(raw_data_file, trigger_record),
						html.B("FFT U-Plane"),
						html.Hr(),
						dcc.Graph(figure=fig_U),
						html.B("FFT V-Plane"),
						html.Hr(),
						dcc.Graph(figure=fig_V),
						html.B("FFT Z-Plane"),
						html.Hr(),
						dcc.Graph(figure=fig_Z)]))
				else:
					return(html.Div(html.H6(nothing_to_plot())))
			return(original_state)
		return(html.Div())