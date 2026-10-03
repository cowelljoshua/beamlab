"""Optional independent BEAM188 checks; uses an installed ANSYS license.

python ansys/verify.py --exe "C:/Program Files/ANSYS Inc/v261/ansys/bin/winx64/ANSYS261.exe"
Retains input decks and raw output. Does not create training labels.
"""
import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from beamnet.physics import reference, valid_domain
from beamnet.network import predict_artifact

CASES = [
    [500, 30, 25, 69000, 100],
    [800, 40, 40, 200000, 300],
    [300, 20, 20, 110000, 50],
    [900, 50, 30, 69000, 200],
    [600, 25, 50, 210000, 400],
    [1000, 60, 20, 200000, 100],
]


def deck(case, elements, index):
    length, width, height, modulus, force = case
    # Beam x=global X; default local y=global Y. RECT width is local y:
    # use height as first section dimension so Izz = width * height**3 / 12.
    return f"""/BATCH
/CLEAR,NOSTART
/FILNAME,beamcheck
/PREP7
ET,1,188
KEYOPT,1,3,3
MP,EX,1,{modulus}
MP,PRXY,1,0.3
SECTYPE,1,BEAM,RECT
SECDATA,{height},{width}
*DO,j,0,{elements}
N,j+1,j*{length}/{elements},0,0
*ENDDO
*DO,j,1,{elements}
E,j,j+1
*ENDDO
D,1,ALL,0
F,{elements+1},FY,-{force}
FINISH
/SOLU
ANTYPE,STATIC
NLGEOM,OFF
OUTRES,ALL,ALL
SOLVE
FINISH
/POST1
SET,LAST
*GET,tip,NODE,{elements+1},U,Y
*GET,reaction,NODE,1,RF,FY
ETABLE,rootmz,SMISC,3
*GET,moment,ELEM,1,ETAB,rootmz
stress=ABS(moment)*6/({width}*{height}**2)
*CFOPEN,case{index}_{elements},csv
*VWRITE,tip,reaction,stress
(E24.16,',',E24.16,',',E24.16)
*CFCLOS
FINISH
"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", required=True)
    args = p.parse_args()
    runs = ROOT / "ansys/runs"
    runs.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="verification-", dir=runs))
    assert np.all(valid_domain(CASES))
    commands = []
    for i, case in enumerate(CASES):
        for mesh in (4, 8, 16):
            commands.append(deck(case, mesh, i))
    commands.append("/EXIT,NOSAVE\n")
    inp = ROOT / "ansys/verification.inp"
    inp.write_text("\n".join(commands), encoding="ascii")
    output = run / "solver.out"
    cmd = [args.exe, "-b", "-smp", "-np", "2", "-dir", str(run),
           "-j", "beamcheck", "-i", str(inp), "-o", str(output)]
    print("Running 6 cases with 4, 8 and 16 beam elements (18 solves).", flush=True)
    result = subprocess.run(cmd, cwd=run, timeout=240, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode != 0:
        raise RuntimeError(f"ANSYS exit code {result.returncode}; inspect {output}")
    model = json.loads((ROOT / "artifacts/model.json").read_text())
    rows = []
    for i, case in enumerate(CASES):
        exact, nn = reference(case), predict_artifact(model, case)
        for mesh in (4, 8, 16):
            values = np.loadtxt(run / f"case{i}_{mesh}.csv", delimiter=",")
            tip, reaction, stress = abs(float(values[0])), float(values[1]), float(values[2])
            rows.append({"case": i + 1, "elements": mesh, "inputs": case,
                         "ansys_deflection_mm": tip, "ansys_stress_mpa": stress,
                         "reaction_n": reaction, "reference": exact.tolist(), "neural": nn.tolist(),
                         "deflection_vs_equation_pct": abs(tip / exact[0] - 1) * 100,
                         "stress_vs_equation_pct": abs(stress / exact[1] - 1) * 100,
                         "neural_vs_ansys_pct": (np.abs(nn / [tip, stress] - 1) * 100).tolist()})
    report = {"status": "completed", "solver": Path(args.exe).name, "cases": 6, "solves": 18,
              "element": "BEAM188, cubic interpolation, linear static, Poisson ratio 0.3",
              "purpose": "Independent spot checks, not training data or experimental validation",
              "note": "BEAM188 includes transverse shear; Euler-Bernoulli labels do not. Root bending stress recovered from element-end bending moment and section modulus.",
              "rows": rows,
              "max_deflection_vs_equation_pct": max(r["deflection_vs_equation_pct"] for r in rows),
              "max_stress_vs_equation_pct": max(r["stress_vs_equation_pct"] for r in rows),
              "max_reaction_relative_error": max(abs(r["reaction_n"] / r["inputs"][4] - 1) for r in rows),
              "max_neural_vs_ansys_pct": np.max([r["neural_vs_ansys_pct"] for r in rows], axis=0).tolist()}
    if report["max_deflection_vs_equation_pct"] > 2 or report["max_stress_vs_equation_pct"] > 0.1 or report["max_reaction_relative_error"] > 1e-6:
        raise RuntimeError("Verification failed; inspect raw solver outputs before accepting results.")
    (ROOT / "reports/ansys_verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (ROOT / "web/ansys-data.js").write_text("globalThis.BEAM_ANSYS=" + json.dumps(report) + ";\n", encoding="utf-8")
    # Keep compact evidence outside the ignored scratch folder.
    (ROOT / "reports/ansys_solver_output.txt").write_text(output.read_text(errors="replace"), encoding="utf-8")
    with (ROOT / "reports/ansys_checks.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
