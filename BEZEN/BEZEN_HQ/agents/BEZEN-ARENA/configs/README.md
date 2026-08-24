# Client configs

One JSON file per client. `/support?c=<filename>` loads it, so a prospect gets a
short clean link (`/support?c=almaya`) instead of their whole business config
base64'd into the URL — which crosses 1,800 characters on even a modest catalog
and starts getting mangled by messaging apps.

Committed rather than stored at runtime on purpose: Render's free tier has an
ephemeral filesystem, so anything written at runtime disappears on the next
restart or deploy.

Fields — all optional except `name`:

```json
{
  "name": "שם העסק",
  "domain": "תחום הפעילות",
  "policies": "מדיניות, קטלוג, מחירים — כל מה שהסוכן רשאי להסתמך עליו כעובדה",
  "escalation": "מה קורה כשצריך אדם אמיתי"
}
```

`policies` is the field that decides whether the agent is useful. With it empty
the agent cannot answer basic questions and falls back to "a representative will
get back to you" — which is what happened in the first live session with a real
prospect. Put the actual catalog and real price ranges in.

The agent is instructed never to invent facts beyond what is in here, so
anything missing becomes "I don't have access to that" rather than a
hallucinated answer.
