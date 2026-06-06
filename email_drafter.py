"""
CLI tool: draft customer service email replies using the Claude API.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

from anthropic import Anthropic
from dotenv import load_dotenv

# Model used for all Claude API calls in this script.
MODEL_NAME = "claude-sonnet-4-6"

# Log file where every drafted reply is appended for later reference.
DRAFT_LOG_FILE = "drafted_replies.txt"


def collect_multiline_message() -> str:
    """Read lines from stdin until the user types DONE on its own line."""
    print("Paste the customer's message below.")
    print("When finished, type DONE on a new line and press Enter:\n")

    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "DONE":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def build_prompt(business_name: str, customer_message: str) -> str:
    """Assemble the instruction sent to Claude with Kenya-specific context."""
    return f"""You are drafting a customer service email reply for a business based in Nairobi, Kenya.

Context for this reply:
- The business operates in Kenya; use British English spelling (e.g. colour, organise, centre).
- Prices and amounts should be in Kenyan Shillings (Ksh) when relevant.
- Tone and conventions should feel natural for Kenyan customer service (warm, respectful, clear).

Business name: {business_name}

Customer's message:
---
{customer_message}
---

Write a warm, professional email reply that:
1. Acknowledges the customer's feelings and concern.
2. Addresses their specific issue clearly.
3. Provides one clear next step they can take or expect.
4. Signs off exactly as: The team at {business_name}

Keep the entire reply under 100 words. Output only the email body—no subject line, no labels, no explanation."""


def save_draft_to_log(draft: str, business_name: str) -> None:
    """Append the draft to drafted_replies.txt with a timestamp and separators."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    separator = "-" * 60
    entry = (
        f"{separator}\n"
        f"{timestamp} | {business_name}\n"
        f"{separator}\n"
        f"{draft}\n"
        f"{separator}\n\n"
    )
    with open(DRAFT_LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(entry)


def extract_text_from_message(message: object) -> str:
    """Join all text blocks from Claude's reply."""
    parts: list[str] = []
    for block in getattr(message, "content", []):
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", ""))
    return "\n".join(parts).strip()


def main() -> None:
    # Load ANTHROPIC_API_KEY and other variables from `.env` in the working directory.
    load_dotenv()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set. Add it to your `.env` file.", file=sys.stderr)
        sys.exit(1)

    # Ask for the business name used in the sign-off and prompt context.
    business_name = input("Enter the business name: ").strip()
    if not business_name:
        print("Error: Business name cannot be empty.", file=sys.stderr)
        sys.exit(1)

    # Collect the customer's full message (may span many lines).
    customer_message = collect_multiline_message()
    if not customer_message:
        print("Error: Customer message cannot be empty.", file=sys.stderr)
        sys.exit(1)

    # Build the Kenya-aware instruction for Claude.
    user_prompt = build_prompt(business_name, customer_message)

    print("\nDrafting reply...\n")

    # Call Claude and print the result; catch API and network errors gracefully.
    try:
        client = Anthropic()
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1024,
            messages=[{"role": "user", "content": user_prompt}],
        )
        draft = extract_text_from_message(response)
    except Exception as exc:
        print(f"Sorry, we could not draft your reply right now: {exc}", file=sys.stderr)
        sys.exit(1)

    print("--- DRAFTED REPLY ---\n")
    print(draft)
    print()

    # Append this draft to the log file so the user keeps a history of all replies.
    try:
        save_draft_to_log(draft, business_name)
        print(f"Saved to {DRAFT_LOG_FILE}\n")
    except OSError as exc:
        print(f"Warning: Could not save to {DRAFT_LOG_FILE}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
