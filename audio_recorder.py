"""
Richard Tsai, April, 20th, 2022
"""
import argparse
import pyaudio
import wave
import numpy as np
import struct
from matplotlib import pyplot as plt
from matplotlib import animation

class Recorder:
    def __init__(self, rate, chunk, path):
        # format
        self.format = pyaudio.paInt16
        self.nchannels = 1
        self.rate = rate
        self.chunk = chunk
        self.path = path

        # open pyaudio stream
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            format=self.format,
            channels=self.nchannels,
            rate=self.rate,
            input=True,
            output=True,
            frames_per_buffer=self.chunk
        )

        # init wave write
        self.wf = wave.open(self.path, "wb")
        self.wf.setnchannels(self.nchannels)
        self.wf.setframerate(self.rate)
        self.wf.setsampwidth(2)

    def __del__(self):
        self.wf.close()
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    def read(self):
        data = self.stream.read(self.chunk)
        self.wf.writeframes(data)

        data_int =  struct.unpack(str(self.chunk) + 'h', data)
        data_np = np.array(data_int, dtype=np.int16)

        return data_np

global rec, chunk, num_chunk, total_samples, samples, count

def init():
    x = np.arange(0, total_samples)
    y = np.zeros(total_samples)
    line.set_data(x, y)
    return line,

def animate(i):
    global rec, samples, count
    data_np = rec.read()
    if count < num_chunk:
        start, end = count * chunk, (count + 1) * chunk
        samples[start:end] = data_np
    else:
        samples = np.concatenate((samples[chunk:], data_np))

    line.set_ydata(samples)
    count += 1

    return line, 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Recorder")
    parser.add_argument("--rate", type=int, default=48000, help="sample rate")
    parser.add_argument("--chunk", type=int, default=1024, help="the number of samples in a chunk")
    parser.add_argument("--nchunk_draw", type=int, default=100, help="the number of chunk in a draw")
    parser.add_argument("--record_path", type=str, default="record.wav", help="the path of record wav")
    args = parser.parse_args()

    rate = args.rate
    chunk = args.chunk
    num_chunk = args.nchunk_draw
    path = args.record_path
    total_samples = chunk * num_chunk

    fig = plt.figure()
    ax = plt.axes(xlim=(0, total_samples), ylim=(-32768, 32767))
    line, = ax.plot([], [], lw=2)

    xticks_lable = []
    xticks_pos = []
    for i in np.arange(0, total_samples / rate, 0.5):
        xticks_lable.append('t+' + str(i))
        xticks_pos.append(int(rate*i))

    plt.xticks(xticks_pos, xticks_lable)

    samples = np.zeros(chunk * num_chunk, dtype=np.int16)
    count = 0
    rec = Recorder(rate, chunk, path)

    animation.FuncAnimation(fig, animate, init_func=init, interval=20, blit=True)
    plt.grid()
    plt.show()

