import scipy.signal
import matplotlib.pyplot as plt

def analyze_spectrum(x, fs, fftlen):
    noverlap = fftlen / 2
    freq, Pxx = signal.welch(x,                        # signal
			     fs=fs,                    # sample rate
			     nperseg=fftlen,           # segment size
			     window='hanning',         # window type to use
			     nfft=fftlen,              # num. of samples in FFT
			     detrend=False,            # remove DC part
			     scaling='spectrum',       # return power spectrum [V^2]
			     noverlap=noverlap)        # overlap between segments

    # set 0 dB to energy of sine wave with maximum amplitude
    ref = (1/np.sqrt(2)**2)   # simply 0.5 ;)
    Pxx_dB = 10 * np.log10(Pxx/ref)

    if debug_mode['analyze_spectrum']:
	plt.rcParams['figure.figsize'] = [12.4, 9.6]
	fill_to = -150 * (np.ones_like(Pxx_dB))  # anything below -150dB is irrelevant
	plt.fill_between(freq, Pxx_dB, fill_to)
	plt.xlim([freq[2], freq[-1]])
	plt.ylim([-150, 6])
	# plt.xscale('log')   # uncomment if you want log scale on x-axis
	plt.xlabel('f, Hz')
	plt.ylabel('Power spectrum, dB')
	plt.grid(True)
	plt.show()

	return freq, Pxx, Pxx_dB
