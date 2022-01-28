import os
import subprocess
import time
import datetime
import logging
import argparse
import pathlib
import soundfile


from utils.ssh_client import SSHClient
from utils.playback import PlayThread

log = logging.getLogger('Diag')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler(filename='log.txt')
fh.setLevel(logging.DEBUG)
log.addHandler(fh)


def play_record_pull_audio(ssh, src_file,  delay_start_sec, record_sec, model):
    start_time = time.time() + delay_start_sec
    th1 = PlayThread(start_time, src_file)
    th1.start()

    dut_wav_path = '/tmp/test.wav'
    cmd = "arecord -r 16000 -f S16_LE -d {} {}".format(record_sec,
                                                       dut_wav_path)
    ssh.execmd_getmsg(cmd)

    strftime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    filename = "{}_{}.wav".format(model, strftime)
    host_record_file = os.path.join(os.path.curdir, "degraded_file", filename)

    th1.join()
    ssh.get_file(dut_wav_path, host_record_file)
    log.info('pull {} to {}'.format(dut_wav_path, host_record_file))
    time.sleep(0.5)

    return host_record_file


def calculate_visqol_mos(reference_file, degraded_file):
    visqol_bin = "/home/richard/workspace/audio_quality/visqol/bazel-bin/visqol"

    subprocess.run([visqol_bin,
                    "--reference_file", reference_file,
                    "--degraded_file", degraded_file,
                    "--use_speech_mode",
                    "--use_unscaled_speech_mos_mapping"])


if __name__ == '__main__':
    src_file = os.path.join(os.path.curdir,
                            "source_file",
                            "SPEECHDT_602_Male.wav")

    parser = argparse.ArgumentParser(description="Play, Record, Pull audio")
    parser.add_argument("--ip", type=str,
                        default="192.168.1.238",
                        help="camera ip")
    parser.add_argument("--username", type=str,
                        default="ubnt",
                        help="camera username")
    parser.add_argument("--password", type=str,
                        default="ubntubnt",
                        help="camera password")
    parser.add_argument("--model", type=str,
                        default="G4dome",
                        help="camera model")
    parser.add_argument("--source_file", type=pathlib.Path,
                        default=src_file,
                        help="source file to be played")

    p = parser.parse_args()
    camera_ip = p.ip
    username = p.username
    password = p.password
    model = p.model
    delay_start_sec = 0.5

    samples, sample_rate = soundfile.read(src_file)
    record_sec = int(len(samples)/sample_rate) + delay_start_sec + 1

    try:
        ssh = SSHClient(host=camera_ip, port=22,
                        username=username,
                        password=password)

        log.info('ssh successfully')
    except Exception as e:
        log.info(e)
        msg = 'connect to "{}" failed...'.format(camera_ip)
        log.info(msg)
        log.info('username = {}'.format(username))
        log.info('password = {}'.format(password))
        raise Exception(msg)

    degraded_path = play_record_pull_audio(ssh,
                                           src_file=src_file,
                                           delay_start_sec=delay_start_sec,
                                           record_sec=record_sec,
                                           model=model)

    ref_file = "./source_file/SPEECHDT_602_Male_16k.wav"
    # calculate_visqol_mos(reference_file=ref_file, degraded_file=degraded_path)
