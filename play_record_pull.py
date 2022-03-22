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

project_dir = os.path.dirname(os.path.abspath(__file__))
tmp_dir = os.path.join(project_dir, 'tmp')
log_dir = os.path.join(project_dir, "logs")
log_file = os.path.join(log_dir, "play_record_pull.txt")

log = logging.getLogger('Diag')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler(filename=log_file)
fh.setLevel(logging.DEBUG)
log.addHandler(fh)


def play_record_pull_audio(ssh, host_play_audio, dut_play_audio, delay_start_sec, dst_folder, record_sec, record_channel, model):
    dut_play_path="/tmp/play.wav"
    dut_record_path = "/tmp/record.wav"
    cmd_record = "arecord -D ubnt_capture -r 16000 -c {} -f S16_LE -d {} {}".format(record_channel, record_sec, dut_record_path)
    cmd_play = "aplay -f S16_LE -r 16000 {}".format(dut_play_path)
    script_file = os.path.join(tmp_dir, "script.sh")

    if model.startswith("UVC_AI_360"):
        cmd_play = "aplay -f S16_LE -B 50000 -r 16000 {}".format(dut_play_path)

    start_time = time.time() + delay_start_sec
    th1 = PlayThread(start_time, host_play_audio)
    th1.start()

    if dut_play_audio is not None:
        with open(script_file, 'w', newline='\n') as f:
            f.write("{} &\n".format(cmd_record))
            f.write("{}\n".format(cmd_play))

        ssh.put_file(dut_play_audio, dut_play_path)
        ssh.put_file(script_file, "/tmp/script.sh")
        ssh.execmd_getmsg("chmod +x /tmp/script.sh")
        ssh.execmd_getmsg("/tmp/script.sh")

    else:
        ssh.execmd_getmsg(cmd_record)

    strftime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    filename = "{}_{}.wav".format(model, strftime)
    host_record_file = os.path.join(dst_folder, filename)

    th1.join()

    ssh.get_file(dut_record_path, host_record_file)
    log.info('pull {} to {}'.format(dut_record_path, host_record_file))
    time.sleep(0.5)

    return host_record_file


def record_pull_audio(ssh, dut_play_audio, dst_folder, record_sec, record_channel, model):
    dut_play_path="/tmp/play.wav"
    dut_record_path = "/tmp/record.wav"
    cmd_record = "arecord -D ubnt_capture -r 16000 -c {} -f S16_LE -d {} {}".format(record_channel, record_sec, dut_record_path)
    cmd_play = "aplay -f S16_LE -r 16000 {}".format(dut_play_path)
    script_file = os.path.join(tmp_dir, "script.sh")

    if model.startswith("UVC_AI_360"):
        cmd_play = "aplay -f S16_LE -B 50000 -r 16000 {}".format(dut_play_path)

    if dut_play_audio is not None:
        with open(script_file, 'w', newline='\n') as f:
            f.write("{} &\n".format(cmd_record))
            f.write("{}\n".format(cmd_play))

        ssh.put_file(dut_play_audio, dut_play_path)
        ssh.put_file(script_file, "/tmp/script.sh")
        ssh.execmd_getmsg("chmod +x /tmp/script.sh")
        ssh.execmd_getmsg("/tmp/script.sh")

    else:
        ssh.execmd_getmsg(cmd_record)

    strftime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    filename = "{}_{}.wav".format(model, strftime)
    host_record_file = os.path.join(dst_folder, filename)

    ssh.get_file(dut_record_path, host_record_file)
    log.info('pull {} to {}'.format(dut_record_path, host_record_file))
    time.sleep(0.5)

    return host_record_file


def calculate_visqol_mos(reference_file, degraded_file):
    visqol_bin = "/home/richard/workspace/audio_quality/visqol/bazel-bin/visqol"

    subprocess.run([visqol_bin,
        "--reference_file", reference_file,
        "--degraded_file", degraded_file,
        "--use_speech_mode",
        "--use_unscaled_speech_mos_mapping"])

def apply_gain(src_file, dest_file, gain_dB):
    data, rate = soundfile.read(src_file)
    gain = pow(10, gain_dB / 20)
    data *= gain
    soundfile.write(dest_file, data, rate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Play, Record, and Pull audio")
    parser.add_argument("--ip", type=str,
        default="192.168.1.156",
        help="camera ip")
    parser.add_argument("--username", type=str,
        default="ubnt",
        help="camera username, default: ubnt")
    parser.add_argument("--password", type=str,
        default="ubntubnt",
        help="camera password, default: ubntubnt")
    parser.add_argument("--duration", type=float,
        default=10.0,
        help="recording duration when source file is not specified, default: 10.0")
    parser.add_argument("--host_play_audio", type=pathlib.Path,
        default=None,
        help="source file to be played on host, default: None")
    parser.add_argument("--host_play_gain", type=float,
        default=1.0,
        help="gain to be applied on the host wav file, default: 1.0")
    parser.add_argument("--dut_play_audio", type=pathlib.Path,
        default=None,
        help="source file to be played on dut, default: None")
    parser.add_argument("--dut_play_gain", type=float,
        default=1.0,
        help="gain to be applied on the dut wave file, default: 1.0")
    parser.add_argument("--dest_folder", type=pathlib.Path,
        default=os.getcwd(),
        help="destinate folder, default: current working directory")
    parser.add_argument("-c", "--channel", type=int, default=1,
        help="channel number of recording")

    p = parser.parse_args()
    camera_ip = p.ip
    username = p.username
    password = p.password
    delay_start_sec = 0.5
    host_play_audio = p.host_play_audio
    host_play_gain = p.host_play_gain
    dut_play_audio = p.dut_play_audio
    dut_play_gain = p.dut_play_gain
    dst_folder = p.dest_folder
    record_channel = p.channel

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    record_sec = p.duration
    if dut_play_audio is not None:
        samples, sample_rate = soundfile.read(dut_play_audio)
        record_sec = int(len(samples)/sample_rate) + delay_start_sec + 1

        if dut_play_gain != 1.0:
            tmp_dut_file = os.path.join(tmp_dir, 'tmp_dut_audio.wav')
            apply_gain(dut_play_audio, tmp_dut_file, dut_play_gain)
            dut_play_audio = tmp_dut_file

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

    if host_play_audio is not None:
        if host_play_gain != 1.0:
            tmp_host_file = os.path.join(tmp_dir, 'tmp_host_audio.wav')
            apply_gain(host_play_audio, tmp_host_file, host_play_gain)
            host_play_audio = tmp_host_file

        degraded_path = play_record_pull_audio(ssh,
            host_play_audio=host_play_audio,
            dut_play_audio=dut_play_audio,
            delay_start_sec=delay_start_sec,
            dst_folder=dst_folder,
            record_sec=record_sec,
            record_channel=record_channel,
            model=model)
    else:
        degraded_path = record_pull_audio(ssh,
            dut_play_audio=dut_play_audio,
            dst_folder=dst_folder,
            record_sec=record_sec,
            record_channel=record_channel,
            model=model)
