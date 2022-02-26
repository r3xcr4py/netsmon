import pandas as pd
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, Select
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.plotting import figure
from rich import print

OUTPUT_DIR = "./netsmon_data/"
MEASUREMENTS_FILE = f"{OUTPUT_DIR}measurements.yaml"
APP_THEME = "dark_minimal"

def set_app_theme(theme):
    global APP_THEME
    APP_THEME = theme

def set_measurements(measurements):
    global MEASUREMENTS
    MEASUREMENTS = pd.DataFrame(measurements)

    MEASUREMENTS['timestamp'] = pd.to_datetime(MEASUREMENTS['timestamp'], unit='s')
    MEASUREMENTS.set_index("timestamp", inplace=True)

    # convert bits to megabits
    MEASUREMENTS['download_speed'] /= 1e6
    MEASUREMENTS['upload_speed'] /= 1e6
    MEASUREMENTS["download_speed"] =  MEASUREMENTS["download_speed"].round(3)
    MEASUREMENTS["upload_speed"] = MEASUREMENTS["upload_speed"].round(3)

def measurements_virtualization_app(doc):
    doc.theme = APP_THEME

    datetime_formatter = DatetimeTickFormatter(
        days="%Y-%m-%d %H:%M",
        months="%Y-%m-%d %H:%M",
        hours="%Y-%m-%d %H:%M",
        minutes="%Y-%m-%d %H:%M"
    )

    autonomous_systems = list(MEASUREMENTS["as"].unique())
    AS_select = Select(title="AS", value=autonomous_systems[0], options=autonomous_systems, width=500)

    source = ColumnDataSource(data=dict(timestamp=[], download_speed=[], upload_speed=[], latency=[]))

    p1 = figure(title="NetSpeedMonitor", x_axis_label="Date",
            y_axis_label="Speed (Mb/s)", x_axis_type="datetime")

    p1.line(x="timestamp", y="download_speed", source=source, color="blue", line_width=2,
            legend_label="Download", name="Download Speed")

    p1.line(x="timestamp", y="upload_speed", source=source, color="red",
            line_width=2, legend_label="Upload", name="Upload Speed")

    p2 = figure(title="NetSpeedMonitor", x_axis_label="Date",
                y_axis_label="Latency (ms)", x_axis_type="datetime")

    p2.line(x="timestamp", y="latency", source=source, color="green",
            line_width=2, name="Latency", legend_label="Latency")

    p1_hover = HoverTool(
        tooltips=[
            ["Date", "@timestamp{%F %T}"],
            ["Download Speed", "@download_speed Mb/s"],
            ["Upload Speed", "@upload_speed Mb/s"],
        ],
        formatters={
            "@timestamp": "datetime"
        },
        line_policy="nearest"
    )

    p2_hover = HoverTool(
        tooltips=[
            ["Date", "@timestamp{%F %T}"],
            ["Latency", "@latency ms"]
        ],
        formatters={
            "@timestamp": "datetime"
        },
        line_policy="nearest"
    )

    p1.add_tools(p1_hover)
    p2.add_tools(p2_hover)

    p1.legend.click_policy = "hide"
    p1.xaxis.formatter = datetime_formatter
    p2.xaxis.formatter = datetime_formatter

    def update_source():
        download_speed = MEASUREMENTS.loc[MEASUREMENTS["as"] == AS_select.value, "download_speed"]
        upload_speed = MEASUREMENTS.loc[MEASUREMENTS["as"] == AS_select.value, "upload_speed"]
        latency = MEASUREMENTS.loc[MEASUREMENTS["as"] == AS_select.value, "latency"]
        timestamp = MEASUREMENTS.loc[MEASUREMENTS["as"] == AS_select.value].index

        source.data = {
            "timestamp": timestamp,
            "download_speed": download_speed,
            "upload_speed": upload_speed,
            "latency": latency
        }

    AS_select.on_change("value", lambda attr, old, new: update_source())

    # initial load of the data
    update_source()

    plots = column(p1, p2, sizing_mode="stretch_width")
    AS_select.width_policy = "fixed"

    doc.add_root(column(AS_select, plots, sizing_mode="stretch_width"))
