import os
import google.generativeai as genai


def _dev_fallback_response(user_message: str, current_mod: dict) -> str:
    msg_lower = user_message.strip().lower()
    if any(token in msg_lower for token in ["done", "completed", "finish", "finished", "i did it", "module complete"]):
        return f"Nice work — you met the objective for '{current_mod.get('title', 'this module')}'. [MODULE_COMPLETE]"

    objective = current_mod.get("objective")
    if objective:
        return f"Let's focus on the objective: {objective} What would you like to try next?"
    return "Tell me what you tried, and I'll guide your next step."


def generate_ai_text(system_instruction: str, user_message: str, current_mod: dict) -> str:
    dev_fallback_enabled = os.getenv("HOMEGROWN_DEV_FALLBACK", "0") == "1"
    if dev_fallback_enabled:
        return _dev_fallback_response(user_message, current_mod)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    genai.configure(api_key=api_key)

    model_name = os.getenv("GEMINI_MODEL", "gemini-pro-latest")
    model = genai.GenerativeModel(model_name)

    full_prompt = f"{system_instruction}\n\nUser: {user_message}"

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        err_text = str(e)
        if "429" in err_text or "quota" in err_text.lower() or "rate" in err_text.lower():
            return _dev_fallback_response(user_message, current_mod)
        raise
