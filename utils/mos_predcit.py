import os
import argparse
import subprocess
import sox
import csv
import numpy as np
import toml

from glob import glob
from scipy.io import wavfile
from pesq import pesq


class MosPredict():
    def __init__(self, config):
        """
        init with data path
        """
        self.config = config
        self.file_format = config['config']['format']
        self.data_path = config['data_path']
        self.models = config['config']['models']
        self.num_models = len(config['config']['models'])
        self.data_path = config['data_path']
        self.merge_dir = config['merge']['output_dir']

        self.data = list()
        self.mos_avg = dict()
        self.mos_std = dict()

        self.parse_path()

    def parse_path(self):
        """
        parse paths into a list of dict to wave path
        """
        noisy_files = glob(os.path.join(self.data_path['noisy'], self.file_format))

        for noisy_wav in noisy_files:
            unit = dict()
            basename = os.path.basename(noisy_wav)

            hyphen = '_'
            fileid_wav = hyphen.join(basename.split(hyphen)[-2:])
            clean_wav = os.path.join(self.data_path['clean'], 'clean_'+fileid_wav)
            unit['clean'] = os.path.abspath(clean_wav)
            unit['noisy'] = os.path.abspath(noisy_wav)

            for model in self.models:
                unit[model] = os.path.abspath(os.path.join(self.data_path[model], basename))

            merge_wav = os.path.abspath(os.path.join(self.merge_dir, basename))
            unit['merge'] = merge_wav

            self.data.append(unit)

    def merge_files(self):
        """
        sox combiner
        """
        channels = self.num_models + 1
        sox_combiner = sox.Combiner()
        sox_combiner.convert(samplerate=16000, n_channels=5)

        if not os.path.exists(self.merge_dir):
            os.mkdir(self.merge_dir)

        for unit in self.data:
            sox_combiner.set_input_format(['wav'] * channels)
            model_list = [unit['noisy']]
            for model in self.models:
                model_list.append(unit[model])

            sox_combiner.build(model_list, unit['merge'], 'merge')

    def calc_pesq(self):
        """
        calculate pesq wb by python pesq package
        """
        mos_avg = dict()
        mos_std = dict()

        def __calc_pesq_model(data, model):
            mos_all = list()

            for unit in data:
                reference = unit['clean']
                degraded = unit[model]

                rate, ref = wavfile.read(reference)
                _, deg = wavfile.read(degraded)

                mos = pesq(rate, ref, deg, 'wb')
                mos_all.append(mos)
            mos_avg[model] = np.mean(mos_all)
            mos_std[model] = np.std(mos_all)
            print("[PESQ] {} mean {:2.2f}, std {:2.2f}".format(model, mos_avg[model], mos_std[model]))

        self.mos_avg = mos_avg
        self.mos_std = mos_std

        models = ["noisy"]
        models.extend(self.models)

        for model in models:
            __calc_pesq_model(self.data, model)

        with open(config['pesq']['output_csv'], 'w') as results:
            for model in models:
                results.write("[PESQ] {} mean {:2.2f}, std {:2.2f}\n".format(model, mos_avg[model], mos_std[model]))

    def write_visqol_csv(self):
        """
        output visqol csv files
        """
        def __write_visqol_csv_model(data, batch_csv_path, model):
            csv_filename = batch_csv_path.replace(".csv", "_" + model + ".csv")
            with open(csv_filename, 'w') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',')
                csv_writer.writerow(['reference_file', 'degraded_file'])

                for unit in data:
                    csv_writer.writerow([unit['clean'], unit[model]])

        models = ["noisy"]
        models.extend(self.models)
        for model in models:
            __write_visqol_csv_model(self.data, self.config['visqol']['batch_csv'], model)

    def calc_visqol(self):
        visqol_bin = self.config['visqol']['visqol_bin']

        input_csvs = list()
        results_csvs = list()
        models = ["noisy"]
        models.extend(self.models)
        for model in models:
            in_csv = self.config['visqol']['batch_csv'].replace(".csv", "_" + model + ".csv")
            re_csv = self.config['visqol']['results_csv'].replace(".csv", "_" + model + ".csv")
            input_csvs.append(os.path.abspath(in_csv))
            results_csvs.append(os.path.abspath(re_csv))

        os.chdir(self.config['visqol']['visqol_dir'])
        for input_csv, results_csv in zip(input_csvs, results_csvs):
            print("input csv: {}".format(input_csv))
            print("results csv: {}".format(results_csv))
            subprocess.run([visqol_bin,
                            "--batch_input_csv", input_csv,
                            "--results_csv", results_csv,
                            "--use_speech_mode",
                            "--use_unscaled_speech_mos_mapping"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configuration", type=str, required=True, help="Config file.")
    args = parser.parse_args()

    config = toml.load(args.configuration)
    predictor = MosPredict(config)

    if config['merge']['enable']:
        predictor.merge_files()

    if config['pesq']['enable']:
        predictor.calc_pesq()

    if config['visqol']['enable']:
        predictor.write_visqol_csv()
        predictor.calc_visqol()
