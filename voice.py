import os
import asyncio
import subprocess
from edge_tts import Communicate
from pydub import AudioSegment
import simpleaudio as sa


# Function to list only en-US and en-GB female voices
# Used to find best voice for the hostess
async def list_voices():
    voices = await edge_tts.list_voices()
    print("en-US / en-GB Female voices:\n" + "-" * 50)
    for voice in voices:
        locale = voice.get('Locale', '').lower()
        gender = voice.get('Gender', '').lower()
        if gender == 'female' and locale in ('en-us', 'en-gb'):
            print(f"Name      : {voice.get('ShortName')}")
            print(f"Locale    : {voice.get('Locale')}")
            print(f"Gender    : {voice.get('Gender')}")
            print(f"Voice Type: {voice.get('VoiceType')}")
            print(f"Friendly  : {voice.get('FriendlyName', 'N/A')}")
            print("-" * 50)

# Async speak function with internal audio playback
async def speak(text, voice="en-GB-SoniaNeural"):
    output_path = "output.mp3"
    try:
        # Generate MP3 using edge-tts
        communicate = Communicate(text=text, voice=voice)
        await communicate.save(output_path)

        # Load and play audio using pydub and simpleaudio
        sound = AudioSegment.from_file(output_path, format="mp3")
        play_obj = sa.play_buffer(
            sound.raw_data,
            num_channels=sound.channels,
            bytes_per_sample=sound.sample_width,
            sample_rate=sound.frame_rate
        )
        play_obj.wait_done()  # Wait for playback to finish

    except Exception as e:
        print(f"[Speak Error] {e}")