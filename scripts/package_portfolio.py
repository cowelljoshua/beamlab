"""Copy only public demo assets into the prepared portfolio checkout."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / "portfolio-integration/public/beamlab"
files = [root / name for name in ("index.html", "README.md", "README.html")]
files += list((root / "web").glob("*.js")) + list((root / "web").glob("*.css"))
files += list((root / "docs").glob("*.md")) + list((root / "docs").glob("*.html"))
files += [root / "reports" / name for name in (
    "metrics.json", "test_predictions.csv", "ansys_verification.json", "demo-desktop.png")]
files += [root / "ansys/verification.inp"]
for source in files:
    destination = target / source.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
print(f"Copied {len(files)} public files to {target}")
