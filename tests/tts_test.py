import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty("voice", engine.getProperty("voices")[0].id)
    engine.setProperty("rate", 150)
    engine.setProperty("volume", 1.0)

    engine.say(text)
    engine.runAndWait()
    engine.stop()

speak("Hello, I am Jarvis.")
speak("All systems are ready.")
speak("How can I help you?")