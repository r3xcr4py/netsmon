import os
from datetime import datetime

import pandas as pd
import yaml
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import HoverTool
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.plotting import figure, output_file, show
from rich import print

OUTPUT_DIR = "./netsmon_data/"
VISUALIZATIONS_OUTPUT_DIR = f"{OUTPUT_DIR}visualizations"
MEASUREMENTS_FILE = f"{OUTPUT_DIR}measurements.yaml"

def read_measurements(filepath):
    if not os.path.exists(filepath):
        print("[bold red]Measurements file not found.[/bold red]")
        exit(1)

    with open(filepath) as f:
        measurements = yaml.safe_load(f)

    if measurements == None or len(measurements) == 0:
        print("[bold red]Measurements file is empty.[/bold red]")
        exit()
    elif len(measurements) == 1:
        print("[bold red]Can't visualize single measurement.[/bold red]")
        exit()
        
    return measurements

def visualize_measurements(filepath=MEASUREMENTS_FILE, theme="dark_minimal"):
    measurements = read_measurements(filepath)

    measurements = pd.DataFrame(measurements)
    measurements['timestamp'] = pd.to_datetime(measurements['timestamp'], unit='s')
    measurements.set_index("timestamp", inplace=True)

    # convert bits to megabits
    measurements['download_speed'] /= 1e6
    measurements['upload_speed'] /= 1e6
    measurements["download_speed"].round(3)
    measurements["upload_speed"].round(3)

    curdoc().theme = theme

    datetime_formatter = DatetimeTickFormatter(
        days="%Y-%m-%d %H:%M",
        months="%Y-%m-%d %H:%M",
        hours="%Y-%m-%d %H:%M",
        minutes="%Y-%m-%d %H:%M"
    )

    p1 = figure(title="NetSpeedMonitor", x_axis_label="Date",
            y_axis_label="Speed (Mb/s)", x_axis_type="datetime")

    p1.line(measurements.index, measurements["download_speed"],
        color="blue", line_width=2, legend_label="Download", name="Download Speed")

    p1.line(measurements.index, measurements["upload_speed"],
        color="red", line_width=2, legend_label="Upload", name="Upload Speed")

    p1.add_tools(HoverTool(
        tooltips=[
            ("Title", "$name"),
            ("Date", "@x{%F %T}"),
            ("Speed", "@y Mb/s"),
        ],
        formatters={
            "@x": "datetime"
        }))

    p1.legend.click_policy = "hide"
    p1.xaxis.formatter = datetime_formatter

    p2 = figure(title="NetSpeedMonitor", x_axis_label="Date",
                y_axis_label="Latency (ms)", x_axis_type="datetime")

    p2.line(measurements.index, measurements["latency"],
            legend_label="Latency", name="Latency", color="green", line_width=2)

    p2.add_tools(HoverTool(
        tooltips=[
            ("Title", "$name"),
            ("Date", "@x{%F %T}"),
            ("Latency", "@y ms")
        ],
        formatters={
            "@x": "datetime"
        }))

    p2.xaxis.formatter = datetime_formatter

    now = datetime.now()

    output_filename = f"{now.strftime('%Y%m%d%H%M%S')}.html"

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    
    if not os.path.exists(VISUALIZATIONS_OUTPUT_DIR):
        os.mkdir(VISUALIZATIONS_OUTPUT_DIR)

    output_file(f"{VISUALIZATIONS_OUTPUT_DIR}/{output_filename}")
    
    show(column(p1, p2, sizing_mode="stretch_width"))
