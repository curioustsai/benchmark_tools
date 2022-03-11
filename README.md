# Installation
Please install required package first
```
pip install -r requirement.txt
```

# Play, record pull wavefile from DUT
```
python play_record_pull.py --ip=192.168.1.238 --username=ubnt --password=ubntubnt --model="G4Pro" --source="./source_file/SPEECHDT_602_Male.wav"

```

The program will play `source_file/SPEECHDT_602_Male.wav` via default speaker of your computer, and then record on the DUT via ssh commands.
Finally, pull back the audio file under `degraded_file` folder.


# Align wavefiles
Two modes are support, single file alignment or batch alignment
## Single file alignment
```
python align_wavfiles.py --target_file="./source_file/Dyna-Src_P835_4_sentences_4convergence_16000Hz.wav" --input_file="/path/to/input" --output_file="/path/to/output"
```
## Batch alignment
```
python align_wavfiles.py --target_file="./source_file/Dyna-Src_P835_4_sentences_4convergence_16000Hz.wav" --batch_input_folder="/path/to/input_folder" --batch_output_folder="/path/to/output_folder"
```

## Benchmark SNR
usage: benchmark_snr.py [-h] [-s SPEECH_FILE] [-d DUT_FOLDER] [-c CONFIG] [-o OUTPUT]
```
python benchmark_snr.py -s ./benchmark_snr_clean/SPEECHDT_602_Female_one_44100Hz.wav -d ./benchmark_snr_dut -c ./benchmark_snr_clean/timestamp.csv -o benchmark_snr_results

```

## erle plotter
usage: erle_plotter.py [-h] [-f FAREND] [-n NEAREND] [-p PROCESSED]

```
python erle_plotter.py -f benchmark_erle/DoubleTestSignal-far\ end_44100.wav -n benchmark_erle/DoubleTestSignal-near\ end_44100.wav -p benchmark_erle/TouchMax_75dBC_SPK79dBC@50cm-2.wav
```
![ERLR example](./images/erle_example.png)


