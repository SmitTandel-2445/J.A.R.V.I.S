import speech_recognition as sr

recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8

try:
    with sr.Microphone(device_index=1) as source:
        print("Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening. Say 'stop listening' to exit.")

        while True:
            try:
                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=5
                )

                print("Recognizing...")
                text = recognizer.recognize_google(audio)
                print("You said:", text)

                if "stop listening" in text.lower():
                    print("Stopping listener.")
                    break

            except sr.WaitTimeoutError:
                print("No speech detected. Still listening...")
            except sr.UnknownValueError:
                print("Couldn't understand that phrase. Try again.")
            except sr.RequestError as error:
                print("Recognition service error:", error)
                break

except OSError as error:
    print("Microphone/audio device error:", error)