#!/home/richard/anaconda3/bin/python3
"""
Created on Mar 10, 2022

@author : Richard Tsai

"""
import argparse
import soundfile 
import pathlib
import numpy as np
from matplotlib import pyplot as plt
from utils.audio import rms


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ERLE plotter")
    parser.add_argument("-f", "--farend", type=pathlib.Path,
                        default=None,
                        help="far end signal")
    parser.add_argument("-n", "--nearend", type=pathlib.Path,
                        default=None,
                        help="near end signal")
    parser.add_argument("-p", "--processed", type=pathlib.Path,
                        default=None,
                        help="processed signal")
    args = parser.parse_args()

    farend_data, rate_f = soundfile.read(args.farend)
    nearend_data, rate_n = soundfile.read(args.nearend)
    processed_data, rate_p = soundfile.read(args.processed)
    rates = np.array([rate_f, rate_n, rate_p])

    if not np.all(rates == rates[0]):
        print("not all sample rate are the same")
        print(rates)
        exit()

    rate = rates[0]
    frame_size = 256
    total_samples = min([len(farend_data), len(nearend_data), len(processed_data)])
    total_frames = int(total_samples / frame_size)

    farend_rms = []
    nearend_rms = []
    processed_rms = []

    for i in range(total_frames):
        start, end = i * frame_size, (i + 1) * frame_size
        farend_rms.append(rms(farend_data[start:end]))
        nearend_rms.append(rms(nearend_data[start:end]))
        processed_rms.append(rms(processed_data[start:end]))

    plt.rcParams['figure.figsize'] = [12.8, 9.6]

    timeticks_sec = np.arange(0, int(total_samples / rate), 1)
    timeticks_sample = timeticks_sec * rate
    timeticks_frame = timeticks_sec * rate / frame_size

    plt.subplot(2,1,1)
    plt.plot(farend_data, label='far end')
    plt.plot(nearend_data, label='near end')
    plt.plot(processed_data, label='processed')
    plt.axis([0, total_samples, -1, 1])
    plt.xticks(timeticks_sample, timeticks_sec, rotation=45)
    plt.grid()
    plt.xlabel('time (sec)')
    plt.ylabel('amplitude')
    plt.legend()

    plt.subplot(2,1,2)
    plt.plot(farend_rms, label='far end rms')
    plt.plot(nearend_rms, label='near end rms')
    plt.plot(processed_rms, label='processed rms')
    plt.xlim([0, total_frames])
    plt.ylim([-96, 0])
    plt.xticks(timeticks_frame, timeticks_sec, rotation=45)
    plt.yticks(np.arange(-96, 0, 3))
    plt.grid()
    plt.xlabel('time (sec)')
    plt.ylabel('rms (dB)')
    plt.legend()

    plt.show()

