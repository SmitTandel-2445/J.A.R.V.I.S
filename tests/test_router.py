import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.router import ActionRouter, ActionResult
from nlp.intent_classifier import IntentType

router = ActionRouter()

# Test 1: Time query (Local, Fast-Path)
res_time = router.route("what time is it")
print("Time query test:", res_time.spoken_response)
assert res_time.intent == IntentType.TIME_DATE
assert "currently" in res_time.spoken_response

# Test 2: System Telemetry (Local, Fast-Path)
res_telem = router.route("system status")
print("Telemetry test:", res_telem.spoken_response)
assert res_telem.intent == IntentType.SYSTEM_TELEMETRY
assert "CPU" in res_telem.spoken_response

# Test 3: Web Search intent
router.context_manager.is_spotify_active = lambda: False
router.context_manager.is_youtube_active = lambda: False
res_search = router.route("search google for python tutorial")
print("Search test:", res_search.spoken_response)
assert res_search.intent == IntentType.WEB_SEARCH

# Test 4: General AI
res_ai = router.route("Who is Tony Stark?")
print("AI test:", res_ai.spoken_response)
assert res_ai.intent == IntentType.CONVERSATION_AI
assert len(res_ai.spoken_response) > 5

print("All Router tests passed successfully!")

