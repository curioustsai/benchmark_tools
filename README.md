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
