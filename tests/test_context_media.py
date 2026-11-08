import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.context import context_manager
from core.router import ActionRouter
from nlp.intent_classifier import IntentClassifier, IntentType

print("=== Testing Context-Aware Media & Search Disambiguation ===")
router = ActionRouter()
clf = IntentClassifier()

# -------------------------------------------------------------------
# Test 1: Explicit Platform Play Commands
# -------------------------------------------------------------------
res1 = clf.classify("play luna bala on spotify")
print(f"'play luna bala on spotify' -> {res1.intent.value} ({res1.parameters})")
assert res1.intent == IntentType.SPOTIFY_PLAY
assert res1.parameters.get("query") == "luna bala"

res2 = clf.classify("play tarak mehta on youtube")
print(f"'play tarak mehta on youtube' -> {res2.intent.value} ({res2.parameters})")
assert res2.intent == IntentType.YOUTUBE_PLAY
assert res2.parameters.get("query") == "tarak mehta"

# -------------------------------------------------------------------
# Test 2: Generic 'play [song]' intent classification
# -------------------------------------------------------------------
res3 = clf.classify("play luna bala")
print(f"'play luna bala' -> {res3.intent.value} ({res3.parameters})")
assert res3.intent == IntentType.PLAY_MEDIA
assert res3.parameters.get("query") == "luna bala"

res4 = clf.classify("play starboy")
print(f"'play starboy' -> {res4.intent.value} ({res4.parameters})")
assert res4.intent == IntentType.PLAY_MEDIA
assert res4.parameters.get("query") == "starboy"

# -------------------------------------------------------------------
# Test 3: Context-Aware Routing when Spotify IS Active
# -------------------------------------------------------------------
print("\n--- Testing with Spotify Context Active ---")
context_manager.set("app", "spotify")
assert context_manager.is_spotify_active() is True

route_spot = router.route("play luna bala")
print(f"Router Result (Spotify Active): {route_spot.intent.value} -> {route_spot.spoken_response}")
assert route_spot.intent == IntentType.SPOTIFY_PLAY
assert "Spotify" in route_spot.spoken_response
print("Spotify Context Routing: PASS")

# -------------------------------------------------------------------
# Test 4: Context-Aware Routing when YouTube IS Active
# -------------------------------------------------------------------
print("\n--- Testing with YouTube Context Active ---")
context_manager.set("app", "youtube")
assert context_manager.is_youtube_active() is True

# When YouTube tab is active, 'search tarak mehta' searches in YouTube!
route_yt_search = router.route("search tarak mehta")
print(f"Router Result (YouTube Active): {route_yt_search.intent.value} -> {route_yt_search.spoken_response}")
assert route_yt_search.intent == IntentType.YOUTUBE_PLAY
assert "YouTube" in route_yt_search.spoken_response
print("YouTube Search Context Routing: PASS")

# -------------------------------------------------------------------
# Test 5: Clean Fallback when NEITHER is Active (Standard Browsing / Desktop)
# -------------------------------------------------------------------
print("\n--- Testing with NO Media Context (Clean Browsing State) ---")
context_manager.clear()
with patch.object(context_manager, "is_spotify_active", return_value=False), \
     patch.object(context_manager, "is_youtube_active", return_value=False):
    assert context_manager.is_spotify_active() is False
    assert context_manager.is_youtube_active() is False

    # 'search tarak mehta' when neither is open -> Standard Google Search!
    route_google = router.route("search tarak mehta")
    print(f"Router Result (Clean State): {route_google.intent.value} -> {route_google.spoken_response}")
    assert route_google.intent == IntentType.WEB_SEARCH
    assert "Google" in route_google.spoken_response or "Searching" in route_google.spoken_response
    print("Google Fallback (Zero Conflict): PASS")

    # Conversational query -> Gemini Brain!
    route_ai = router.route("Who is Tony Stark?")
    print(f"Router Result (Clean State AI): {route_ai.intent.value} -> {route_ai.spoken_response[:50]}...")
assert route_ai.intent == IntentType.CONVERSATION_AI
print("Conversational AI (Zero Conflict): PASS")

print("\nALL CONTEXT-AWARE SPOTIFY & YOUTUBE TESTS PASSED 100%!")

