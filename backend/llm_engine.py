"""
LLM integration for AI rule parsing and remediation suggestions.
Supports OpenAI-compatible APIs (OpenAI, DeepSeek, etc.).
"""
import json
import re

# Configurable defaults
LLM_API_URL = "https://api.deepseek.com/v1/chat/completions"
LLM_MODEL = "deepseek-chat"
LLM_API_KEY = ""  # Set via frontend or env


async def llm_parse_regulation(text: str, api_key: str = "", api_url: str = "") -> list[dict]:
    """Use LLM to parse a complex regulation into structured rules."""
    key = api_key or LLM_API_KEY
    url = api_url or LLM_API_URL
    if not key:
        return []

    prompt = f"""Parse this building regulation into a JSON array of compliance check rules.
Each rule must have: target, property, condition, value, unit, scope.

Supported targets: IfcDoor, IfcWall, IfcWindow (+ means combine)
Supported properties: OverallWidth, OverallHeight, FireRating, count
Supported conditions: gte (>=), exists
value: number or null
unit: mm, cm, m, count, or null
scope: all or egress

Regulation: "{text}"

Return ONLY valid JSON array, no explanation. Example:
[{{"target":"IfcDoor","property":"OverallWidth","condition":"gte","value":900,"unit":"mm","scope":"all"}}]"""

    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            }, headers={"Authorization": f"Bearer {key}"})
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            # Extract JSON from response
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                rules = json.loads(match.group())
                return rules
    except Exception:
        pass
    return []


async def llm_explain_failure(element: dict, rule_desc: str, api_key: str = "", api_url: str = "") -> str:
    """Generate remediation suggestion for a failed element."""
    key = api_key or LLM_API_KEY
    url = api_url or LLM_API_URL
    if not key:
        return "LLM API key not configured. Add your API key in settings to get AI suggestions."

    prompt = f"""A building compliance check failed. Provide a concise remediation suggestion in Chinese.

Rule: {rule_desc}
Element: {json.dumps(element, ensure_ascii=False)}

Reply in 1-2 sentences, practical and actionable. Mention relevant codes if applicable (GB 50016)."""

    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            }, headers={"Authorization": f"Bearer {key}"})
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"LLM unavailable: {str(e)[:100]}"
