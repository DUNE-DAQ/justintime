from .. import ctrl_class
from dash import html, dcc
from dash.dependencies import Input, Output, State

def return_obj(dash_app, engine):
	ctrl_id = "06_adc_map_selection_ctrl"

	ctrl_div = html.Div([
		dcc.Checklist(
			id=ctrl_id,
			options=[
				{'label': 'Z', 'value': 'Z'},
				{'label': 'V', 'value': 'V'},
				{'label': 'U', 'value': 'U'},
			],
			value=[],
			labelStyle={'display': 'inline-block'},
			style={'display': 'inline-block'},
		)
	])

	ctrl = ctrl_class.ctrl("adc_map_selection", ctrl_id, ctrl_div, engine)

	return(ctrl)
