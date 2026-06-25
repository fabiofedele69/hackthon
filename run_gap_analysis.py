# FILE: run_gap_analysis.py

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from mavric_react_loop import create_react_loop


def load_input_file(input_path: Path) -> str:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    return input_path.read_text(encoding="utf-8")


def build_user_message(analysis_content: str) -> str:
    return (
        "You are executing Phase 3 of the RFI workflow: Gap Analysis.\n\n"
        "The input is a structured analysis of a control testing request. "
        "It may be stored in a .md file but the content is JSON or JSON-like structured content.\n\n"
        "Your task is to identify what is still missing before the control testing process can continue.\n\n"
        "Focus on:\n"
        "- missing control metadata\n"
        "- missing ownership information\n"
        "- missing evidence\n"
        "- missing documentation\n"
        "- unclear control execution details\n"
        "- unclear frequency or review period\n"
        "- unclear systems or applications in scope\n"
        "- missing approval or sign-off evidence\n\n"
        "Return the output using this structure:\n\n"
        "## Gap Analysis Summary\n"
        "## Identified Gaps\n"
        "## Missing Evidence\n"
        "## Missing Metadata\n"
        "## Ambiguities\n"
        "## Risk / Impact Assessment\n"
        "## Recommended Next Action\n"
        "## Audit Notes\n\n"
        "Rules:\n"
        "- Do not invent facts.\n"
        "- Use only the input content.\n"
        "- If information is unavailable, mark it as missing.\n"
        "- If information is unclear, mark it as ambiguous.\n"
        "- Do not claim that an RFI has been sent.\n"
        "- Keep the response suitable for a regulated banking environment.\n\n"
        f"INPUT CONTENT:\n{analysis_content}"
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


def save_gap_analysis(input_path: Path, gap_analysis: str) -> Path:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{input_path.stem}_gap_analysis.md"
    output_path.write_text(gap_analysis, encoding="utf-8")

    return output_path


def main() -> None:
    load_dotenv(override=True)

    input_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("output/control_testing_email_001_analysis.md")
    )

    analysis_content = load_input_file(input_file)
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
                "thread_id": f"gap-analysis-{input_file.stem}"
            }
        },
    )

    gap_analysis = extract_text_response(result)
    output_path = save_gap_analysis(input_file, gap_analysis)

    print("\n=== Gap Analysis ===\n")
    print(gap_analysis)
    print(f"\nGap analysis saved to: {output_path}")


if __name__ == "__main__":
    main()
