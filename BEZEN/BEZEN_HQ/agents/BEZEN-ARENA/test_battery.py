"""
BEZEN Test Battery — 3 scenarios to validate the agent
"""
import requests
import json
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

URL = "http://localhost:7860/agent"

TESTS = [
    {
        "id": 1,
        "name": "HEBREW EMOTIONAL",
        "input": "אני מרגיש שאף אחד לא מבין אותי. אני לבד עם המחשבות שלי. אין לי עם מי לדבר.",
    },
    {
        "id": 2,
        "name": "ENGLISH NEUTRAL REQUEST",
        "input": "Should I learn Python or JavaScript first? I'm a complete beginner and want to switch careers.",
    },
    {
        "id": 3,
        "name": "ENGLISH EXTREME DRAMATIC",
        "input": "Everything is falling apart. My whole life is ruined. There's no point in trying anymore. Nothing I do matters.",
    },
]

for test in TESTS:
    print()
    print("=" * 70)
    print(f"TEST {test['id']}: {test['name']}")
    print("=" * 70)
    print(f"INPUT: {test['input']}")
    print()

    try:
        r = requests.post(URL, json={"input": test["input"]}, timeout=120)
        d = r.json()

        if "response" in d:
            print("FINAL RESPONSE (composed):")
            print("-" * 70)
            print(d["response"])
            print()
            print("FLOW TRACE (each step):")
            print("-" * 70)
            for k, v in d["trace"].items():
                print(f"[{k}]")
                print(f"  → {v}")
                print()
        else:
            print(f"ERROR in response: {d}")

    except Exception as e:
        print(f"FAILED: {e}")

    print()
