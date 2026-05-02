"""
Small script: load API credentials, send a paragraph to Claude, print a 3-sentence summary.
"""

# Lets you use modern type hints (e.g. `list[str]`) on all Python versions this file supports.
from __future__ import annotations

# `os` reads environment variables; `sys` exits the program and can write to stderr.
import os
import sys

# Read key=value pairs from a `.env` file into process environment variables.
from dotenv import load_dotenv

# Official Anthropic client for Claude (Messages API).
from anthropic import Anthropic


# Triple-quoted string spanning lines; `.strip()` removes leading/trailing whitespace including the first newline.
KENYA_TECH_PARAGRAPH = """
After several years of academic writing, I am transitioning into AI automation services. 
I am moving from Nakuru to Nairobi in two months to be closer to clients and the 
broader tech ecosystem. My goal is to help local Kenyan businesses — clinics, law 
firms, real estate agencies — eliminate manual repetitive work using AI-powered 
systems. I am currently learning Python, the Claude API, and n8n to build these 
solutions. The plan is to deliver my first paid project within three months.
""".strip()


def extract_text_from_message(message: object) -> str:
    """Join all text blocks from Claude’s reply (handles plain text responses)."""
    # Build a list of strings we will join; `list[str]` means “list containing str elements.”
    parts: list[str] = []
    # Each item in `content` is a block (e.g. text); we only collect text blocks.
    # `getattr(obj, "name", default)` reads an attribute safely if the SDK shape changes slightly.
    for block in getattr(message, "content", []):
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", ""))
    # Join blocks with newlines, then strip outer whitespace for clean printing.
    return "\n".join(parts).strip()


def main() -> None:
    # Load variables from `.env` in the current working directory (same folder if you run from there).
    load_dotenv()

    # Fail fast with a clear message if the key is missing after loading `.env`.
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set. Add it to your `.env` file.", file=sys.stderr)
        sys.exit(1)

    # Client reads `ANTHROPIC_API_KEY` from the environment automatically.
    client = Anthropic()

    # Instruction plus the paragraph we want summarized.
    user_message = (
        "Read the paragraph below and Give me 5 bullet points highlighting the key insights and goals from this text. "
        "Use clear, fluent English. Do not add a title or bullet points—only the three sentences.\n\n"
        f"{KENYA_TECH_PARAGRAPH}"
    )

    # Send the request: model id, token budget, and one chat turn (`messages` is a list of role/content dicts).
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}],
    )

    # Pull the assistant’s text from the structured response.
    summary = extract_text_from_message(response)

    # Print only the summary, with a short label for readability in the terminal.
    print("\n--- Summary (3 sentences) ---\n")
    print(summary)
    print()


# Run `main()` only when this file is executed directly (not when imported as a module).
if __name__ == "__main__":
    main()
