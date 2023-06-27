
import multiprocessing as mp
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import numpy as np
import librosa
import asyncio
import wave
from io import BytesIO
import os
from mpyg321.MPyg123Player import MPyg123Player # or MPyg321Player if you installed mpg321


player = MPyg123Player()
#player.pitch(0.35)

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

    def modify_audio(self):
        # set pitch to 0.7 
        wav_file = "tmp/tts.wav"
        sound = AudioSegment.from_mp3("tmp/tts.mp3")
        sound.export("tmp/tts.wav", format="wav")
        wr = wave.open(wav_file, 'r')
        par = list(wr.getparams())
        par[3] = 0
        ww = wave.open('tmp/tts.wav', 'w')
        ww.setparams(tuple(par))
        low_pitch = 0.7
        frames = wr.getnframes()
        buffer = wr.readframes(frames)
        # convert audio to numpy array
        audio_data = np.frombuffer(buffer, dtype=np.int16)
        # adjust pitch
        new_audio_data = librosa.effects.pitch_shift(audio_data, 16000, low_pitch)
        # convert back to wav file
        new_audio_data = new_audio_data.astype(np.int16)
        ww.writeframes(new_audio_data.tobytes())
        wr.close()
        ww.close()
        # play the modified audio

    
    def generateTTS(self, text):
        mp3_file = BytesIO()
        tts = gTTS(text=text, lang=self.lang, tld=self.lang);
        tts.save('tmp/tts.mp3')
        player.play_song("tmp/tts.mp3")

        # self.modify_audio()
    
    
