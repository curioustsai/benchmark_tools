import argparse
import soundfile
import numpy as np
import matplotlib.pyplot as plt


def rms(signal, frame_size=128):
    """
    calculate rms value frame by frame
    """
    eps = 1e-10
    num_samples = len(signal)
    num_frames = int(num_samples / frame_size)

    rms = 0
    for i in range(num_frames):
        start, end = i * frame_size, (i + 1) * frame_size
        rms += np.mean(signal[start:end] ** 2)

    rms = max(rms / num_frames, eps)

    return 10 * np.log10(rms)


def convert_timestamp(timestamp):
    """
    convert timestamp to millisecond
    timestamp mm:ss.ms
    """
    timestamp = timestamp.split('.')
    mmss = timestamp[0]

    ms = 0
    if len(timestamp) > 1:
        ms = int(timestamp[1])

    mmss = mmss.split(':')
    mins = int(mmss[0])
    secs = int(mmss[1])

    secs = mins * 60 + secs
    ms = secs * 1000 + ms

    return ms


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polar Pattern")
    parser.add_argument("-f", "--filename", type=str, default=None, help="input wavefile")
    parser.add_argument("--offset", type=str, default="00:28.500", help="offset between each speech utterance")
    parser.add_argument("--duration", type=str, default="00:16.000", help="duration of each speech utterance")
    parser.add_argument("-s", "--frame_size", type=int,
                        default=256,
                        help="samples in a frame")
    parser.add_argument("-v", "--verbose", action='store_true', help="draw partition for each utterance")

    args = parser.parse_args()
    filename = args.filename
    frame_size = args.frame_size
    offset = args.offset
    duration = args.duration

    data, rate = soundfile.read(filename)
    # extract only one channel
    if len(data.shape) > 1:
        data = data[:, 0]

    timestamp1 = input("Time stamp (mm:ss.ms) for counter clockwise 180 deg:")
    timestamp1 = timestamp1.strip()
    ms1 = convert_timestamp(timestamp1)

    timestamp2 = input("Time stamp (mm:ss.ms) for counter clockwise 180 deg:")
    timestamp2 = timestamp2.strip()
    ms2 = convert_timestamp(timestamp2)

    # time stamp array 1
    rms1 = []
    offset = convert_timestamp(offset) * rate // 1000  # 0:28.271
    duration = convert_timestamp(duration) * rate // 1000  # 0:15.000
    sample_begin = ms1 * rate // 1000

    ticks_begin = []
    ticks_end = []
    for i in range(0, 18):
        sample_end = sample_begin + duration
        session = data[sample_begin:sample_end]
        rms1.append(rms(session, frame_size))
        ticks_begin.append(sample_begin)
        ticks_end.append(sample_end)
        sample_begin += offset

    # time stamp array 2, reverse order
    rms2 = []
    sample_begin = ms2 * rate // 1000

    for i in range(0, 18):
        sample_end = sample_begin + duration
        session = data[sample_begin:sample_end]
        rms2.append(rms(session, frame_size))
        ticks_begin.append(sample_begin)
        ticks_end.append(sample_end)
        sample_begin += offset

    rms2.reverse()
    rms_all = rms1 + rms2
    rms_all.append(rms1[0])
    rms_all = rms_all - rms1[0]
    indices = np.arange(0, (2 + 10/180) * np.pi, 10 / 180 * np.pi)

    if args.verbose:
        plt.plot(data)
        for b, e in zip(ticks_begin, ticks_end):
            plt.vlines(b, -1, 1, linestyles='dotted', color='g')
            plt.vlines(e, -1, 1, linestyles='dotted', color='r')

        plt.show()

    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.plot(indices, rms_all)
    ax.set_rmax(0)
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)
    ax.set_xticks(np.pi/180 * np.linspace(0, 360, 36, endpoint=False))
    plt.savefig(filename.replace('.wav', '.png'))
