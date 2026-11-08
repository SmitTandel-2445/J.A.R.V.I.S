import sounddevice as sd
import wave

SAMPLE_RATE = 16000
DURATION = 3
CHANNELS = 1

print("Recording for 3 seconds... Speak normally.")
audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype="int16",
    device=1,
)
sd.wait()

with wave.open("test_recording.wav", "wb") as wav_file:
    wav_file.setnchannels(CHANNELS)
    wav_file.setsampwidth(2)  # 16-bit audio = 2 bytes
    wav_file.setframerate(SAMPLE_RATE)
    wav_file.writeframes(audio.tobytes())

print("Saved test_recording.wav")

print("Playing recording...")
sd.play(audio, samplerate=SAMPLE_RATE, device=3)
sd.wait()
peak = abs(audio.astype("int32")).max()
print(f"Recording peak level: {peak} / 32767")
print("Playback finished.")