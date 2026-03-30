from __future__ import annotations

import json
from pathlib import Path


REQUIRED_ROOT_FILES = [
    "agent.yaml",
    "SOUL.md",
    "SKILL.md",
]
REQUIRED_SKILL_DIRS = [
    "skills/support-resolution",
    "skills/escalation-triage",
]


def validate_structure(project_root: Path) -> dict:
    missing = []
    present = []

    for file_name in REQUIRED_ROOT_FILES:
        path = project_root / file_name
        if path.exists() and path.is_file():
            present.append(file_name)
        else:
            missing.append(file_name)

    skills_dir = project_root / "skills"
    if skills_dir.exists() and skills_dir.is_dir():
        present.append("skills/")
    else:
        missing.append("skills/")

    for skill_path in REQUIRED_SKILL_DIRS:
        path = project_root / skill_path
        if path.exists() and path.is_dir() and (path / "SKILL.md").exists():
            present.append(f"{skill_path}/SKILL.md")
        else:
            missing.append(f"{skill_path}/SKILL.md")

    score = round(len(present) / (len(present) + len(missing)), 3) if (present or missing) else 0.0
    return {
        "project_root": str(project_root),
        "passed": len(missing) == 0,
        "compliance_score": score,
        "present": present,
        "missing": missing,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    report = validate_structure(project_root)
    output_path = project_root / "gitagent_structure_report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved structure report to {output_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
