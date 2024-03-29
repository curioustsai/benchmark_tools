import numpy as np
import librosa
import soundfile 

from scipy.signal import hilbert, correlate, correlation_lags


def downsample_16kHz(filepath):
    signals, fs = librosa.load(filepath)

    if fs != 16000:
        src_output = librosa.resample(signals, fs, 16000)
        soundfile.write(filepath.replace(".wav", "_16kHz.wav"), src_output, 16000)

def rms(signal, frame_size=128):
    eps = 1e-10
    num_samples = len(signal)
    num_frames = int(num_samples / frame_size)

    rms = 0
    for i in range(num_frames):
        start, end = i * frame_size, (i + 1) * frame_size
        rms += np.mean(signal[start:end] ** 2)

    rms = max(rms / num_frames, eps)

    return 10 * np.log10(rms)

def xcorr(signal1, signal2):
    sig1_centered = signal1 - np.mean(signal1)
    sig2_centered = signal2 - np.mean(signal2)

    sig1 = np.abs(hilbert(sig1_centered))
    sig2 = np.abs(hilbert(sig2_centered))

    corr = correlate(sig1, sig2, mode="full")
    lags = correlation_lags(sig1.size, sig2.size, mode="full")
    lag = lags[np.argmax(corr)]

    return lag


def align_wav(signal, lag, length):
    if lag < 0:
        signal = np.concatenate([signal[-lag:], np.zeros(-lag)])
    else:
        signal = np.concatenate([np.zeros(lag), signal])

    if signal.size > length:
        signal = signal[:length]
    else:
        signal = np.concatenate([signal, np.zeros(length-signal.size)])

    return signal


# if __name__ == "__main__":
#     files = ["./wav/UVC G4 Doorbell_Speech 80dB _ BG 80dB.wav",
#              "./wav/UVC G4 Doorbell_Speech 80dB _ BG 85dB.wav",
#              "./wav/UVC G4 Doorbell_Speech 80dB _ BG 90dB.wav"]
#
#     for f in files:
#         target, fs = soundfile.read("./wav/UVC G4 Doorbell_Speech 80dB.wav")
#         source, fs = soundfile.read(f)
#         lag = xcorr(target, source)
#         align = align_wav(source, lag, target.size)
#
#         start, end = int(5 * fs), int(6 *fs)
#         print("{}, rms: {:2.2f} dB".format(f, rms(align[start:end])))
#
#         soundfile.write(os.path.join("align", os.path.basename(f)), align, fs)

