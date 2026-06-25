# FILE: run_rfi_decision.py

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from mavric_react_loop import create_react_loop


def load_input_file(input_path: Path) -> str:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return input_path.read_text(encoding="utf-8")


def build_user_message(gap_analysis_content: str) -> str:
    return (
        "You are executing Phase 4 of the RFI workflow: RFI Decision Engine.\n\n"
        "The input is the gap analysis produced from a control testing request.\n\n"
        "Your task is to decide whether an RFI should be opened.\n\n"
        "Return the output using this structure:\n\n"
        "## RFI Decision Summary\n"
        "## Decision\n"
        "Use one of: OPEN_RFI, REQUEST_CLARIFICATION, NO_RFI_REQUIRED, HUMAN_REVIEW_REQUIRED\n\n"
        "## Decision Rationale\n"
        "## Priority\n"
        "Use one of: LOW, MEDIUM, HIGH\n\n"
        "## Required Information Before RFI\n"
        "## Recommended Next Action\n"
        "## Audit Notes\n\n"
        "Rules:\n"
        "- Do not invent facts.\n"
        "- Use only the input content.\n"
        "- If the evidence is insufficient, recommend OPEN_RFI or REQUEST_CLARIFICATION.\n"
        "- If critical information is missing but the recipient or owner is unknown, recommend HUMAN_REVIEW_REQUIRED.\n"
        "- Do not claim that an RFI has been sent.\n"
        "- Keep the response suitable for a regulated banking environment.\n\n"
        f"GAP ANALYSIS INPUT:\n{gap_analysis_content}"
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


def save_decision(input_path: Path, decision: str) -> Path:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{input_path.stem}_rfi_decision.md"
    output_path.write_text(decision, encoding="utf-8")

    return output_path


def main() -> None:
    load_dotenv(override=True)

    input_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("output/control_testing_email_001_analysis_gap_analysis.md")
    )

    gap_analysis_content = load_input_file(input_file)
    user_message = build_user_message(gap_analysis_content)

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
                "thread_id": f"rfi-decision-{input_file.stem}"
            }
        },
    )

    decision = extract_text_response(result)
    output_path = save_decision(input_file, decision)

    print("\n=== RFI Decision ===\n")
    print(decision)
    print(f"\nRFI decision saved to: {output_path}")


if __name__ == "__main__":
    main()
