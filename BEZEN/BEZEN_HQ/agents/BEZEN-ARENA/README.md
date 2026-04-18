# BEZEN-WORDSMITH Agent

Runtime alignment agent for AgentTopology Arena.
Category: wordsmith

## Local Run

```bash
pip install -r requirements.txt
# Set ANTHROPIC_API_KEY in .env
python bezen_wordsmith.py
# Open http://localhost:7860/
```

## Endpoints

- `GET /` - Demo page (HTML)
- `GET /health` - Status check (JSON)
- `POST /agent` - Main API: `{"input": "user message"}`
- `GET /test` - Quick test with sample prompt

## Deploy to Render

1. Push to GitHub
2. New Web Service on render.com
3. Set env var: `ANTHROPIC_API_KEY`
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn bezen_wordsmith:app`
