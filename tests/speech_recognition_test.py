import speech_recognition as sr

recognizer = sr.Recognizer()

with sr.AudioFile("test_recording.wav") as source:
    audio = recognizer.record(source)

try:
    text = recognizer.recognize_google(audio)
    print("Recognized speech:", text)
except sr.UnknownValueError:
    print("The speech recognizer could not understand the audio.")
except sr.RequestError as error:
    print("Could not reach the speech recognition service:", error)