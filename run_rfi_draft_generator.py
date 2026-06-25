# FILE: run_rfi_draft_generator.py

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from mavric_react_loop import create_react_loop


def load_input_file(input_path: Path) -> str:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return input_path.read_text(encoding="utf-8")


def build_user_message(decision_content: str) -> str:
    return (
        "You are executing Phase 5 of the RFI workflow: RFI Draft Generator.\n\n"
        "The input is the RFI decision and supporting gap analysis from a control testing request.\n\n"
        "Your task is to generate a human-reviewable draft RFI message.\n\n"
        "Return the output using this structure:\n\n"
        "## Draft RFI Subject\n"
        "## Draft RFI Message\n"
        "## Requested Information\n"
        "## Requested Evidence\n"
        "## Clarification Questions\n"
        "## Missing Inputs Before Sending\n"
        "## Human Review Checklist\n"
        "## Audit Notes\n\n"
        "Rules:\n"
        "- Do not invent facts, owners, due dates, control IDs, test case IDs, or evidence.\n"
        "- If the recipient or owner is missing, mark it as missing and do not address the message to a named person.\n"
        "- Do not claim that the RFI has been sent.\n"
        "- The output is only a draft for human review.\n"
        "- Keep the language professional and suitable for a regulated banking environment.\n\n"
        f"RFI DECISION INPUT:\n{decision_content}"
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


def save_rfi_draft(input_path: Path, draft: str) -> Path:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{input_path.stem}_rfi_draft.md"
    output_path.write_text(draft, encoding="utf-8")

    return output_path


def main() -> None:
    load_dotenv(override=True)

    input_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("output/control_testing_email_001_analysis_gap_analysis_rfi_decision.md")
    )

    decision_content = load_input_file(input_file)
    user_message = build_user_message(decision_content)

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
                "thread_id": f"rfi-draft-{input_file.stem}"
            }
        },
    )

    draft = extract_text_response(result)
    output_path = save_rfi_draft(input_file, draft)

    print("\n=== RFI Draft ===\n")
    print(draft)
    print(f"\nRFI draft saved to: {output_path}")


if __name__ == "__main__":
    main()
