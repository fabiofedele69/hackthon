# FILE: run_rfi_clarification.py

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from mavric_react_loop import create_react_loop


def load_analysis_file(input_path: Path) -> str:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    return input_path.read_text(encoding="utf-8")


def build_user_message(analysis_content: str) -> str:
    return (
        "You are executing Phase 2 of the RFI workflow.\n\n"
        "The input is the Phase 1 analysis file. It may have a .md extension, "
        "but its content is JSON or JSON-like structured output.\n\n"
        "Use the entire file as context, but focus specifically on:\n"
        "1. clarification questions\n"
        "2. recommended next action\n"
        "3. audit notes\n\n"
        "Your task is to generate a structured RFI clarification package that can be reviewed by a human.\n\n"
        "Return the output with the following sections:\n\n"
        "## RFI Clarification Summary\n"
        "## Clarification Questions to Send\n"
        "## Missing Inputs Required Before Sending\n"
        "## Recommended Action\n"
        "## Human Review Checklist\n"
        "## Audit Notes\n\n"
        "Rules:\n"
        "- Do not invent facts, owners, due dates, control IDs, or evidence.\n"
        "- If a required value is missing, explicitly mark it as missing.\n"
        "- Do not claim that the RFI was sent.\n"
        "- Keep the result suitable for a regulated banking environment.\n\n"
        f"PHASE 1 ANALYSIS FILE CONTENT:\n{analysis_content}"
    )


def extract_text_response(result) -> str:
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        messages = result.get("messages")
        if messages:
            last_message = messages[-1]

            if isinstance(last_message, dict):
                return last_message.get("content", str(last_message))

            content = getattr(last_message, "content", None)
            if content:
                return content

        return json.dumps(result, indent=2, default=str)

    return str(result)


def save_clarification_package(input_path: Path, clarification_package: str) -> Path:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{input_path.stem}_clarification_package.md"
    output_path.write_text(clarification_package, encoding="utf-8")

    return output_path


def main() -> None:
    load_dotenv(override=True)

    input_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("output/control_testing_email_001_analysis.md")
    )

    analysis_content = load_analysis_file(input_file)
    user_message = build_user_message(analysis_content)

    agent = create_react_loop()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": f"rfi-clarification-{input_file.stem}"
            }
        },
    )

    clarification_package = extract_text_response(result)
    output_path = save_clarification_package(input_file, clarification_package)

    print("\n=== RFI Clarification Package ===\n")
    print(clarification_package)
    print(f"\nClarification package saved to: {output_path}")


if __name__ == "__main__":
    main()
