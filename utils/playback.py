import logging
import threading
import time

import soundcard
import soundfile

log = logging.getLogger('Diag')


class PlayThread(threading.Thread):
    def __init__(self, start_time, wavefile):
        threading.Thread.__init__(self)

        self.default_speaker = soundcard.default_speaker()
        self.samples, self.sample_rate = soundfile.read(wavefile)

        self.start_time = start_time


    def play(self):
        self.default_speaker.play(self.samples, self.sample_rate)


    def run(self):
        while time.time() < self.start_time:
            time.sleep(0.1)
            log.info("wait for start playing")
            pass

        log.info('playback start')
        self.play()
        log.info('playback stop')
