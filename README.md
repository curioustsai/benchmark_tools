# Introduction
The package of `Benchmark Tools` is a collection of useful audio tools that help your experiment smooth.

# Installation
Please install required package first
```
pip install -r requirement.txt
```

# Tools
Note: if you don't know how use each tool, please execute `python <toolname.py> -h`

## 1. Play, record pull wavefile from DUT
An tools help you play, record, and pull audio wave files from a DUT. Use `-h` for more details.

* Linux:
```
python play_record_pull.py --ip=192.168.1.238 --username=ubnt --password=ubntubnt --dut_play_audio="./source_file/SPEECHDT_602_Male.wav"
```


* Windows:
```
python play_record_pull.py --ip=192.168.1.238 --username=ubnt --password=ubntubnt --dut_play_audio=".\source_file\SPEECHDT_602_Male.wav"
```


The program will play `source_file/SPEECHDT_602_Male.wav` via default speaker of your computer, and then record on the DUT via ssh commands.
Finally, pull back the audio file under `degraded_file` folder.


## 2. Align

### Align single input file with target file

* Linux:
```
python align_wavfiles.py --target_file="./source_file/Dyna-Src_P835_4_sentences_4convergence_16000Hz.wav" --input_file="/path/to/input" --output_file="/path/to/output"
```

* Windows:
```
python align_wavfiles.py --target_file=".\source_file\Dyna-Src_P835_4_sentences_4convergence_16000Hz.wav" --input_file="\path\to\input" --output_file="\path\to\output"
```

### Batch align the input folder with target file
* Linux:
```
python align_wavfiles.py --target_file="./source_file/Dyna-Src_P835_4_sentences_4convergence_16000Hz.wav" --batch_input_folder="/path/to/input_folder" --batch_output_folder="/path/to/output_folder"
```

* Windows:
```
python align_wavfiles.py --target_file=".\source_file\Dyna-Src_P835_4_sentences_4convergence_16000Hz.wav" --batch_input_folder="\path\to\input_folder" --batch_output_folder="\path\to\output_folder"
```

## 3. Benchmark SNR
usage: benchmark_snr.py [-h] [-s SPEECH_FILE] [-d DUT_FOLDER] [-c CONFIG] [-o OUTPUT]

* Linux:
```
python benchmark_snr.py -s ./benchmark_snr_clean/SPEECHDT_602_Female_one_44100Hz.wav -d ./benchmark_snr_dut -c ./benchmark_snr_clean/timestamp.csv -o benchmark_snr_results
```

* Windows:
```
python benchmark_snr.py -s .\benchmark_snr_clean\SPEECHDT_602_Female_one_44100Hz.wav -d .\benchmark_snr_dut -c .\benchmark_snr_clean\timestamp.csv -o benchmark_snr_results
```

## 4. Echo Return Loss Energy (ERLE) plotter
usage: erle_plotter.py [-h] [-f FAREND] [-n NEAREND] [-p PROCESSED]

* Linux:
```
python erle_plotter.py -f benchmark_erle/DoubleTestSignal-far_end_44100.wav -n benchmark_erle/DoubleTestSignal-near_end_44100.wav -p benchmark_erle/TouchMax_75dBC_SPK79dBC@50cm-2.wav
```
* Windows:
```
python erle_plotter.py -f benchmark_erle\DoubleTestSignal-far_end_44100.wav -n benchmark_erle\DoubleTestSignal-near_end_44100.wav -p benchmark_erle\TouchMax_75dBC_SPK79dBC@50cm-2.wav
```
![ERLR example](./images/erle_example.png)

## 5. Root Mean Square (RMS)
usage: rms [-h] [-v] [-f FRAME_SIZE] file [file ...]

Calculate the rms for the entire wave file
---
* Linux:
```
python rms benchmark_erle/DoubleTestSignal-far_end_44100.wav
```
* Windows:
```
python rms benchmark_erle\DoubleTestSignal-far_end_44100.wav
```
* result:
```
[rms] benchmark_erle/DoubleTestSignal-far end_44100.wav: -23.759493494843756
```

Visualize the rms versus time
---
* Linux:
```
python rms -v benchmark_erle/DoubleTestSignal-far_end_44100.wav
```
* Windows:
```
python rms -v benchmark_erle\DoubleTestSignal-far_end_44100.wav
```
![RMS example](./images/rms_level.png)
