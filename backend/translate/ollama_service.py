import requests
import json
import re
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "glm-5:cloud"   # or "llama3"


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
                    "stream": False
                },
                timeout=120
            )
            return response.json()["response"]
        except Exception:
            time.sleep(2)

    raise Exception("Ollama failed after retries")


def ollama_extract_kg(text):
    prompt = f"""
Extract entities and relationships from the text.

Return ONLY valid JSON in this format:

{{
  "entities": [
    {{"id": "E1", "name": "Murko Darjan", "type": "PERSON"}}
  ],
  "relations": [
    {{"source": "Murko Darjan", "target": "Somalia", "relation": "BORN_IN", "context": "Born February 11, 1999"}}
  ]
}}

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