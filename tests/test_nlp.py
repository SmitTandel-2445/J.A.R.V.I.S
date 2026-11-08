import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nlp.intent_classifier import IntentClassifier, IntentType

clf = IntentClassifier()
tests = [
    ("Jarvis, open Chrome", IntentType.OPEN_APP, {"app_name": "Chrome"}),
    ("Could you please launch Notepad", IntentType.OPEN_APP, {"app_name": "Notepad"}),
    ("close chrome", IntentType.CLOSE_APP, {"app_name": "chrome"}),
    ("volume up", IntentType.SYSTEM_VOLUME, {"action": "up", "step": 10}),
    ("mute audio", IntentType.SYSTEM_VOLUME, {"action": "mute"}),
    ("set volume to 65%", IntentType.SYSTEM_VOLUME, {"action": "set", "level": 65}),
    ("what time is it", IntentType.TIME_DATE, {"query_type": "time"}),
    ("what day is it", IntentType.TIME_DATE, {"query_type": "date"}),
    ("search google for quantum physics", IntentType.WEB_SEARCH, {"query": "quantum physics"}),
    ("play believer on youtube", IntentType.YOUTUBE_PLAY, {"query": "believer"}),
    ("check battery", IntentType.SYSTEM_TELEMETRY, {}),
    ("Who is Tony Stark?", IntentType.CONVERSATION_AI, {"query": "Who is Tony Stark?"}),
]

all_passed = True
for query, expected_intent, expected_params in tests:
    res = clf.classify(query)
    match = (res.intent == expected_intent) and (res.parameters == expected_params)
    if not match:
        print(f"FAILED: '{query}' -> got {res.intent} {res.parameters}, expected {expected_intent} {expected_params}")
        all_passed = False
    else:
        print(f"PASS: '{query}' -> {res.intent.value} ({res.parameters})")

print("All tests passed:", all_passed)
if not all_passed:
    exit(1)
