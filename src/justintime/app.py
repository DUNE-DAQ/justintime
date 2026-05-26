from dash import Dash, html, dcc, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import click
import rich
import os

import logging
from rich.logging import RichHandler

# just in time  imports
from . import load_all as ld
from .cruncher.filehandle import FileHandle
from .navbar import create_navbar
#from header import create_header
from .data_cache import TriggerRecordCache


@click.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-p', '--port', type=int, default=8001)
@click.option('--tpc-channel-map', required=True, type=str)
@click.option('--pds-channel-map', type=str, default="SimplePDS")
@click.option("--template",type=click.Choice(['flatly','darkly']),default='flatly')
@click.argument('raw_data_path', type=click.Path(exists=True, file_okay=False))
def main(verbose: bool, raw_data_path: str, port: int,
         tpc_channel_map: str, pds_channel_map: str,
         template: str):

    FORMAT = "%(message)s"
    logging.basicConfig(
        level="DEBUG" if verbose else "INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

    logging.getLogger("watchdog").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("inotify").setLevel(logging.WARNING)
    logging.getLogger("inotify.adapters").setLevel(logging.WARNING)
    #logging.getLogger().setLevel(logging.INFO)
    #print(__name__)
    #logging.getLogger("__main__").setLevel(logging.DEBUG)

    theme=([dbc.themes.FLATLY if template=='flatly' else dbc.themes.DARKLY])
    rich.print("Light mode" if theme==[dbc.themes.FLATLY] else "Dark mode")
    assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    dash_app = Dash(__name__, external_stylesheets=theme, assets_folder=assets_folder)

    init_dashboard(dash_app, raw_data_path, tpc_channel_map, pds_channel_map, template)
    debug=True
    dash_app.run(debug=debug, host='0.0.0.0', port=port)


def init_dashboard(dash_app, raw_data_path, tpc_channel_map, pds_channel_map, template):
    engine = FileHandle(raw_data_path, tpc_channel_map, pds_channel_map)

    data_files = engine.list_files()
    logging.debug(data_files)
    #engine = DataManager("/tmp/", 'VDColdboxChannelMap')
    tr_cache = TriggerRecordCache(engine)
    pages, plots, ctrls = ld.get_elements(dash_app = dash_app, engine = engine, storage = tr_cache, theme=template)
    
    layout = []
    layout.append(create_navbar(pages))

    layout.append(html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.A(html.Img(src=dash_app.get_asset_url('image3.png')),style={"marginLeft":"0.8em"}),
                        html.H2("(Proto)DUNE Prompt-Feedback: Just-in-Time",style={"fontSize":"12px","marginBottom":"2em"}),
                    
                        html.H2("   "),
                       # html.H2('id=text_page'),
                        
                        # html.P( id = "pages_div",style={'fontSize': '12px '}),
                        html.Div([ctrl.div for ctrl in ctrls], id = "ctrls_div",style={'fontSize': '12px '}),
                        
                        # Change to side-by-side for mobile layout
                        html.Div(
                            className="row",
                            children=[
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        
                                    ],
                                ),
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                    ],
                                ),
                            ],
                        ),
                       
                    ],
                ),
    
                # Column for app graphs and plots
                html.Div(
                    className="eight columns div-for-charts",
                    children=[
                        
                        html.Div(
                            className="text-padding",
                            children=[
                                
                            ],
                        ),
                        html.Div([plot.div for plot in plots], id = "plots_div",style={'fontSize': '14px '})],
                
                ),
            
    ],style={"backgroundColor":["#f6f3f3e4" if template=="flatly" else "#222"]})]
))            
    
    layout.append(html.Div([dcc.Location(id='url', refresh=False),html.Div(id='page-content')])) 
    
    init_page_callback(dash_app, tr_cache)

    dash_app.layout = html.Div(layout)

def init_page_callback(dash_app, storge):
    pages, plots, ctrls = ld.get_elements()
    
    page_output=[Output("text_page","children")]
    plot_outputs = [Output(plot.id, "style") for plot in plots]
    ctrl_outputs = [Output(ctrl.id, "style") for ctrl in ctrls]

    @dash_app.callback(Output("01_clickable_title_ctrl","children"),[Input('url', 'pathname')])

    def show_page(pathname):
        pages, plots, ctrls = ld.get_elements()
        for page in pages:
            
            if pathname:

                if f"/{page.id}" in pathname or pathname=="/":

                    return([page.name])
                 
    @dash_app.callback(*ctrl_outputs,*plot_outputs,[Input('url', 'pathname')])
    
    def page_button_callback(pathname):

        pages, plots, ctrls = ld.get_elements()
        style_list = [{"display":"none"} for _ in range(len(plots)+len(ctrls))]

        for page in pages:
            
            if pathname:
                
                if f"/{page.id}" in pathname or pathname=="/":
                    page_output=page.name
                    return(calculate_page_style_list(page, plots, ctrls, style_list, storge))
                    
        return(style_list)    


    @dash_app.callback([Output("plot_description","children")],[Input('url', 'pathname')])
    
    def show_description(pathname):
        pages, plots, ctrls = ld.get_elements()
        for page in pages:
            
            if pathname:
                
                if f"/{page.id}" in pathname or pathname=="/":
                    
                    return([page.text])
          
def calculate_page_style_list(page, plots, ctrls, style_list, storge):
    needed_plots = []
    needed_ctrls = []
    for plot_n, plot in enumerate(plots):
        if plot.id in page.plots:
            needed_plots.append(plot.id)
            style_list[len(ctrls)+plot_n] = plot.display
            for ctrl in ctrls:
                if (ctrl.id in plot.ctrls) and not (ctrl.id in needed_ctrls):
                    needed_ctrls.append(ctrl.id)
    storge.update_shown_plots(needed_plots)
    needed_ctrls = get_ctrl_dependancies(ctrls,needed_ctrls)

    for ctrl_n, ctrl in enumerate(ctrls):
        if ctrl.id in needed_ctrls:
            style_list[ctrl_n] = ctrl.display
    return(style_list)

def get_ctrl_dependancies(ctrls,needed_ctrls):
    changed = True
    while changed:
        changed = False
        for ctrl_out in ctrls:
            if ctrl_out.id in needed_ctrls:
                for ctrl_in in ctrls:
                    if (ctrl_in.id in ctrl_out.ctrls) and not (ctrl_in.id in needed_ctrls):
                        needed_ctrls.append(ctrl_in.id)
                        changed = True
    return(needed_ctrls)

if __name__ == "__main__":

    main()
    
