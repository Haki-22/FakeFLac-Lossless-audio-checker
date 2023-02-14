# FakeFLac (Lossless audio checker)

Python GUI app used to spot fake lossless audio files through use of spectograms.

Keep in mind that what you hear should be the number one priority when dealing with audio files.

## Contains options for:

Plotting spectogram of selected audio file and its lossy compression.
Playing selected audio, its lossy compression and their difference (+- what is missing with lossy compression) through default media browser.
Save the lossy compression if needed. 
Also can convert audio into mp3 with different bitrates
Plotting a single spectogram for one audio file
Help -> How to spot fake "lossless" compression

## Requirements
python
Installation of following libraries:
- Kivy
- pydub
- scipy
- numpy
- matplotlib

Can be done by
```bash
pip install kivy pydub scipy numpy matplotlib
```

## Usage

(run the script)
Choose your adio file (works for mono and stereo now) and look at spectograms
By checking "limit to 45s" you will speed up the calculation but your data will be limited to 45 seconds.

In lossy audio files you can spot the cuttoff (for different bitrates different kHz)
If the cutoff frequency of your audio file matches its fake lossless compression you are probably dealing with a fake lossless compression
The program also calculates the most used highest frequency and displays it as a number. lossless audio file should have higher number.

By playbuttons you can play your song and its fake lossless version (If you've chosen different bitrate you can play that). 
Also their difference (note that it might not be that accurate).

If you have found a fake you can save the lossy file to save some space.

## How to spot fake lossless compression
There is no absolute way to do this without the original audio file.
One way to get closer to the answer is to look at your file, its fake lossless spectogram and compare those two.
Other apps i've come accross usually dont work. (Tried with my own fake lossless audio files that I've created for that purpose)
Refer to google for more info or look here: https://erikstechcorner.com/2020/09/how-to-check-if-your-flac-files-are-really-lossless/

## Limitations

- Tested only on my machine
- Basic GUI
- Sometimes lags when opeing audio file
- To display examples you need pictures attached to this repository
