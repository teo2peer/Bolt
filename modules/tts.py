
import multiprocessing as mp
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import numpy as np
import librosa
import asyncio
import wave

class TTS(mp.Process):
    def __init__(self, tts_pipe, lang="es"):
        super().__init__()
        self.tts_pipe = tts_pipe
        self.lang = lang
        

    def run(self):
        # Loop to receive text from the main process
        # if the text is not empty, it will generate the TTS
        # if new text is received, it will overwrite the previous TTS
        text = "";
        while True:
            text = self.tts_pipe.recv()
            if text != "":
                self.generateTTS(text)
            elif text == "exit":
                break
            else:
                continue
    


    def speak(self, text):
        self.generateTTS(text)
        tts = AudioSegment.from_mp3("tmp/tts.mp3")
        # play(tts)


    def generateTTS(self, text):
        tts = gTTS(text=text, lang=self.lang);
        tts.save('tmp/tts.mp3')