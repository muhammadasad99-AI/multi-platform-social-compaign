"""
Platform voice as DATA, not duplicated prompts. Modeled on FlyRank's
config/social-prompts.config.ts pattern: one shared brand-voice fragment,
composed with a small per-platform rules fragment, never copy-pasted
whole prompts per platform.
"""

BRAND_VOICE = (
    "You are writing on behalf of a friendly, knowledgeable tech brand. "
    "Be clear, confident, and avoid corporate jargon. Never use more than one emoji."
)

PLATFORM_RULES = {
    "instagram": {
        "tone": "warm and visual, invites engagement, can be slightly longer",
        "max_chars": 2200,
        "hashtags": "3-5 relevant hashtags at the end",
        "cta": "encourage saves/shares",
    },
    "x": {
        "tone": "punchy, concise, conversational, one clear hook",
        "max_chars": 280,
        "hashtags": "0-2 hashtags max, only if they add discoverability",
        "cta": "encourage replies/reposts",
    },
}


def build_caption_prompt(platform: str, content_summary: str) -> str:
    """Composes: shared brand voice + platform rules + content summary."""
    if platform not in PLATFORM_RULES:
        raise ValueError(f"Unknown platform '{platform}'")

    rules = PLATFORM_RULES[platform]
    return (
        f"{BRAND_VOICE}\n\n"
        f"Platform: {platform}\n"
        f"Tone: {rules['tone']}\n"
        f"Max length: {rules['max_chars']} characters\n"
        f"Hashtags: {rules['hashtags']}\n"
        f"Call to action style: {rules['cta']}\n\n"
        f"Content to promote:\n{content_summary}\n\n"
        f"Write ONE caption for this platform. Output only the caption text."
    )