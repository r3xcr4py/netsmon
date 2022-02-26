#!/usr/bin/python3

import argparse
import math
import os
from datetime import datetime

import requests
import yaml
from bokeh.server.server import Server
from rich import print
from rich.console import Console
from rich.table import Table

from utils import speedtest
from utils.visualization import (measurements_virtualization_app,
                                 set_app_theme, set_measurements)

CF_METADATA_URL = "https://speed.cloudflare.com/meta"

OUTPUT_DIR = "./netsmon_data/"
MEASUREMENTS_FILE = f"{OUTPUT_DIR}measurements.yaml"

console = Console()


def best_unit(bits):
    if bits == 0:
        return "0b"
    units = ("b", "Kb", "Mb", "Gb")
    i = int(math.floor(math.log(bits, 1000)))
    p = math.pow(1000, i)
    s = round(bits / p, 2)
    return "%s %s" % (s, units[i])


def get_internet_information():
    with console.status("[bold green]Getting your internet information...[/bold green]") as status:
        info = requests.get(CF_METADATA_URL).json()

    return info

def read_measurements(filepath = MEASUREMENTS_FILE):
    if not os.path.exists(filepath):
        print("[bold red]Measurements file not found.[/bold red]")
        exit(1)

    with open(filepath) as f:
        measurements = yaml.safe_load(f)

    if measurements == None or len(measurements) == 0:
        print("[bold red]Measurements file is empty.[/bold red]")
        exit()

    return measurements

def save_measurement_data(data):
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    if os.path.exists(MEASUREMENTS_FILE):
        with open(MEASUREMENTS_FILE) as f:
            old_data = yaml.safe_load(f)
            old_data = old_data if old_data != None else []
            
        old_data.append(data)

        with open(MEASUREMENTS_FILE, 'w') as f:
            yaml.safe_dump(old_data, f, allow_unicode=True)
    else:
        with open(MEASUREMENTS_FILE, 'w') as f:
            yaml.safe_dump([data], f, allow_unicode=True)

def list_measurements():
    data = read_measurements()

    table = Table(show_header=True, header_style="bold",
                  title="Measurements", show_edge=True, show_lines=True,
                  row_styles=["green", "dim green"])

    table.add_column("Date", justify="center")
    table.add_column("IP", justify="center")
    table.add_column("AS", justify="center")
    table.add_column("Download Speed", justify="center")
    table.add_column("Upload Speed", justify="center")
    table.add_column("Latency", justify="center")

    for measurement in data:
        table.add_row(
            datetime.fromtimestamp(measurement['timestamp']).strftime("%d/%m/%Y %H:%M:%S"),
            measurement['ip'],
            measurement['as'],
            best_unit(measurement['download_speed']),
            best_unit(measurement['upload_speed']),
            str(round(measurement['latency'])) + "ms"
        )

    console.print(table)

def new_measurement():
    info = get_internet_information()

    print(f"""[reset]  IP: [bold blue]{info['clientIp']}[/bold blue]
  AS: [bold blue]AS{info['asn']} {info['asOrganization']}[/bold blue][/reset]\n""")

    data = speedtest.run_standard_test()

    now = datetime.now()

    table = Table(show_header=True, header_style="bold",
                  caption=now.strftime("%d/%m/%Y %H:%M:%S"))

    table.add_column("Download Speed", justify="center", style="bold green")
    table.add_column("Upload Speed", justify="center", style="bold green")
    table.add_column("Ping", justify="center", style="bold green")
    table.add_column("Jitter", justify="center", style="bold green")

    table.add_row(
        best_unit(data['download_speed']),
        best_unit(data['upload_speed']),
        str(round(data['latency'])) + "ms",
        str(round(data['jitter'])) + "ms"
    )

    console.print(table)

    save_measurement_data({
        'timestamp': round(now.timestamp()),
        'ip': info['clientIp'],
        'as': f"AS{info['asn']} {info['asOrganization']}",
        'download_speed': round(data['download_speed']),
        'upload_speed': round(data['upload_speed']),
        'latency': round(data['latency'])
    })


def parse_args():
    parser = argparse.ArgumentParser(
        description="Measure your internet speed. Visualize your internet speed over time."
    )

    parser.add_argument(
        "-l", "--list-measurements",
        action="store_true",
        help="List all measurements"
    )

    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Visualize your internet speed measurements"
    )
    
    parser.add_argument(
        "--theme",
        action="store",
        choices=["caliber", "dark_minimal", "light_minimal", "night_sky", "contrast"],
        default="dark_minimal",
        help="Set the visualization theme"
    )

    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.list_measurements:
        list_measurements()
    elif args.visualize:
        if args.theme:
            set_app_theme(args.theme)

        measurements = read_measurements()

        if len(measurements) == 1:
            print("[bold red]Can't visualize single measurement.[/bold red]")
            exit()

        set_measurements(measurements)

        server = Server(applications={'/': measurements_virtualization_app})
        server.start()

        print('Opening application on http://localhost:5006/')

        server.io_loop.add_callback(server.show, "/")
        server.io_loop.start()
    else:
        new_measurement()


if __name__ == "__main__":
    main()
