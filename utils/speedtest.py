import math
import statistics
import time

import requests

CF_DOWNLOAD_ENDPOINT = "https://speed.cloudflare.com/__down?measId=0&bytes={}"
CF_UPLOAD_ENDPOINT = "https://speed.cloudflare.com/__up?measId=0"

REQ_SESSION = requests.Session()

def get_server_timing(server_timing: str) -> float:
	for part in server_timing.split(";"):
		if "dur=" in part:
			return float(part.split("=")[1]) / 1000

def percentile(data: list, percentile: int) -> float:
	size = len(data)
	return sorted(data)[int(math.ceil((size * percentile) / 100)) - 1]

def latency_test():
	endpoint = CF_DOWNLOAD_ENDPOINT.format(0)

	start = time.perf_counter()
	res = REQ_SESSION.get(endpoint)
	res.raise_for_status()

	total_time_taken = time.perf_counter() - start
	server_time_taken = get_server_timing(res.headers['Server-Timing'])

	return total_time_taken - server_time_taken

def upload_test(total_bytes: int):
    start = time.perf_counter()
        
    UPLOAD_HEADERS = {
        'Connection': 'keep-alive',
        'DNT': '1',
        'Content-Type': 'text/plain;charset=UTF-8',
        'Accept': '*/*'
    }
    
    res = REQ_SESSION.post(CF_UPLOAD_ENDPOINT, data=bytearray(total_bytes), headers=UPLOAD_HEADERS)
    res.raise_for_status()

    total_time_taken = time.perf_counter() - start

    # server_time_taken = get_server_timing(res.headers['Server-Timing'])

    return total_bytes, total_time_taken

def download_test(total_bytes: int):
    endpoint = CF_DOWNLOAD_ENDPOINT.format(total_bytes)
    start = time.perf_counter()

    res = REQ_SESSION.get(endpoint)
    res.raise_for_status()
    
    total_time_taken = time.perf_counter() - start
    
    content_size = len(res.content)
    
    server_time_taken = get_server_timing(res.headers['Server-Timing'])
    
    return content_size, total_time_taken - server_time_taken

def run_tests(test_type: str, bytes_to_transfer: int, iteration_count: int = 8) -> list:
    measurements = []

    for i in range(0, iteration_count):
        if test_type == "down":
            total_bytes, seconds_taken = download_test(bytes_to_transfer)
        elif test_type == "up":
            total_bytes, seconds_taken = upload_test(bytes_to_transfer)
        else:
            return measurements

        bits_per_second = (int(total_bytes) / seconds_taken) * 8
        measurements.append(bits_per_second)

    return measurements

def run_standard_test(measurement_sizes: list = None, measurement_percentile: int = 90, test_patience: int = 15) -> dict:
    if not measurement_sizes:
        measurement_sizes = [
            100_000,
		    1_000_000,
		    10_000_000,
		    25_000_000,
		    100_000_000,
		    250_000_000,
	    ]


    LATENCY_MEASUREMENTS 	= []
    DOWNLOAD_MEASUREMENTS 	= []
    UPLOAD_MEASUREMENTS 	= []

    latency_test()
    
    LATENCY_MEASUREMENTS.extend([latency_test()*1000 for i in range(20)])

    latency = percentile(LATENCY_MEASUREMENTS, 50)
    jitter = statistics.stdev(LATENCY_MEASUREMENTS)

    first_dl_test, first_ul_test = True, True
    continue_dl_test, continue_ul_test = True, True

    for i in range(len(measurement_sizes)):
        measurement = measurement_sizes[i]
        download_test_count = (-2 * i + 12)
        upload_test_count = (-2 * i + 10)
        total_download_bytes = measurement * download_test_count
        total_upload_bytes = measurement * upload_test_count

        if not first_dl_test:
            if current_down_speed_mbps * test_patience < total_download_bytes / 125000:
                continue_dl_test = False
        else:
            first_dl_test = False
		
        if continue_dl_test:
            DOWNLOAD_MEASUREMENTS += run_tests("down", measurement, download_test_count)
            current_down_speed_mbps = percentile(DOWNLOAD_MEASUREMENTS, measurement_percentile) / 1_000_000

        if not first_ul_test:
            if current_up_speed_mbps * test_patience < total_upload_bytes / 125000:
                continue_ul_test = False
        else:
            first_ul_test = False

        if continue_ul_test:
            UPLOAD_MEASUREMENTS += run_tests("up", measurement, upload_test_count)
            current_up_speed_mbps = percentile(UPLOAD_MEASUREMENTS, measurement_percentile) / 1_000_000

    download_speed	= percentile(DOWNLOAD_MEASUREMENTS, measurement_percentile)
    upload_speed	= percentile(UPLOAD_MEASUREMENTS, measurement_percentile)

    return {
        "download_measurements" : DOWNLOAD_MEASUREMENTS,
        "upload_measurements"   : UPLOAD_MEASUREMENTS,
        "latency_measurements"  : LATENCY_MEASUREMENTS,
        'download_speed'        : download_speed,
        'upload_speed'          : upload_speed,
        'latency'               : latency,
        'jitter'                : jitter
	}
