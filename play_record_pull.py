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
from utils.board_info import get_model_name

log = logging.getLogger('Diag')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler(filename='log.txt')
fh.setLevel(logging.DEBUG)
log.addHandler(fh)


def play_record_pull_audio(ssh, src_file,  delay_start_sec, dst_folder, record_sec, model):
    start_time = time.time() + delay_start_sec
    th1 = PlayThread(start_time, src_file)
    th1.start()

    dut_wav_path = '/tmp/test.wav'
    cmd = "arecord -r 16000 -f S16_LE -d {} {}".format(record_sec,
        dut_wav_path)
    ssh.execmd_getmsg(cmd)

    strftime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    filename = "{}_{}.wav".format(model, strftime)
    host_record_file = os.path.join(dst_folder, filename)

    th1.join()

    ssh.get_file(dut_wav_path, host_record_file)
    log.info('pull {} to {}'.format(dut_wav_path, host_record_file))
    time.sleep(0.5)

    return host_record_file


def record_pull_audio(ssh, dst_folder, record_sec, model):
    dut_wav_path = '/tmp/test.wav'
    cmd = "arecord -r 16000 -f S16_LE -d {} {}".format(record_sec,
        dut_wav_path)
    ssh.execmd_getmsg(cmd)

    strftime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    filename = "{}_{}.wav".format(model, strftime)
    host_record_file = os.path.join(dst_folder, filename)

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
    parser = argparse.ArgumentParser(description="Play, Record, Pull audio")
    parser.add_argument("--ip", type=str,
        default="192.168.1.156",
        help="camera ip")
    parser.add_argument("--username", type=str,
        default="ubnt",
        help="camera username")
    parser.add_argument("--password", type=str,
        default="ubntubnt",
        help="camera password")
    parser.add_argument("--source_file", type=pathlib.Path,
        default=None,
        help="source file to be played")
    parser.add_argument("--dest_folder", type=pathlib.Path,
        default=os.getcwd(),
        help="source file to be played")

    p = parser.parse_args()
    camera_ip = p.ip
    username = p.username
    password = p.password
    delay_start_sec = 0.5
    src_file = p.source_file
    dst_folder = p.dest_folder

    if src_file is not None:
        samples, sample_rate = soundfile.read(src_file)
        record_sec = int(len(samples)/sample_rate) + delay_start_sec + 1
    else:
        record_sec = 10

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

    model = get_model_name(ssh)

    if src_file is not None:
        degraded_path = play_record_pull_audio(ssh,
            src_file=src_file,
            delay_start_sec=delay_start_sec,
            dst_folder=dst_folder,
            record_sec=record_sec,
            model=model)
    else:
        degraded_path = record_pull_audio(ssh,
            record_sec=record_sec,
            dst_folder=dst_folder,
            model=model)
