"""Debate test battery - 4 controversial topics in different domains."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from anthropic import Anthropic
from bezen_debate import BezenDebate, API_KEY

client = Anthropic(api_key=API_KEY)
debate = BezenDebate(client, "claude-sonnet-4-5-20250929")

TOPICS = [
    "Should remote work become the default for knowledge workers?",
    "Is universal basic income a good response to AI-driven job displacement?",
    "האם חובה צבאית עדיין רלוונטית בעידן הטכנולוגי?",
    "Should social media platforms be legally responsible for misinformation?",
]

for i, topic in enumerate(TOPICS, 1):
    print()
    print("=" * 75)
    print(f"DEBATE #{i}: {topic}")
    print("=" * 75)

    result = debate.respond(topic)

    # Print just the calibrated position (most important for ELO judging)
    print("\n>>> CALIBRATED POSITION:")
    print(result["trace"]["flow_5_position"])

    print("\n>>> COMMON GROUND:")
    print(result["trace"]["flow_4_common_ground"])

    print("\n>>> PRACTICAL TEST:")
    print(result["trace"]["flow_6_implication"])
    print()
