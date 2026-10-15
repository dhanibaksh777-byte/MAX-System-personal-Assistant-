import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, '.')

from assistant_core import AssistantCore

core = AssistantCore()

test_cases = [
    ("open youtube", "en"),
    ("youtube kholo", "hi"),
    ("open spotify", "en"),
    ("tum kaun ho", "hi"),
    ("who are you", "en"),
    ("volume up", "en"),
    ("aawaz badhao", "hi"),
    ("play lofi beats on youtube", "en"),
    ("search for quantum computing", "en"),
    ("یوٹیوب کھولو", "ur"),
    ("کیسے ہو", "ur")
]

print("=" * 60)
print("TESTING MAX ASSISTANT ZERO-DELAY MULTILINGUAL FAST PATH")
print("=" * 60)

for msg, lang in test_cases:
    t0 = time.time()
    res = core.process_message(msg, lang)
    dt = (time.time() - t0) * 1000
    fast = res.get('fast_path', False)
    reply = res.get('response', '')
    print(f"\nUser [{lang}]: '{msg}'")
    print(f"Max  : '{reply[:75]}...'")
    print(f"Delay: {dt:.2f} ms | Fast-path: {fast}")

print("\n" + "=" * 60)
print("All fast-path tests completed!")
print("=" * 60)
