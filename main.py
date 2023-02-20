#This program is used to spot fake lossless audio files through use of spectograms, you can play these and their difference. save the lossy compression if needed. Also you can convert audio into mp3 with different bitrate
#To use this in python u need to install following libraries: Kivy, pydub, scipy, numpy, matplotlib
#
import io
import os
import time
import gc
import atexit
#import multiprocessing as mp

#rozložte FakeFlacChecker7-final-build.py na více jednodušších modulů
#vytvořte main.py, který bude sloužit ke spuštění programu

#Graphics:
import tkinter as tk
from tkinter import filedialog
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock

#AudioHandling:
import matplotlib.pyplot as plt 
import scipy.io.wavfile as wavfile
from pydub import AudioSegment
import tempfile
import pydub
import numpy as np

#For playing audio by default browser
import subprocess
import platform
import webbrowser

from audio_handling import is_wav_to_memory, play_audio_by_default_browser, difference_between_audio_files, get_temp_file_path_of_difference, get_temp_file_path

#from memory_profiler import profile     (To see memory consumption)


class MyGridLayout(GridLayout):
    """ Devides GUI layout into 3 separate collumns and initializes widgets"""
    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)
        self.cols=3
        self.insideleft = FloatLayout(size_hint=(.7, 1))
        self.insidecenter = FloatLayout(size_hint=(1, 1))
        self.insideright = FloatLayout(size_hint=(1, 1))
        
        self.image = Image()
        self.image_fake = Image()
        self.widgetje = False
        self.file_name =""

        #Name:
        self.insideleft.add_widget(Label(text='Lossless audio checker', size_hint=(1,.1),pos_hint={'x':0, 'y':.9}, bold='text', font_size='30sp'))

        #What the program is doing:
        self.doing_text = "Choose option"   
        self.doing_label = Label(text=self.doing_text, size_hint=(.1, .1), pos_hint={'x': .0, 'y': 0}, color=(1,0,1,1))
        self.insideright.add_widget(self.doing_label)

        #Main audio compare button:
        self.Compare = Button(text="Compare audio \nwith its fake high resolution",size_hint=(.6,.1),pos_hint={'x':.1, 'y':.8})
        self.Compare.bind(on_press=self.ChooseSong)
        self.insideleft.add_widget(self.Compare)

        #For faster computation (Limit to 45s of audio data):
        self.limit_to_45 = CheckBox(size_hint=(.6, .1), pos_hint={'x': .2, 'y': .7})
        self.limit_to_45.bind(active=self.update_limit_to_45_variable)
        self.insideleft.add_widget(self.limit_to_45)
        self.limit_to_45_variable = False

        self.label = Label(text="Limit audio to 45s", size_hint=(.4, .1), pos_hint={'x': .1, 'y': .7})
        self.insideleft.add_widget(self.label)
        
        #Choose bitrate for second audio: (Compare different bitrates)
        self.bitrate_dropdown = DropDown(size_hint=(.6, .1), pos_hint={'x': .2, 'y': .6})
        bitrate_options = ["320k", "196k", "160k", "128k", "96k", "64k"]
        self.bitrate= "320k"
        for option in bitrate_options:
            btn = Button(text=option, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.bitrate_dropdown.select(btn.text))
            self.bitrate_dropdown.add_widget(btn)

        self.bitrate_dropdown.bind(on_select=self.update_selected_bitrate)
        self.dropdown_button = Button(text='Choose Bitrate\n Default=320k', size_hint=(.6, .1), pos_hint={'x': .1, 'y': .6})
        self.dropdown_button.bind(on_release=self.bitrate_dropdown.open)

        self.bitrate_dropdown.bind(on_select=lambda instance, x: setattr(self.dropdown_button, 'text', "Selected bitrate:" + x))

        self.insideleft.add_widget(self.dropdown_button)
        self.insideleft.add_widget(Label(text="To check lossless audio do not change\ndefault bitrate", size_hint=(.4,.1), pos_hint={'x': .3, 'y': .5}))
        
        #Spectogram for one file
        self.bspecto = Button(text="Open spectogram for one file", size_hint=(.6,.1),pos_hint={'x':.1, 'y':.4})
        self.bspecto.bind(on_press=self.OnlySpecButton)
        self.insideleft.add_widget(self.bspecto)

        #How to use:
        self.help = Button(text="How it works", size_hint=(.6,.1),pos_hint={'x':.1, 'y':.3})
        self.help.bind(on_press=self.show_help)
        self.insideleft.add_widget(self.help)

        #For folder, fastest computation, shows only most highest frequencies found form 14kHz:
        #self.only_max_freq_button = Button(text="Calculate only\nhighest max frequencies", size_hint=(.6,.1), pos_hint={'x':.1, 'y':.2})
        #self.only_max_freq_button.bind(on_press=self.only_max_freq)
        #self.insideleft.add_widget(self.only_max_freq_button)

        #Play High res audio:
        self.playbutton = Button(background_normal='Icons-and-pictures/icons8-play-button-circled-100.png', size_hint=(None, None), pos_hint={'x': 0, 'y': .8})
        self.playbutton.bind(on_press=self.play_song)
        self.audio_label = Label(text="Your audio file:", size_hint=(None, None), pos_hint={'x': 0.3, 'y': 0.8})
        
        #Play Fake high res audio:    (image from https://icons8.com/icon/YJ5CCqdcOBs2/play-button-circled)
        self.playbutton_fake = Button(background_normal='Icons-and-pictures/icons8-play-button-circled-100.png', size_hint=(None, None), pos_hint={'x': 0, 'y': .8},)
        self.playbutton_fake.bind(on_press=self.play_fake_song)
        self.audio_label_fake = Label(text="Converted file:", size_hint=(None, None), pos_hint={'x': 0.2, 'y': 0.8})

        #Save icon for low-quality audio
        self.save_icon = Button(background_normal='Icons-and-pictures/icons8-save-90.png', size_hint=(None, None), pos_hint={'x': 0.5, 'y': .8})
        self.save_icon.bind(on_press=self.save_mp3)

        #Play difference between high and low quality aduio:
        self.play_difference_button = Button(background_normal='Icons-and-pictures/icons8-play-button-circled-100.png', size_hint=(None, None), pos_hint={'x': 0, 'y': .1},)
        self.play_difference_button.bind(on_press=self.play_difference)
        self.play_difference_label = Label(text="Play the differnce between High-Low res audio:", size_hint=(None, None), pos_hint={'x': .4, 'y': .1})

        self.add_widget(self.insideleft)
        self.add_widget(self.insidecenter)
        self.add_widget(self.insideright)
    
    def update_doing_text(self, instance):
        """ Updates doing text (self.doing_text needs to be changed before calling) """
        self.doing_label.text=str(self.doing_text)

    def play_difference(self, instance):
        """Button func: Calls function to calculate difference between audio files and then plays it by default browser """
        self.doing_text = "Opening the difference audio, please wait"
        self.update_doing_text(self.doing_text)
        
        def calculation_callback(dt):

            temp_file_path_of_difference = get_temp_file_path_of_difference()
            if temp_file_path_of_difference != "" and os.path.exists(temp_file_path_of_difference):
                play_audio_by_default_browser(temp_file_path_of_difference)
                print(temp_file_path_of_difference)
            else:
                difference_between_audio_files(self.file_name, self.limit_to_45_variable)
        
        Clock.schedule_once(calculation_callback, 0)
        
    def update_selected_bitrate(self, instance, value):
        """ Updates bitrate if new is selected """
        if value:
            self.bitrate = value
            if self.bitrate == "320k":
                self.doing_text = "Choose audio file for lossles check"
                self.update_doing_text(self.doing_text)
            else:
                self.doing_text = "Selected bitrate:" + self.bitrate + "\nOpen new file, which will be converted to this bitrate"
                self.update_doing_text(self.doing_text)

    def play_song(self, instance):
        """Button func:  Plays selected audio """
        if self.file_name != "":
            self.doing_text = "Opening original audio"
            self.update_doing_text(self.doing_text)

            def calculation_callback(dt):
                play_audio_by_default_browser(self.file_name)
        
            Clock.schedule_once(calculation_callback, 0)
            

    def update_limit_to_45_variable(self, checkbox, value):
        """Checkbox func: Updates limit_to_45 var to True or False"""
        self.limit_to_45_variable = value
        if value:
            self.doing_text = "Limiting audio to 45seconds"
            self.update_doing_text(self.doing_text)
        else:
            self.doing_text = "Whole audio selected"
            self.update_doing_text(self.doing_text)

    def play_fake_song(self, instance):
        """Button func: plays the fake lossless version of audio """
        temp_file_path = get_temp_file_path()
        print(temp_file_path)
        if temp_file_path != "":
            self.doing_text = "Opening fake \"Lossless\" audio\nSometimes takes a little longer"
            self.update_doing_text(self.doing_text)

            def calculation_callback(dt):
                 play_audio_by_default_browser(temp_file_path)
        
            Clock.schedule_once(calculation_callback, 0)
           

    def save_mp3(self, instance):
        """ Button func: saves the lossy audio file """
        def save_mp3(temp_file_path):
            self.doing_text = "Saving lower-quiality audio"
            self.update_doing_text(self.doing_text)

            def calculation_callback(dt):
                root = tk.Tk()
                root.withdraw()

                file_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 files", "*.mp3")])
                if file_path:
                    audio = AudioSegment.from_mp3(temp_file_path)
                    audio.export(file_path, format="mp3", bitrate=self.bitrate)
                    self.doing_text = os.path.basename(file_path) + " Succesfully Saved"
                    self.update_doing_text(self.doing_text)

                else:
                    self.doing_text = "Error while saving audio"
                    self.update_doing_text(self.doing_text)
        
            Clock.schedule_once(calculation_callback, 0)    

        temp_file_path = get_temp_file_path()
        save_mp3(temp_file_path)
        
    def ChooseSong(self, instance):
        """ Button func: takes original audio, converts it into fake lossy version and spectograms """
        temp_file_path = get_temp_file_path()
        temp_file_path_of_difference = get_temp_file_path_of_difference()
        root = tk.Tk()
        root.withdraw()
        file_name = filedialog.askopenfilename(filetypes = (("Audio Files", "*.wav;*.flac;*.mp3;"), ("All Files", "*.*")))
        if file_name == "":
            self.doing_text = "No file was selected"
            self.update_doing_text(self.doing_text)
        if file_name != "":
            self.file_name = file_name
            print(self.file_name)
            self.doing_text = "Opening: " + os.path.basename(self.file_name) +" and calculating spectograms\nPlease wait"
            self.update_doing_text(self.doing_text)

            if self.widgetje:
                self.insidecenter.remove_widget(self.image)
                self.insideright.remove_widget(self.image_fake)
                self.insidecenter.remove_widget(self.max_freq_label)
                self.insideright.remove_widget(self.max_freq_label_fake)
                if temp_file_path != "" and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if temp_file_path_of_difference != "" and os.path.exists(temp_file_path_of_difference):
                        os.remove(temp_file_path_of_difference)
            if not self.widgetje:
                self.insidecenter.clear_widgets()
                self.insideright.clear_widgets()
                
                self.insidecenter.add_widget(self.playbutton)
                self.insidecenter.add_widget(self.audio_label)
                self.insideright.add_widget(self.playbutton_fake)
                self.insideright.add_widget(self.save_icon)
                self.insideright.add_widget(self.audio_label_fake)
                self.insidecenter.add_widget(self.play_difference_button)
                self.insideleft.add_widget(self.play_difference_label)
                self.insideright.add_widget(self.doing_label)

            #Kivy doesnt support piclikng objects, you would need to reconstruct this way differently
            """ spectogram_high = mp.Process(target=self.load_spectogram_high, args=(self.file_name,))
            spectogram_low = mp.Process(target=self.load_spectogram_low, args=(self.file_name,))
            spectogram_high.start()
            spectogram_low.start() """
            #

            def calculation_callback(dt):          
                start_time = time.time()
                self.load_spectogram_high(self.file_name)
                self.load_spectogram_low(self.file_name)

                end_time = time.time()
                duration = end_time - start_time
                self.doing_text = "Done, duration: " + str(int(duration)) + " seconds\nChoose an option or open new file"
                self.update_doing_text(self.doing_text)
            
            Clock.schedule_once(calculation_callback, 0)
            gc.collect()

    #@profile
    def load_spectogram_high(self, file_name):
        """Calculates the spectogram of selected audio in memory and then displays it, calculates most highest frequencies from 14000freq """
        #Load audio to memory:
        Fs, aud = is_wav_to_memory(file_name, False, self.bitrate, self.limit_to_45_variable, False)
        
        #Plot spectogram:
        powerSpectrum, frequenciesFound, time, imageAxis = plt.specgram(aud, Fs=Fs, cmap='nipy_spectral')    #'hot'    #

        #Show most used highest frequencies:
        if max(frequenciesFound) > 14000:
            n_frequencies, n_times = powerSpectrum.shape
            frequency_range = np.where((frequenciesFound >= 14000))
            max_frequencies = [frequenciesFound[np.argmax(powerSpectrum[frequency_range, i])] for i in range(n_times)]

            print("Max frequency:", max(max_frequencies) + 14000)
            max_freq_text = "Most used highest frequencies (from 14KHz+): " + str(max(max_frequencies) + 14000) + "\nThis value should be higher"
            self.max_freq_label = Label(text=max_freq_text,pos_hint={'x':.3, 'y':.23}, size_hint=(.1, .1))
            self.insidecenter.add_widget(self.max_freq_label)
        else:
            self.max_freq_label = Label(text="Too small frequencies found",pos_hint={'x':.3, 'y':.23}, size_hint=(.1, .1))
            self.insidecenter.add_widget(self.max_freq_label)

        plt.title(os.path.basename(file_name))
        plt.xlabel('Time [s]')
        plt.ylabel('Frequency [Hz]')
        
        #Save spectogram to memory and refresh memory buffer:
        buf=io.BytesIO()
        buf.flush()
        plt.savefig(buf, format="png", transparent=True)
        plt.close()
        
        buf.seek(0)

        im = CoreImage(buf, ext='png') 
        self.image = Image(texture=CoreImage(im).texture, pos_hint={'x':0, 'y':.1}, size_hint=(1, 1))
        self.insidecenter.add_widget(self.image)

        #Clear buffer: (Otherwise creates plot in older plot)
        buf.seek(0)
        buf.truncate(0)

        self.widgetje = True

    def load_spectogram_low(self, file_name):
        """Calculates the spectogram of fake lossless audio in memory and then displays it, calculates most highest frequencies from 14000freq """
        #Show most used highest frequencies:
        def show_highest_freq(powerSpectrum, frequenciesFound, frequency_range_from):
            n_frequencies, n_times = powerSpectrum.shape
            frequency_range = np.where((frequenciesFound >= frequency_range_from))
            max_frequencies = [frequenciesFound[np.argmax(powerSpectrum[frequency_range, i])] for i in range(n_times)]

            print("Max frequency:", max(max_frequencies) + frequency_range_from)
            max_freq_text = "Most used highest frequencies (from " + str(frequency_range_from)[0:2]+ "KHz+): " + str(max(max_frequencies) + frequency_range_from) + "\nThis value should be lower"
            self.max_freq_label_fake = Label(text=max_freq_text,pos_hint={'x':.35, 'y':.23}, size_hint=(.1, .1))
            self.insideright.add_widget(self.max_freq_label_fake)

        #Load audio data to memory:
        Fs, aud = is_wav_to_memory(file_name, True, self.bitrate, self.limit_to_45_variable, True)

        #Plot spectogram and save it to memory: 
        powerSpectrum, frequenciesFound, time, imageAxis =  plt.specgram(aud, Fs=Fs, cmap='nipy_spectral')    #'hot'  #

        #if different bitrate is selected, the spectrum needs to be calculated from lower highest freq.
        frequency_range_from = 14000
        if max(frequenciesFound) > 14000:
            if self.bitrate == "320k":
                show_highest_freq(powerSpectrum, frequenciesFound, frequency_range_from)
            elif self.bitrate == "196k":
                frequency_range_from = 12000
                show_highest_freq(powerSpectrum, frequenciesFound, frequency_range_from)
            elif self.bitrate =="160k":
                frequency_range_from = 10000
                show_highest_freq(powerSpectrum, frequenciesFound, frequency_range_from)
            else:
                pass
        else:
            self.max_freq_label_fake = Label(text="Too small frequencies found",pos_hint={'x':.35, 'y':.23}, size_hint=(.1, .1))
            self.insideright.add_widget(self.max_freq_label_fake)


        new_name = "Fake-(mp3-to-wav) " + os.path.basename(file_name)
        plt.title(new_name)
        plt.xlabel('Time [s]')
        plt.ylabel('Frequency [Hz]')
        
        buf=io.BytesIO()
        buf.flush()
        plt.savefig(buf, format="png", transparent=True)
        plt.close()
        
        #Add image on screen:
        buf.seek(0)
        im = CoreImage(buf, ext='png')
        self.image_fake = Image(texture=CoreImage(im).texture, pos_hint={'x':0, 'y':0.1}, size_hint=(1, 1))
        self.insideright.add_widget(self.image_fake)

        #Clear memory:
        buf.seek(0)
        buf.truncate(0)

    def only_max_freq(self, instance):
        """ Takes audio files from a folder and passes it one by one to only_max_frequencies_value """
        root = tk.Tk()
        root.withdraw()

        directory = filedialog.askdirectory()

        if directory:
            self.file_names = []
            for file_name in os.listdir(directory):
                if file_name.endswith((".wav", ".flac", ".mp3")):
                    self.file_names.append(os.path.join(directory, file_name))
            print(self.file_names)
        
            for file_name in self.file_names:
                self.only_max_frequencies_value(file_name)

    def only_max_frequencies_value(self, file_name):
        """ Calculates only the highest frequencies  (>14Khz) and prints to console """
        Fs, aud = is_wav_to_memory(file_name, False, self.bitrate, self.limit_to_45_variable, False)

        #Plot spectogram and save it to memory: 
        powerSpectrum, frequenciesFound, time, imageAxis = plt.specgram(aud, Fs=Fs)    #'hot'  #
        plt.close()

         #Show most used highest frequencies:
        n_frequencies, n_times = powerSpectrum.shape
        frequency_range = np.where((frequenciesFound >= 14000))
        max_frequencies = [frequenciesFound[np.argmax(powerSpectrum[frequency_range, i])] for i in range(n_times)]

        print("Max frequency of original file", os.path.basename(file_name), ":", max(max_frequencies) + 14000)

        Fs, aud = is_wav_to_memory(file_name, True, self.bitrate, self.limit_to_45_variable, False)

        #Plot spectogram and save it to memory: 
        powerSpectrum, frequenciesFound, time, imageAxis = plt.specgram(aud, Fs=Fs)    #'hot'  #
        plt.close()

         #Show most used highest frequencies:
        n_frequencies, n_times = powerSpectrum.shape
        frequency_range = np.where((frequenciesFound >= 14000))
        max_frequencies = [frequenciesFound[np.argmax(powerSpectrum[frequency_range, i])] for i in range(n_times)]

        print("Max frequency of its fake lossles compresion", os.path.basename(file_name), ":", max(max_frequencies) + 14000)

    def show_difference(self, instance):
        """ Button func: shows how to spot the difference (By image examples)"""
        self.insidecenter.clear_widgets()
        self.insideright.clear_widgets()
        self.insidecenter.add_widget(Label(text="Example of lossless audio: (Up to 22KHz)", pos_hint={'x':0, 'y':.8}, size_hint=(1,.1)))
        lossless = Image(source="Icons-and-pictures/Lossless-audio-example.png", pos_hint={'x':0, 'y':0}, size_hint=(1, 1))
        self.insidecenter.add_widget(lossless)

        self.insideright.add_widget(Label(text="Example of lossy compression (196k) (Up to 19KHz):", pos_hint={'x':0, 'y':.8}, size_hint=(1,.1)))
        lossy = Image(source="Icons-and-pictures/Lossy-audio-example.png", pos_hint={'x':0, 'y':0}, size_hint=(1, 1))
        self.insideright.add_widget(lossy)

        example_button = Button(text="Show me example of lossles audio check (Real flac)", pos_hint={'x':0.1, 'y':.1}, size_hint=(.8,.1))
        example_button.bind(on_press=self.show_difference_lossles)
        self.insidecenter.add_widget(example_button)

        example_button2 = Button(text="Show me example of lossy audio check (Fake flac)", pos_hint={'x':0.1, 'y':.1}, size_hint=(.8,.1))
        example_button2.bind(on_press=self.show_difference_lossy)
        self.insideright.add_widget(example_button2)

    def show_difference_lossles(self, instance):
        """ Button func: shows how lossles audio should look like (By image examples)"""
        self.insidecenter.clear_widgets()
        self.insideright.clear_widgets()
        self.insidecenter.add_widget(Label(text="Example of lossless audio check:", pos_hint={'x':0.5, 'y':.8}, size_hint=(1,.1)))
        lossless = Image(source="Icons-and-pictures/Lossless-audio-example1split1.png", pos_hint={'x':0, 'y':.0}, size_hint=(1, 1))
        self.insidecenter.add_widget(lossless)

        lossy = Image(source="Icons-and-pictures/Lossless-audio-example1split2.png", pos_hint={'x':0, 'y':0}, size_hint=(1, 1))
        self.insideright.add_widget(lossy)

        example_button = Button(text="Back", pos_hint={'x':0.8, 'y':0}, size_hint=(.4,.1))
        example_button.bind(on_press=self.show_difference)
        self.insidecenter.add_widget(example_button)
        
    def show_difference_lossy(self, instance):
        """ Button func: shows how lossy audio should look like (By image examples)"""
        self.insidecenter.clear_widgets()
        self.insideright.clear_widgets()
        self.insidecenter.add_widget(Label(text="Example of lossy (fake flac)audio check:", pos_hint={'x':0.5, 'y':.8}, size_hint=(1,.1)))
        lossless = Image(source="Icons-and-pictures/Lossy-audio-example1split1.png", pos_hint={'x':0, 'y':.0}, size_hint=(1, 1))
        self.insidecenter.add_widget(lossless)

        lossy = Image(source="Icons-and-pictures/Lossy-audio-example1split2.png", pos_hint={'x':0, 'y':0}, size_hint=(1, 1))
        self.insideright.add_widget(lossy)

        example_button = Button(text="Back", pos_hint={'x':0.8, 'y':0}, size_hint=(.4,.1))
        example_button.bind(on_press=self.show_difference)
        self.insidecenter.add_widget(example_button)

    def OnlySpecButton(self, instance):
        """ Button func: opens spectogram for one file"""
        root = tk.Tk()
        root.withdraw()
        self.file_name = filedialog.askopenfilename(filetypes = (("Audio Files", "*.mp3;*.wav;*.flac;"), ("All Files", "*.*")))
        print(self.file_name)
        
        if self.file_name != "":
            self.doing_text = "Opening spectogram for file: " + os.path.basename(self.file_name)
            self.update_doing_text(self.doing_text)
            def calculation_callback(dt):
                self.only_spectogram(self.file_name)
            Clock.schedule_once(calculation_callback, 0)

    def only_spectogram(self, file_name):
        """ Opens spectogram for one file """
        Fs, aud = is_wav_to_memory(file_name, False, self.bitrate, False, False)

        plt.specgram(aud, Fs=Fs, cmap='nipy_spectral')    #'hot'    #powerSpectrum, frequenciesFound, time, imageAxis =
        plt.title(os.path.basename(file_name))
        plt.xlabel('Time [s]')
        plt.ylabel('Frequency [Hz]')
        plt.show()

    def show_help(self, instance):
        """ Button func: Shows how it works """
        self.insidecenter.clear_widgets()
        self.insideright.clear_widgets()
        self.insideleft.remove_widget(self.play_difference_label)

        help_text = """ There is no way to check if audio is truly lossless if you do not have the original file\n
One way to determine this is by looking at the spectrogram of the file and finding the cutoff.\n\n
Some audio files have a lower cutoff frequency, but this doesn't mean they're not lossless.\n
This program compares the spectrogram of your audio file to a fake "lossless" version.\n
If there's a difference, the audio file is likely lossless.\n
Most used highest friequencies are also displayed, if these values match you are probably dealing with fake lossless compression.\n\n
Use the "Compare audio with its fake resolution" option for this. You can limit the audio to 45 seconds for faster processing.\n\n
!!Please note that changing the bitrate to lower settings won't show you if the audio is truly lossless!!\n\n
You can play both the original and the lower-quality audio and save the lower-quality audio as an MP3 file.\n
You can play the difference between those two (+- What you are missing by compressing the audio)\n\n
You can also view the spectrogram of a single file using the "Open spectrogram for one file" option.\n
\n
\n
        """
        
        example_button = Button(text="Show me example", pos_hint={'x':0.4, 'y':.1}, size_hint=(.6,.1))
        example_button.bind(on_press=self.show_difference)
        self.insidecenter.add_widget(example_button)
        
        help_label = Label(text=help_text,size_hint=(.9, .9),  pos_hint={'x': 0.3, 'y': 0.05} ) #,7 ,6

        self.insidecenter.add_widget(help_label)
        self.widgetje = False

class LosslessAudioChecker(App):
    def build(self):
        return MyGridLayout()

def remove_temp_file():
    """ Removes temporary files at exit"""
    temp_file_path = get_temp_file_path()
    temp_file_path_of_difference = get_temp_file_path_of_difference()
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    if os.path.exists(temp_file_path_of_difference):
        os.remove(temp_file_path_of_difference)


if __name__ == '__main__':
    Window.size = (1366, 768)       #1024x640, 1366x768, 1920x1080
    Window.top = 30
    Window.left = 0
    Window.minimum_height = 640

    plt.style.use('dark_background')
    plt.rcParams['text.color'] = 'white'
    
    LosslessAudioChecker().run()
    atexit.register(remove_temp_file)
