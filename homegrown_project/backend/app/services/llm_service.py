import os
import json
import google.generativeai as genai

_model_cache: dict = {}


def _dev_fallback_response(user_message: str, current_mod: dict) -> str:
    msg_lower = user_message.strip().lower()
    if any(token in msg_lower for token in ["done", "completed", "finish", "finished", "i did it", "module complete"]):
        payload = {
            "version": 1,
            "mode": "chat",
            "blocks": [
                {
                    "type": "markdown",
                    "text": f"Nice work — you met the objective for '{current_mod.get('title', 'this module')}'. [MODULE_COMPLETE]",
                }
            ],
        }
        return json.dumps(payload)

    objective = current_mod.get("objective")
    if objective:
        payload = {
            "version": 1,
            "mode": "chat",
            "blocks": [
                {"type": "markdown", "text": f"Let's focus on the objective: {objective} What would you like to try next?"}
            ],
        }
        return json.dumps(payload)

    payload = {
        "version": 1,
        "mode": "chat",
        "blocks": [{"type": "markdown", "text": "Tell me what you tried, and I'll guide your next step."}],
    }
    return json.dumps(payload)


def generate_ai_text(system_instruction: str, user_message: str, current_mod: dict) -> str:
    dev_fallback_enabled = os.getenv("HOMEGROWN_DEV_FALLBACK", "0") == "1"
    if dev_fallback_enabled:
        return _dev_fallback_response(user_message, current_mod)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    model_name = os.getenv("GEMINI_MODEL", "gemini-pro-latest")
    cache_key = (api_key, model_name)

    if cache_key not in _model_cache:
        genai.configure(api_key=api_key)
        _model_cache[cache_key] = genai.GenerativeModel(model_name)

    model = _model_cache[cache_key]

    full_prompt = f"{system_instruction}\n\nUser: {user_message}"

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        err_text = str(e)
        if "429" in err_text or "quota" in err_text.lower() or "rate" in err_text.lower():
            return _dev_fallback_response(user_message, current_mod)
        raise
