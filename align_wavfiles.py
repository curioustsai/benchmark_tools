import os
import argparse
import soundfile
import pathlib
import logging
from glob import glob
from utils.audio import xcorr, align_wav

project_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(project_dir, "logs")

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "align_wavfiles.txt")

log = logging.getLogger('Diag')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler(filename=log_file)
fh.setLevel(logging.DEBUG)
log.addHandler(fh)


def main():
    targ = os.path.join(os.path.curdir,
                               "source_file",
                               "Dyna-Src_P835_4_sentences_4convergence_16000Hz.wav")

    parser = argparse.ArgumentParser(description="Align audio wavfiles")
    parser.add_argument("--target_file", type=pathlib.Path,
                        default=targ,
                        help="target for alignment")
    parser.add_argument("--input_file", type=pathlib.Path,
                        default=None,
                        help="source for alignment")
    parser.add_argument("--output_file", type=pathlib.Path,
                        default=None,
                        help="output file after alignment")
    parser.add_argument("--batch_input_folder", type=pathlib.Path,
                        default=None,
                        help="batch input folder for alignment")
    parser.add_argument("--batch_output_folder", type=pathlib.Path,
                        default=None,
                        help="batch ouptut folder for alignment")

    parse_value = parser.parse_args()
    target_file = parse_value.target_file
    input_file = parse_value.input_file
    output_file = parse_value.output_file
    batch_input_folder = parse_value.batch_input_folder
    batch_output_folder = parse_value.batch_output_folder

    if not os.path.exists(target_file):
        print("The target file: {} doesn't exist".format(target_file))
        return

    if input_file is not None and os.path.exists(input_file):
        target, fs_t = soundfile.read(target_file)
        source, fs_i = soundfile.read(input_file)

        if fs_t != fs_i:
            print("The sample rate of {} doesnt' match with target file {}.".format(input_file, target_file))
            return

        # use small piece to align
        if len(target) > 10 * fs_t and len(source) > 10 * fs_i:
            start_sample, end_sample = 0, 10 * fs_t
            lag = xcorr(target[start_sample: end_sample], source[start_sample:end_sample])
        else:
            lag = xcorr(target, source)

        align = align_wav(source, lag, target.size)
        soundfile.write(output_file, align, fs_t)

    elif batch_input_folder is not None and os.path.exists(batch_input_folder):
        if not os.path.exists(batch_output_folder):
            os.makedirs(batch_output_folder)

        source_files = glob(os.path.join(batch_input_folder, '*.wav'))

        for source_file in source_files:
            target, fs_t = soundfile.read(target_file)
            source, fs_s = soundfile.read(source_file)

            if fs_t != fs_s:
                print("The sample rate of {} doesnt' match with target file {}.".format(source_file, target_file))
                continue

            # use small piece to align
            if len(target) > 10 * fs_t and len(source) > 10 * fs_t:
                start_sample, end_sample = 0, 10 * fs_t
                lag = xcorr(target[start_sample: end_sample], source[start_sample:end_sample])
            else:
                lag = xcorr(target, source)

            align = align_wav(source, lag, target.size)

            soundfile.write(os.path.join(batch_output_folder, os.path.basename(source_file)), align, fs_t)

if __name__ == "__main__":
    main()
