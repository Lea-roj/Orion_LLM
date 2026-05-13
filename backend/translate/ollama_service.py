import requests
import json
import re
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"
# https://github.com/ollama/ollama/blob/86b0dd4b165497e08ec331e3c2c2aa229beb09db/docs/faq.md#how-can-i-expose-ollama-on-my-network
# https://github.com/ollama/ollama/issues/1579

class KB:
    def __init__(self, entities, relations):
        self.entities = entities
        self.relations = relations


def call_ollama(prompt, retries=3):
    for _ in range(retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                },
                timeout=120
            )
            return response.json()["response"]
        except Exception:
            time.sleep(2)

    raise Exception("Ollama failed after retries")


def ollama_extract_kg(text, context=None):
    context_block = ""

    if context:
        context_block = f"""
Previously identified entities (use these for consistency, reuse names if possible):
{", ".join(context[:50])}
"""

    prompt = f"""
Extract entities and relationships from the text.

IMPORTANT:
- Reuse existing entity names if they appear again
- Avoid duplicates (e.g. "EU" vs "European Union")
- Keep entity names consistent

Return ONLY valid JSON in this format:

{{
  "entities": [
    {{"id": "E1", "name": "Murko Darjan", "type": "PERSON"}}
  ],
  "relations": [
    {{"source": "Murko Darjan", "target": "Somalia", "relation": "BORN_IN", "context": "Born February 11, 1999"}}
  ]
}}

{context_block}

Text:
{text}
"""

    raw_output = call_ollama(prompt)

    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if not match:
        return KB([], [])

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return KB([], [])

    return KB(
        entities=data.get("entities", []),
        relations=data.get("relations", [])
    )