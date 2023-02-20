import io
import os

#AudioHandling:
import tempfile
import pydub
import scipy.io.wavfile as wavfile
from pydub import AudioSegment
import numpy as np

#For playing audio by default browser
import subprocess
import platform
import webbrowser

global temp_file_path_of_difference, temp_file_path
temp_file_path, temp_file_path_of_difference = "", ''

def get_temp_file_path_of_difference():
    return temp_file_path_of_difference

def get_temp_file_path():
    return temp_file_path

def is_wav_to_memory(file_name: str, mp3_and_back: bool, bitrate:str, limit_to_45sec:bool, save_mp3:bool):
    """ Opens selected audio, if needed covnerts to wav in memory.

    Parameters
    ----------
    file_name : str
        Name of audio file
    mp3_and_back : bool
        True converts the audio to mp3 (to selected bitrate) and then to wav (fake lossless version)
    bitrate: str
        Sets destination bitrate
    limit_to_45sec : bool
        Takes only 45seconds of audio file
    save_mp3 : bool 
        True saves the mp3 as temp

    Returns
    -------
    Fs : int
        Number of samples per second. (common sampling rate for audio signals is 44100 Hz)
    aud : NumPy array
        Contains the audio data
    """

    def convert_to_memory(file_name):    
        """ Opens selected audio, if needed covnerts to wav in memory. """
        if file_name.endswith(".wav"):
            with open(file_name, "rb") as f:
                return f.read()
        else:
            audio = AudioSegment.from_file(file_name, format=file_name.split(".")[-1])
            with io.BytesIO() as f:
                audio.export(f, format="wav")
                f.seek(0)
                return f.read()

    def convert_to_memory_45s(file_name):   
        """ Opens 45 seconds of selected audio, if needed covnerts to wav in memory. """ 
        if file_name.endswith(".wav"):
            audio = AudioSegment.from_file(file_name, format="wav")[:45000]
            with io.BytesIO() as f:
                audio.export(f, format="wav")
                f.seek(0)
                return f.read()
        else:
            audio = AudioSegment.from_file(file_name, format=file_name.split(".")[-1])[:45000]
            with io.BytesIO() as f:
                audio.export(f, format="wav")
                f.seek(0)
                return f.read()
    
    if limit_to_45sec:
        aud_data = convert_to_memory_45s(file_name)
    else:
        aud_data = convert_to_memory(file_name)

    if mp3_and_back:
        
        def convert_to_mp3(aud_data):
            """ converts the audio to mp3 (to selected bitrate) and then to wav (fake lossless version) """
            
            audio = AudioSegment.from_file(io.BytesIO(aud_data), format="wav")
            with io.BytesIO() as f:
                audio.export(f, format="mp3", bitrate=bitrate)
                f.seek(0)
                return f.read()

        def convert_to_wav(aud_data):
            audio = AudioSegment.from_file(io.BytesIO(aud_data), format="mp3")
            new_name = "Fake-(mp3-to-wav) " + os.path.basename(file_name)
            global temp_file_path
            if save_mp3:
                with tempfile.NamedTemporaryFile(prefix=new_name, suffix=".mp3", delete=False) as d:
                    d.write(aud_data)
                    temp_file_path = d.name
                    print (temp_file_path, "Temporary mp3-to-wav")
            with io.BytesIO() as f:
                audio.export(f, format="wav")
                f.seek(0)
                return f.read()

        def to_wav_and_mp3_and_back(file_name):
            mp3_data = convert_to_mp3(aud_data)
            audio_data = convert_to_wav(mp3_data)
            return audio_data    

        aud_data= to_wav_and_mp3_and_back(aud_data)
    
    Fs, aud = wavfile.read(io.BytesIO(aud_data))

    # select left channel only
    if aud.shape[1] == 2:
        aud = aud[:,0]

    return  Fs, aud

def play_audio_by_default_browser(file_path: str):
    """ Opens default media browser for selected audio, if it fails opens in web browser 
    
    Parameters
    ----------
    file_path : str
        Name of audio file
    """
    operating_system = platform.system()
    success = False
    if operating_system == "Windows":
        try:
            os.startfile(file_path)
            success = True
        except:
            pass
    elif operating_system == "Linux":
        try:
            subprocess.run(["xdg-open", file_path], check=True)
            success = True
        except:
            pass
    elif operating_system == "Darwin":
        try:
            subprocess.run(["open", "-a", "Music", file_path], check=True)
            success = True
        except:
            pass
    if not success:
        webbrowser.open(file_path)

def difference_between_audio_files(file_name:str, limt_to_45_sec:bool):
    """ Takes audio file and its lossy conversion and combines them, combined result saves as temp file 
    
    Parameters
    ----------
    file_name : str
        Name of audio file
    limt_to_45_sec: bool
        True takes only 45s of audio
        """


    print(temp_file_path)
    print(file_name, "File name")

    new_name = "Difference between High-Low-" + os.path.basename(file_name)

    file_format = file_name.split(".")[-1]
    audio = None
    if file_format == "wav":
        audio = pydub.AudioSegment.from_wav(file_name)
    elif file_format == "mp3":
        audio = pydub.AudioSegment.from_mp3(file_name)
    elif file_format == "flac":
        audio = pydub.AudioSegment.from_file(file_name, format="flac")

    if limt_to_45_sec:
        # Get the length of the audio in milliseconds
        duration = audio.duration_seconds * 1000

        # Select the first 45 seconds of the audio
        audio = audio[:min(45000, duration)]

    mp3 = pydub.AudioSegment.from_mp3(temp_file_path)

    # Convert the MP3 to a numpy array
    mp3_array = np.array(mp3.get_array_of_samples())
    # Invert the MP3
    mp3_array = -mp3_array

    # Convert the numpy array back to an audio segment
    mp3_inverted = pydub.AudioSegment(
        mp3_array.tobytes(),
        frame_rate=mp3.frame_rate,
        sample_width=mp3.sample_width,
        channels=mp3.channels
    )

    combined = audio.overlay(mp3_inverted)

    with tempfile.NamedTemporaryFile(prefix=new_name,suffix=".mp3", delete=False) as temp:
        combined.export(temp.name, format="mp3", bitrate="320k")
        play_audio_by_default_browser(temp.name)
        print(temp.name)
        
        global temp_file_path_of_difference
        temp_file_path_of_difference = temp.name
        print(temp_file_path_of_difference)
