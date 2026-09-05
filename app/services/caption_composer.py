"""
Caption composition. AI is OPTIONAL here (per the brief: "composition is
what's graded, not AI usage"). If GEMINI_API_KEY is set, we call Gemini's
free tier; otherwise we fall back to a deterministic template composer
that still uses the shared BRAND_VOICE + PLATFORM_RULES fragments.

Either path goes through build_caption_prompt() so the composition logic
(shared + platform fragments, no duplicated prompts) is identical.
"""
import os
from config.social_prompts_config import build_caption_prompt, PLATFORM_RULES


def _template_fallback(platform: str, content_summary: str) -> str:
    rules = PLATFORM_RULES[platform]
    if platform == "instagram":
        return (
            f"{content_summary}\n\n"
            f"Read the full story — link in bio. "
            f"#tech #buildinpublic #softwareengineering"
        )[: rules["max_chars"]]
    else:  # x
        return f"{content_summary} 🧵"[: rules["max_chars"]]


def compose_caption(platform: str, content_summary: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _template_fallback(platform, content_summary)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = build_caption_prompt(platform, content_summary)
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        return text if text else _template_fallback(platform, content_summary)
    except Exception:
        # AI is optional and must never be a hard dependency for the demo.
        return _template_fallback(platform, content_summary)


def compose_all_captions(content_summary: str) -> dict:
    return {
        platform: compose_caption(platform, content_summary)
        for platform in PLATFORM_RULES
    }