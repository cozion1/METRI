#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VirtueBalanceEngine
===================
Reads BEZEN session pattern activations and produces a Virtue Balance score
across the 6 VIA virtues and 24 VIA strengths.

Scoring model:
  Per detected pattern  →  contribution = confidence × severity × decay(count)
  Per VIA strength       →  sum of contributions from all mapped patterns
  Per virtue             →  sum of strength raw scores / patterns-in-virtue (normalized)

'Activation' = how strongly that virtue's pain domain is being experienced.
  High activation = pain area needing attention.
  Low activation  = relatively healthy / untouched domain.

Recommended strengths are drawn from the most-activated virtue — the positive
capacities that directly counterbalance that pain domain.

Usage:
    python engine/virtue_balance.py [session_state.json] [output.json]

    Defaults:
        input  = data/bezen_session_state_example.json
        output = data/bezen_virtue_balance.json
"""

import json
import math
import os
import sys
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(filename):
    with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────
#  ACTIVATION LEVELS
# ─────────────────────────────────────────────────────────────────────
def _activation_level(pct):
    if pct >= 70:  return ("high",   "גבוה",    "גיוס אקטיבי — תחום דורש עיבוד")
    if pct >= 40:  return ("medium", "בינוני",  "פעיל — תחום נוכח בחוויה")
    if pct >= 10:  return ("low",    "נמוך",    "רקע — תחום מופיע מעט")
    return              ("none",   "ללא",     "לא מזוהה — תחום שקט")


# ─────────────────────────────────────────────────────────────────────
#  RECOMMENDATION REASONS  (keyed by via_strength_id)
# ─────────────────────────────────────────────────────────────────────
_REASONS = {
    "creativity":           ("חשיבה יצירתית פותחת מוצאים חדשים מתוך הכאב",
                             "Creative thinking opens new paths through pain"),
    "curiosity":            ("סקרנות הופכת חרדה לחקירה",
                             "Curiosity transforms anxiety into inquiry"),
    "judgment":             ("שיפוט ביקורתי מאזן תפיסות עצמיות מעוותות",
                             "Critical judgment corrects distorted self-perception"),
    "love_of_learning":     ("למידה נותנת משמעות לחוויות קשות",
                             "Learning gives meaning to difficult experiences"),
    "perspective":          ("ראייה רחבה מקטינה את עוצמת הכאב",
                             "Broader perspective reduces the intensity of pain"),
    "bravery":              ("אומץ מאפשר פעולה למרות הפחד",
                             "Bravery enables action despite fear"),
    "perseverance":         ("התמדה מחזקת אמונה ביכולת להתמיד",
                             "Perseverance rebuilds belief in one's capacity"),
    "honesty":              ("כנות עם עצמי מאפשרת ריפוי אמיתי",
                             "Honesty with oneself enables genuine healing"),
    "zest":                 ("חיוניות מזכירה שהחיים שווים מאמץ",
                             "Zest is a reminder that life is worth the effort"),
    "love":                 ("אהבה עצמית ולאחרים מרפאה פצעי דחייה",
                             "Love of self and others heals wounds of rejection"),
    "kindness":             ("נדיבות פנימית מנגנת נגד קשיחות עצמית",
                             "Inner kindness counters self-harshness"),
    "social_intelligence":  ("הבנת דינמיקות חברתיות מפחיתה תחושת בדידות",
                             "Social understanding reduces the sense of aloneness"),
    "teamwork":             ("שייכות לצוות מרפאה ניכור ובידוד",
                             "Belonging to a team heals alienation"),
    "fairness":             ("הגינות פנימית מאפשרת שחרור מכעס",
                             "Internal fairness allows release from anger"),
    "leadership":           ("מנהיגות אישית מחזקת תחושת סוכנות ושליטה",
                             "Personal leadership strengthens agency and control"),
    "forgiveness":          ("סליחה משחררת מנטל הכעס והבושה",
                             "Forgiveness releases the burden of anger and shame"),
    "humility":             ("ענווה מאפשרת קבלה עצמית ללא שיפוטיות",
                             "Humility allows self-acceptance without judgment"),
    "prudence":             ("שיקול דעת זהיר מפחית הצפה ואי-ודאות",
                             "Careful prudence reduces overwhelm and uncertainty"),
    "self_regulation":      ("ויסות עצמי מחזיר תחושת שליטה פנימית",
                             "Self-regulation restores a sense of inner control"),
    "appreciation_of_beauty":("הערכת יופי מחזירה תחושת ערך לחיים",
                             "Appreciating beauty restores a sense of value in life"),
    "gratitude":            ("הכרת טובה מאזנת את ה'חסר' בתפיסת העצמי",
                             "Gratitude balances the perceived deficit in self-view"),
    "hope":                 ("תקווה נותנת כיוון כשהמצב נראה חסר תוחלת",
                             "Hope provides direction when things feel hopeless"),
    "humor":                ("הומור מקל עומסים ומייצר ריחוק בריא",
                             "Humor lightens burdens and creates healthy distance"),
    "spirituality":         ("רוחניות מעניקה משמעות ומעוגנות מעבר לכאב",
                             "Spirituality provides meaning and grounding beyond pain"),
}


# ─────────────────────────────────────────────────────────────────────
#  ENGINE CLASS
# ─────────────────────────────────────────────────────────────────────
class VirtueBalanceEngine:

    def __init__(self):
        # pattern_id → {via_strength_id, virtue_id, ...}
        raw_map = _load("bezen_pattern_to_strength_map.json")
        self.pattern_map = {m["pattern_id"]: m for m in raw_map["mappings"]}

        # via_strength_id → {label_he, label_en, virtue_id, pattern_count, ...}
        raw_str = _load("bezen_via_strengths.json")
        self.strengths = {s["id"]: s for s in raw_str["strengths"]}

        # virtue_id → {label_he, label_en, strength_ids, pattern_count, ...}
        raw_vir = _load("bezen_virtues.json")
        self.virtues = {v["id"]: v for v in raw_vir["virtues"]}

        # Precompute: virtue_id → {expected pattern count for that virtue}
        self.virtue_pattern_counts = {vid: v["pattern_count"] for vid, v in self.virtues.items()}

    # ── scoring helpers ───────────────────────────────────────────────

    @staticmethod
    def _decay(count):
        """Logarithmic count decay — diminishing returns after 1st activation."""
        return 1.0 + math.log1p(max(0, count - 1))

    @staticmethod
    def _contribution(confidence, severity, count):
        """Weighted contribution of a single detected pattern."""
        sev_norm = max(0.0, min(1.0, severity / 5.0))          # severity 0-5 → 0-1
        conf     = max(0.0, min(1.0, float(confidence)))
        return conf * sev_norm * VirtueBalanceEngine._decay(count)

    # ── main compute ─────────────────────────────────────────────────

    def compute(self, session: dict) -> dict:
        """
        session must follow bezen_session_state_example.json structure.
        Returns the full virtue balance document.
        """
        detected = session.get("detected_patterns", [])
        if not detected:
            detected = []

        # ── 1.  Build strength scores ─────────────────────────────────
        # strength_id → { raw_score, contributing_patterns }
        strength_scores_raw = {sid: {"raw": 0.0, "patterns": []} for sid in self.strengths}

        for dp in detected:
            pid        = dp.get("pattern_id", "")
            confidence = dp.get("confidence", 1.0)
            severity   = dp.get("severity", 3)
            count      = dp.get("count", 1)

            mapping = self.pattern_map.get(pid)
            if not mapping:
                continue

            sid   = mapping["via_strength_id"]
            score = self._contribution(confidence, severity, count)
            strength_scores_raw[sid]["raw"] += score
            strength_scores_raw[sid]["patterns"].append(pid)

        # ── 2.  Normalise strength scores to 0-100 ────────────────────
        max_raw = max((v["raw"] for v in strength_scores_raw.values()), default=1.0) or 1.0

        strength_scores = {}
        for sid, data in strength_scores_raw.items():
            s_meta = self.strengths[sid]
            raw    = data["raw"]
            pct    = round((raw / max_raw) * 100, 1)
            lvl    = _activation_level(pct)
            strength_scores[sid] = {
                "label_he":             s_meta["label_he"],
                "label_en":             s_meta["label_en"],
                "virtue_id":            s_meta["virtue_id"],
                "raw_score":            round(raw, 4),
                "normalized":           pct,
                "activation_level":     lvl[0],
                "activation_label_he":  lvl[1],
                "pattern_count":        len(data["patterns"]),
                "contributing_patterns": sorted(data["patterns"]),
            }

        # ── 3.  Aggregate into virtue scores ─────────────────────────
        virtue_scores_raw = {vid: 0.0 for vid in self.virtues}
        virtue_active_str = {vid: [] for vid in self.virtues}

        for sid, sc in strength_scores.items():
            vid = sc["virtue_id"]
            virtue_scores_raw[vid] += sc["raw_score"]
            if sc["pattern_count"] > 0:
                virtue_active_str[vid].append(sid)

        # Normalise per-virtue by expected pattern count (so virtues with more
        # mapped patterns aren't artificially inflated)
        virtue_norm_scores = {}
        for vid, raw in virtue_scores_raw.items():
            expected = self.virtue_pattern_counts.get(vid, 1) or 1
            virtue_norm_scores[vid] = raw / expected

        max_vraw = max(virtue_norm_scores.values(), default=1.0) or 1.0

        virtue_scores = {}
        for vid, nraw in virtue_norm_scores.items():
            v_meta = self.virtues[vid]
            pct    = round((nraw / max_vraw) * 100, 1)
            lvl    = _activation_level(pct)
            virtue_scores[vid] = {
                "label_he":             v_meta["label_he"],
                "label_en":             v_meta["label_en"],
                "raw_score":            round(virtue_scores_raw[vid], 4),
                "normalized":           pct,
                "activation_level":     lvl[0],
                "activation_label_he":  lvl[1],
                "activation_description_he": lvl[2],
                "active_strengths":     sorted(virtue_active_str[vid]),
                "strength_count":       len(v_meta["strength_ids"]),
                "pattern_count":        sum(
                    strength_scores[s]["pattern_count"]
                    for s in v_meta["strength_ids"]
                ),
            }

        # ── 4.  Dominant / weakest ────────────────────────────────────
        sorted_v = sorted(virtue_scores.items(), key=lambda x: x[1]["normalized"], reverse=True)
        dominant_id = sorted_v[0][0]
        weakest_id  = sorted_v[-1][0]

        dominant_data = virtue_scores[dominant_id]
        weakest_data  = virtue_scores[weakest_id]

        dominant_virtue = {
            "id":            dominant_id,
            "label_he":      dominant_data["label_he"],
            "label_en":      dominant_data["label_en"],
            "score":         dominant_data["normalized"],
            "interpretation_he": "תחום הכאב הדומיננטי בסשן — מומלץ לעבד ולאזן",
            "interpretation_en": "Dominant pain domain in session — focus area for balancing",
        }

        weakest_virtue = {
            "id":            weakest_id,
            "label_he":      weakest_data["label_he"],
            "label_en":      weakest_data["label_en"],
            "score":         weakest_data["normalized"],
            "interpretation_he": "תחום שקט — חוזק יחסי בסשן זה",
            "interpretation_en": "Quiet domain — relative strength in this session",
        }

        # ── 5.  Recommended balancing strengths ──────────────────────
        # Pull the top-2 active strengths from the dominant virtue
        # + top-1 from second-most-active virtue (breadth bonus)
        dominant_strengths = [
            (s, strength_scores[s]["normalized"])
            for s in self.virtues[dominant_id]["strength_ids"]
        ]
        dominant_strengths.sort(key=lambda x: x[1], reverse=True)

        second_id = sorted_v[1][0] if len(sorted_v) > 1 else None
        second_strengths = []
        if second_id:
            second_strengths = [
                (s, strength_scores[s]["normalized"])
                for s in self.virtues[second_id]["strength_ids"]
            ]
            second_strengths.sort(key=lambda x: x[1], reverse=True)

        candidates = []
        for sid, score in dominant_strengths[:2]:
            candidates.append((sid, score, dominant_id))
        if second_strengths:
            candidates.append((second_strengths[0][0], second_strengths[0][1], second_id))
        # Deduplicate while preserving order
        seen = set()
        recs = []
        for sid, score, vid in candidates:
            if sid not in seen:
                seen.add(sid)
                recs.append((sid, score, vid))

        recommended_strengths = []
        for i, (sid, score, vid) in enumerate(recs, 1):
            s_meta   = self.strengths[sid]
            reasons  = _REASONS.get(sid, ("כוח מאזן", "Balancing strength"))
            recommended_strengths.append({
                "priority":         i,
                "via_strength_id":  sid,
                "label_he":         s_meta["label_he"],
                "label_en":         s_meta["label_en"],
                "virtue_id":        vid,
                "virtue_label_he":  self.virtues[vid]["label_he"],
                "virtue_label_en":  self.virtues[vid]["label_en"],
                "activation_score": score,
                "reason_he":        reasons[0],
                "reason_en":        reasons[1],
            })

        # ── 6.  Assemble output document ─────────────────────────────
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "version":            "1.0",
            "computed_at":        now,
            "session_id":         session.get("session_id", ""),
            "user_id":            session.get("user_id", ""),
            "total_activations":  len(detected),
            "active_pattern_ids": sorted({dp["pattern_id"] for dp in detected
                                          if dp.get("pattern_id") in self.pattern_map}),
            "strength_scores":    strength_scores,
            "virtue_scores":      virtue_scores,
            "virtue_ranking":     [
                {"rank": i + 1, "id": vid, "score": virtue_scores[vid]["normalized"]}
                for i, (vid, _) in enumerate(sorted_v)
            ],
            "dominant_virtue":         dominant_virtue,
            "weakest_virtue":          weakest_virtue,
            "recommended_strengths":   recommended_strengths,
        }


# ─────────────────────────────────────────────────────────────────────
#  CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    session_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(DATA_DIR, "bezen_session_state_example.json")
    )
    output_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.join(DATA_DIR, "bezen_virtue_balance.json")
    )

    with open(session_path, encoding="utf-8") as f:
        session = json.load(f)

    engine  = VirtueBalanceEngine()
    balance = engine.compute(session)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(balance, f, ensure_ascii=False, indent=2)

    # ── print summary ──
    print(f"Session : {balance['session_id']}")
    print(f"Patterns: {balance['total_activations']} activations → {len(balance['active_pattern_ids'])} unique")
    print()
    print("Virtue scores (ranked):")
    for r in balance["virtue_ranking"]:
        bar = "#" * int(r["score"] / 5)
        vs  = balance["virtue_scores"][r["id"]]
        print(f"  {r['rank']}. {r['id']:<22} {r['score']:>5.1f}%  {bar:<20}  [{vs['activation_level']}]")
    print()
    dom = balance["dominant_virtue"]
    wk  = balance["weakest_virtue"]
    print(f"Dominant : {dom['id']} ({dom['label_he']})  score={dom['score']}")
    print(f"Weakest  : {wk['id']}  ({wk['label_he']})  score={wk['score']}")
    print()
    print("Recommended balancing strengths:")
    for r in balance["recommended_strengths"]:
        print(f"  {r['priority']}. {r['via_strength_id']:<26} [{r['virtue_id']}]")
        print(f"     {r['reason_he']}")
    print()
    print(f"Written  : {os.path.relpath(output_path)}")
