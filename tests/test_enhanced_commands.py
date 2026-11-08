import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation.app_launcher import app_launcher
from automation.app_scanner import app_scanner
from automation.browser import browser_controller
from core.router import ActionRouter
from nlp.intent_classifier import IntentClassifier, IntentType

print("=== 1. Testing App Scanner & Dynamic Discovery ===")
print(f"Total applications indexed: {len(app_scanner.installed_apps)}")

# Check key installed apps on user's system
test_apps = ["chrome", "excel", "firefox", "vs code", "github", "chatgpt", "spotify"]
for app in test_apps:
    target, res_type = app_scanner.resolve(app)
    print(f"Resolving '{app}' -> Type: {res_type}, Target: {target}")
    assert target is not None, f"Failed to resolve {app}"

print("App Scanner Resolution: PASS\n")

print("=== 2. Testing App Launcher Fallback ===")
# Launching web service
success_web, msg_web = app_launcher.launch("github")
print(f"Launch Web (github): {success_web} -> {msg_web}")
assert success_web is True

# Launching unknown app (should trigger Google search fallback)
success_unk, msg_unk = app_launcher.launch("some_unknown_rare_app_12345")
print(f"Launch Unknown (fallback to Google): {success_unk} -> {msg_unk}")
assert success_unk is True
assert "Searching Google" in msg_unk
print("App Launcher Tests: PASS\n")

print("=== 3. Testing Intent Classifier Search & Tab Variations ===")
clf = IntentClassifier()

search_tests = [
    ("search marvel movies in 2026", "marvel movies in 2026"),
    ("search for quantum computing", "quantum computing"),
    ("google latest AI developments", "latest AI developments"),
    ("find python cheatsheet", "python cheatsheet"),
    ("look up Albert Einstein", "Albert Einstein"),
]

for query, expected_target in search_tests:
    res = clf.classify(query)
    print(f"Query: '{query}' -> Intent: {res.intent.value}, Param: {res.parameters.get('query')}")
    assert res.intent == IntentType.WEB_SEARCH
    assert res.parameters.get("query") == expected_target

tab_tests = [
    ("new tab", "new_tab"),
    ("open a new tab", "new_tab"),
    ("close tab", "close_tab"),
    ("refresh page", "refresh"),
    ("reload tab", "refresh"),
    ("go back", "back"),
    ("next tab", "next_tab"),
    ("incognito window", "incognito"),
]

for query, expected_act in tab_tests:
    res = clf.classify(query)
    print(f"Query: '{query}' -> Intent: {res.intent.value}, Action: {res.parameters.get('action')}")
    assert res.intent == IntentType.BROWSER_TAB
    assert res.parameters.get("action") == expected_act

print("Search & Tab Intent Tests: PASS\n")

print("=== 4. Testing ActionRouter Integration ===")
router = ActionRouter()

# Search route
res_search = router.route("search python documentation")
print(f"Router Search: {res_search.spoken_response}")
assert res_search.intent == IntentType.WEB_SEARCH

# Tab route
res_tab = router.route("new tab")
print(f"Router Tab: {res_tab.spoken_response}")
assert res_tab.intent == IntentType.BROWSER_TAB

print("\nALL ENHANCED APPLICATION & SEARCH TESTS PASSED SUCCESSFULLY!")

