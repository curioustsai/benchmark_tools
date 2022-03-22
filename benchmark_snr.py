#!/home/richard/anaconda3/bin/python3
"""
Created on Mar 9, 2022

@author : Richard Tsai

"""
import os
import argparse
import pathlib
import soundfile 
import numpy as np
from utils.audio import rms, xcorr
from scipy import signal
from matplotlib import pyplot as plt

search_range_sec = 5
pilot_timestamp_start, pilot_timestamp_end = 0, 1.0

def timestamp2sec(timestamp):
    # timestamp format mm:ss.xxx
    min = float(timestamp.split(":")[0])
    sec = float(timestamp.split(":")[1])

    return min * 60 + sec

def sample2timestamp(sample, rate):
    sec = sample / rate
    min = int(sec / 60)
    sec = sec % 60
    ms = sec - int(sec)
    ms = int(ms * 1000)
    sec = int(sec)

    timestamp = "{:02d}:{:02d}.{:03d}".format(min, sec, ms)

    return timestamp

def readTimestamp(config):
    names = []
    timestamp_start = []
    timestamp_end = []

    # marker.csv foramt
    # Name	Start	Duration	Time Format	Type	Description
    with open(config, "r") as fp:
        for count, line in enumerate(fp):
            if count > 0:
                name = line.rstrip().split("\t")[0]
                start_timestamp = line.rstrip().split("\t")[1]
                duration_timestamp = line.rstrip().split("\t")[2]

                start = timestamp2sec(start_timestamp)
                duration = timestamp2sec(duration_timestamp)

                names.append(name)
                timestamp_start.append(start)
                timestamp_end.append(start + duration)

    return names, timestamp_start, timestamp_end

def plotFig(dut_data, rate, dut_timestamp_start, dut_timestamp_end, output_png):
    total_samples = len(dut_data)

    plt.rcParams['figure.figsize'] = [24.8, 19.2]

    plt.subplot(3, 1, 1)
    plt.axis([0, total_samples, -1, 1])
    plt.plot(range(total_samples), dut_data)

    for s, e in zip(dut_timestamp_start, dut_timestamp_end):
        plt.vlines([s, e], -1, 1, 'r')

    ticks_samples = dut_timestamp_start + dut_timestamp_end
    ticks_timestamps = [sample2timestamp(t, rate) for t in ticks_samples]
    plt.xticks(ticks_samples, ticks_timestamps, rotation=90)
    plt.grid()
    plt.xlabel('time')
    plt.ylabel('amplitude')

    freqs, times, Sx = signal.spectrogram(dut_data, fs=rate,
                                           window='hanning',
                                           nperseg=1024,
                                           scaling='spectrum')

    plt.subplot(3, 1, 2)
    plt.pcolormesh(times, freqs / 1000, 10 * np.log10(Sx), cmap='viridis')
    plt.ylabel('Frequecy [kHz]')
    plt.xlabel('Time [s]')

    plt.subplot(3, 1, 3)
    frame_size = 256
    total_frames = int(total_samples / frame_size)

    levels = []
    for i in range(total_frames):
        start, end = i * frame_size, (i + 1) * frame_size
        levels.append(rms(dut_data[start:end]))
    plt.plot(levels)
    plt.xlim([0, len(levels)])
    plt.ylim([-96, 0])
    ticks_sec = np.arange(0, int(total_samples / rate), 1)
    ticks_frame = ticks_sec * rate / frame_size
    plt.xticks(ticks_frame, ticks_sec)
    plt.yticks(np.arange(-96, 0, 3))
    plt.grid()
    plt.xlabel('time')
    plt.ylabel('rms (dB)')

    plt.savefig(output_png)
    plt.clf()
    # plt.show()

def main_process(speech_file, dut_file, config, output_folder, csv_file):
    speech_data, rate = soundfile.read(speech_file)
    dut_data, _ = soundfile.read(dut_file)

    # 1. align speech_file and dut_file, align by pilot tone
    start, end = int(pilot_timestamp_start * rate), int(pilot_timestamp_end * rate)
    search_start = max(0, start - search_range_sec * rate)
    search_end = min(end + search_range_sec * rate, len(dut_data))
    lag = xcorr(speech_data[start:end], dut_data[search_start:search_end])

    # 2. read timestamp from config
    names, timestamp_start, timestamp_end = readTimestamp(config)

    # 3. calculate rms of speech_file and dut_file within timestamp
    rms_list = []
    dut_timestamp_start = []
    dut_timestamp_end = []
    for s, e in zip(timestamp_start, timestamp_end):
        start, end = int(s * rate - lag), int(e * rate - lag)
        dut_timestamp_start.append(start)
        dut_timestamp_end.append(end)
        rms_list.append(rms(dut_data[start:end]))

    # 4. output csv format
    with open(csv_file, "a") as csv:
        if os.stat(csv_file).st_size == 0:
            header = "File, "
            header_rms = ""
            header_time = ""
            for name in names:
                header_rms += "{} (rms), ".format(name)
                header_time += "{} (start), {} (end), ".format(name, name)
            header += header_rms + ", " + header_time + "\n"
            csv.write(header)

        file_stat = "{}, ".format(dut_file)
        time_str = ""
        rms_str = ""
        for s, e, r in zip(dut_timestamp_start, dut_timestamp_end, rms_list):
            ss = sample2timestamp(s, rate)
            ee  = sample2timestamp(e, rate)
            time_str += "{}, {}, ".format(ss, ee)
            rms_str += "{:2.2f}, ".format(r)
        file_stat += rms_str + ", " + time_str + "\n"

        csv.write(file_stat)

    # 5. plot marker at dut file for double-confirm
    output_png = os.path.join(output_folder, os.path.basename(dut_file.replace('.wav', '.png')))
    plotFig(dut_data, rate, dut_timestamp_start, dut_timestamp_end, output_png)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A customized script for benchmark SNR experiment")
    parser.add_argument("-s", "--speech_file", type=pathlib.Path,
                        default=None,
                        help="clean speech source file")
    parser.add_argument("-d", "--dut_folder", type=pathlib.Path,
                        default=None,
                        help="DUT mic record folder")
    parser.add_argument("-c", "--config", type=pathlib.Path,
                        default=None,
                        help="timestamp config")
    parser.add_argument("-o", "--output", type=pathlib.Path,
                        default=None,
                        help="output folder")

    parse_value = parser.parse_args()
    speech_file = parse_value.speech_file
    dut_folder = parse_value.dut_folder
    config = parse_value.config
    output_folder = parse_value.output
    csv_file = os.path.join(output_folder, os.path.basename(dut_folder) + '.csv')

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    if os.path.exists(csv_file):
        os.remove(csv_file)

    for dut_file in os.listdir(dut_folder):
        dut_path = os.path.join(dut_folder, dut_file)
        main_process(speech_file, dut_path, config, output_folder, csv_file)
