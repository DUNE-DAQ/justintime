from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from PIL import Image
from matplotlib.colors import Normalize
from matplotlib import cm
import numpy as np
import rich
import logging

def add_dunedaq_annotation(figure):
    figure.add_annotation(dict(font=dict(color="black",size=12),
        #x=x_loc,
        # x=1,
        # y=-0.20,
        x=1,
        y=1.14,
        showarrow=False,
        align="right",
        text='Powered by DUNE-DAQ',
        textangle=0,
        xref="paper",
        yref="paper"
        ))

def selection_line(partition,run,raw_data_file, trigger_record):
    return(html.Div([

        html.H6([f"{partition}: Run {run}, Trigger Record {trigger_record}"]),
        html.Div([
        html.B("Raw Data File: ",style={"display":"inline-block",'marginRight':"0.4rem"}),
        html.Div(raw_data_file,style={"display":"inline-block"})]),
        html.Hr()
    ]))

def make_static_img(df, zmin: int = None, zmax: int = None, title: str = "",colorscale:str="", height:int=None,orientation: str = ""):
    
    if not df.empty:
        xmin, xmax = min(df.columns), max(df.columns)
        #ymin, ymax = min(df.index), max(df.index)
        ymin, ymax = max(df.index), min(df.index)

        if orientation=="horizontal":
            col_range = list(range(ymax, ymin))
            df = df.reindex(index=col_range, fill_value=0)
            
        elif orientation=="vertical":
            col_range = list(range(xmin, xmax))
            df = df.reindex(columns=col_range, fill_value=0)

        else:
            raise ValueError(f"Unexpeced orientation value found {orientation}. Expected values [horizontal, vertical]")
        
        img_width = df.columns.size
        img_height = df.index.size

        a = df.to_numpy()
        amin = zmin if zmin is not None else np.min(a)
        amax = zmax if zmax is not None else np.max(a)

        # Some normalization from matplotlib
        col_norm = Normalize(vmin=amin, vmax=amax)
        scalarMap  = cm.ScalarMappable(norm=col_norm, cmap=colorscale )
        seg_colors = scalarMap.to_rgba(a) 
        img = Image.fromarray(np.uint8(seg_colors*255))

        # Create figure
        fig = go.Figure()

    # Add invisible scatter trace.
    # This trace is added to help the autoresize logic work.
    # We also add a color to the scatter points so we can have a colorbar next to our image
        fig.add_trace(
            go.Scatter(
                x=[xmin, xmax],
                y=[ymin, ymax],
                mode="markers",
                marker={"color":[amin, amax],
                        "colorscale":colorscale,
                        "showscale":True,
                        "colorbar":{
                            # "title":"Counts",
                            "titleside": "right"
                        },
                        "opacity": 0
                    },
                showlegend=False
            )
        )

        # Add image
        fig.update_layout(
            images=[go.layout.Image(
                x=xmin,
                sizex=xmax-xmin,
                y=ymax,
                sizey=ymax-ymin,
                xref="x",
                yref="y",
                opacity=1.0,
                layer="below",
                sizing="stretch",
                source=img)]
        )

        # Configure other layout
        fig.update_layout(
            title=title,
            xaxis=dict(showgrid=False, zeroline=False, range=[xmin, xmax]),
            yaxis=dict(showgrid=False, zeroline=False, range=[ymin, ymax]),
            #yaxis_title="Offline Channel",
            #xaxis_title="Time ticks",
            height=height)
    else:
        
        fig=go.Figure()
    # fig.show(config={'doubleClick': 'reset'})
    return fig


def make_tp_plot(df_tp, df_ta, xmin, xmax, cmin, cmax, fig_w, fig_h, info, orientation:str=""):
    rich.print("TP Dataset")
    rich.print(df_tp)
    rich.print("TA Dataset")
    rich.print(df_ta)
    if not df_tp.empty:
        if orientation=='horizontal':
            # Axes
            y_title="Offline Channel"
            x_title="Time Ticks"
            y = df_tp['channel']
            x = df_tp['time_peak']

            # Subplots
            column_widths = [0.2,0.9]
            row_heights = None
            rows=1
            cols=2
            h_col=1
            h_row=1
            s_col=2
            s_row=1



            # histogram
            h_args = dict(y=df_tp["channel"],name='channel', nbinsy=int(xmax-xmin))

        else:
            # Axes
            x_title="Offline Channel"
            y_title="Time Ticks"
            x = df_tp['channel']
            y = df_tp['time_peak']

            # Subplots
            row_heights = [0.9, 0.2]
            column_widths = None
            rows=2
            cols=1
            h_col=1
            h_row=2
            s_col=1
            s_row=1

            h_args = dict(x=df_tp["channel"],name='channel', nbinsx=int(xmax-xmin))

        # fig=go.Figure()
        fig = make_subplots(
            rows=rows, cols=cols, 
            #subplot_titles=(["Trigger Primitives"]), 
            column_widths=column_widths,
            row_heights = row_heights,
            horizontal_spacing=0.05,
            shared_yaxes=True,
            y_title=y_title,
            x_title=x_title,
        
        )
        fig.add_trace(
            go.Scattergl(
                y=y,
                x=x,
                mode='markers',name="Trigger Primitives",
                marker=dict(
                    size=10,
                    color=df_tp['adc_peak'], #set color equal to a variable
                    colorscale='Plasma', # one of plotly colorscales
                    cmin = cmin,
                    cmax = cmax,
                    showscale=True
                    ),
                ),
                row=s_row, col=s_col
            )
        if not df_ta.empty:
            traces = make_ta_overlay(df_ta, cmin, cmax, orientation)
            for t in traces:
                fig.add_trace(
                    t,
                    row=s_row, col=s_col
                )
            # for i, ta in df_ta.iterrows():
            #     time_points = [
            #                 ta['time_start'],
            #                 ta['time_start'],
            #                 ta['time_end'],
            #                 ta['time_end'],
            #                 ta['time_start']
            #             ]
            #     channel_points = [
            #                 ta['channel_start'],
            #                 ta['channel_end'],
            #                 ta['channel_end'],
            #                 ta['channel_start'],
            #                 ta['channel_start']
            #             ]
            #     fig.add_trace(
            #         go.Scatter(
            #             x= channel_points if orientation == 'vertical' else time_points, 
            #             y= time_points if orientation == 'vertical' else channel_points, 
            #             fill="toself"
            #         ),
            #         row=s_row, col=s_col

            #     )
        fig.add_trace(
            go.Histogram(**h_args), 
            row=h_row, col=h_col
        )
        
        # fig.update_yaxes(range=[xmin,xmax])
        fig.update_layout(legend=dict(yanchor="top", y=0.01, xanchor="left", x=1))

    else:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=[xmin, xmax],
                mode="markers",
            )
        )
    fig.update_layout(
        #width=fig_w,
        height=fig_h,
        yaxis = dict(autorange="reversed"),
        title_text=f"Run {info['run_number']}: {info['trigger_number']}",
        #legend=dict(x=0,y=1),
       # width=950
        )

    return fig

def make_tp_overlay(df, cmin, cmax, orientation):

    if orientation == 'horizontal':
        x_label = 'time_peak'
        y_label = 'channel'
    elif orientation == 'vertical':
        x_label = 'channel'
        y_label = 'time_peak'
    else:
        raise ValueError(f"Unexpeced orientation value found {orientation}. Expected values [horizontal, vertical]")

    if not df.empty:
        # rich.print(2.*max(df['adc_integral'])/(10**2))
        # rich.print("adc integra", max(df['adc_integral']))
        fig=go.Scattergl(
                x=df[x_label],
                y=df[y_label],
                # error_x=dict(
                #     type='data',
                #     symmetric=False,
                #     array=df['time_peak']-df["time_start"],
                #     arrayminus=df["time_over_threshold"]-(df['time_peak']-df["time_start"])
                # ),
                mode='markers', name="Trigger Primitives",
                
                marker=dict(size=df["adc_integral"],
                    sizemode='area',
                    sizeref=2.*max(df['adc_integral'])/(12**2),sizemin=3,
                    color=df['adc_peak'], #set color equal to a variable
                    colorscale="delta", # one of plotly colorscales
                    cmin = 0,
                    cmax = cmax,
                    showscale=True,colorbar=dict( x=1.12 )
                    ),
                text=[
                    f"start : {row['time_start']}<br>peak : {row['time_peak']}<br>end : {row['time_start']+row['time_over_threshold']}<br>tot : {row['time_over_threshold']}<br>offline ch: {row['channel']}<br>sum adc : {row['adc_integral']}<br>peak adc : {row['adc_peak']}"
                        for index, row in df.iterrows()
                    ],
                )   
    else:
        fig = go.Scatter()

    return fig

def make_ta_overlay(df_tas, cmin, cmax, orientation):

    traces = []
    border_time = 16
    border_channel = 0.5
    for i, ta in df_tas.iterrows():

        text=f"""
start : {ta['time_start']}
peak : {ta['time_peak']}
end : {ta['time_end']}
ch_start : {ta['channel_start']}
ch_peak: {ta['channel_peak']}
ch_end : {ta['channel_end']}
peak adc : {ta['adc_peak']}
adc_integral : {ta['adc_integral']}
""".replace('\n','<br>')


        time_points = [
                    ta['time_start']-border_time,
                    ta['time_start']-border_time,
                    ta['time_end']+border_time,
                    ta['time_end']+border_time,
                    ta['time_start']-border_time
                ]
        channel_points = [
                    ta['channel_start']-border_channel,
                    ta['channel_end']+border_channel,
                    ta['channel_end']+border_channel,
                    ta['channel_start']-border_channel,
                    ta['channel_start']-border_channel
                ]
        if orientation == 'vertical':
            x=channel_points
            y=time_points
        else:
            x=time_points
            y=channel_points

        # if orientation == 'vertical':
        #     y0=ta['time_start']
        #     y1=ta['time_end']
        #     x0=ta['channel_start']
        #     x1=ta['channel_end']            
        # else:
        #     x0=ta['time_start']
        #     x1=ta['time_end']
        #     y0=ta['channel_start']
        #     y1=ta['channel_end']

        traces.append(
            # go.layout.Shape(
            #         type="rect",
            #         x0=x0, y0=y0, x1=x1, y1=y1,
            #         line=dict(
            #             color="RoyalBlue",
            #             width=2,
            #         ),
            #         fillcolor="LightSkyBlue",
            #         opacity=0.5,
            #         layer='below'
            #     )

            go.Scatter(
                name=f"ta[{i}]",
                text=text,
                x=x, 
                y=y, 
                fill="toself",
                line=dict(
                    color="RoyalBlue",
                    width=2,
                ),
                fillcolor="LightSkyBlue",
                opacity=0.5,

            )
        )
    return traces


def make_tp_density(df,xmin, xmax,cmin,cmax,fig_w, fig_h, info):
    if not df.empty:
        # fig=go.Figure()
        fig=px.density_heatmap(df,y=df['channel'],
            x=df['time_peak'],nbinsy=200,nbinsx=200,
                z=df['adc_peak'],histfunc="count",
                color_continuous_scale="Plasma")

        fig.update_layout(
    xaxis_title="Time Ticks",
    yaxis_title="Offline Channel")

    else:
        fig = px.scatter()      
    
    fig.update_layout(
        #width=fig_w,
        height=fig_h,
        yaxis = dict(autorange="reversed"),
        title_text=f"Run {info['run_number']}: {info['trigger_number']}",
        legend=dict(x=0,y=1),
      #  width=950

        )
    fig.update_layout(font_family="Lato", title_font_family="Lato")
    return fig

def waveform_tps(fig,df,channel_num):
    if not df.empty:
        # fig=go.Figure()
        
        if channel_num in set(df['channel']):            
            
            tps=(df[df['channel'] == channel_num])
            rich.print("Dataframe used for TPs (with similar offline channels)")
            rich.print(tps)
            rich.print("TPs time over threshold (in order of appearance):")                 
            # for i in range(len(tps)):
            for index, tp in tps.iterrows():


                # tp = tps.iloc[i]
                                                                                
                time_start = tp['time_start']
                time_over_threshold = tp["time_over_threshold"]
                time_end = (tp["time_start"]+tp["time_over_threshold"])
                time_peak = tp["time_peak"]
                channel =tp["channel"]
                adc_peak = tp["adc_peak"]
                rich.print(time_over_threshold)
                                    
                fig.add_vrect(time_start, time_end, line_width=0, fillcolor="red", opacity=0.2)
                fig.add_vline(x=time_peak, line_width=1, line_dash="dash", line_color="red")    
    else:
        fig = go.Scatter()
        
    return fig

def tp_hist_for_mean_std(df, xmin, xmax, info):
    if not df.empty:
        fig=go.Histogram(x=df["channel"],name='TP Multiplicity per channel', nbinsx=int(xmax-xmin))

    else:
        fig = go.Scatter()
 

    return fig

def nothing_to_plot():

    return "Nothing to plot"
