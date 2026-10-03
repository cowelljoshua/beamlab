"""Export the intentionally small DESIGN.md token subset without dependencies."""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
front = (root / "DESIGN.md").read_text(encoding="utf-8").split("---")[1]
tokens, section, role = [], None, None
for line in front.splitlines():
    if re.match(r"^[a-z]+:", line):
        section = line.split(":")[0]
    match = re.match(r'^  ([\w-]+): "(.+)"$', line)
    if match and section in ("colors", "rounded", "spacing"):
        prefix = {"colors": "color", "rounded": "radius", "spacing": "space"}[section]
        tokens.append(f"  --{prefix}-{match[1]}: {match[2]};")
    if section == "typography":
        if re.match(r"^  \w+:$", line):
            role = line.strip().rstrip(":")
        match = re.match(r'^    fontFamily: "(.+)"$', line)
        if match:
            tokens.append(f"  --font-{role}: {match[1]};")
(root / "web").mkdir(exist_ok=True)
(root / "web/tokens.css").write_text("/* Generated from DESIGN.md; do not edit. */\n:root {\n" + "\n".join(tokens) + "\n}\n", encoding="utf-8")
