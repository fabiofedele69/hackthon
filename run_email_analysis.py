# FILE: run_email_analysis.py

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from mavric_react_loop import create_react_loop


def load_email_json(input_path: Path) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a JSON file")

    with input_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_user_message(email_json: dict) -> str:
    return (
        "Analyze the following control testing email JSON and identify what is missing. "
        "Return a structured analysis with known facts, missing information, missing evidence, "
        "clarification questions, recommended next action, and audit notes.\n\n"
        f"{json.dumps(email_json, indent=2)}"
    )


def extract_text_response(result) -> str:
    """
    The exact result structure can vary depending on the MAVRIC/LangGraph wrapper.
    This function tries common LangGraph response formats.
    """

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


def save_analysis(input_path: Path, analysis: str) -> Path:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{input_path.stem}_analysis.md"
    output_path.write_text(analysis, encoding="utf-8")

    return output_path


def main() -> None:
    load_dotenv(override=True)

    input_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("input/control_testing_email_001.json")
    )

    email_json = load_email_json(input_file)
    user_message = build_user_message(email_json)

    agent = create_react_loop()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        }
    )

    analysis = extract_text_response(result)
    output_path = save_analysis(input_file, analysis)

    print("\n=== RFI Missing Information Analysis ===\n")
    print(analysis)
    print(f"\nAnalysis saved to: {output_path}")


if __name__ == "__main__":
    main()
