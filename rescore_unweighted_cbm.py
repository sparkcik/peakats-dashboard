#!/usr/bin/env python3
"""
RESCORE 42 UNWEIGHTED CBM Candidates on Gemini 3 Flash
Run from your #PEAKATS directory (or anywhere with access to processed folders)

Usage:
    python rescore_unweighted_cbm.py /path/to/#PEAKATS

What it does:
    1. Searches your #PEAKATS folder tree for the 42 resume PDFs
    2. Copies found resumes to a temp staging folder
    3. Runs peak_rig_processor_v2.py against them (client=cbm)
    4. Cleans up staging folder
    5. Reports what was found/missing
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# The 42 UNWEIGHTED resume filenames from PEAKATS
TARGET_RESUMES = [
    "ResumePabloAlipatJr.pdf",
    "ResumeSYLVESTERARIZI.pdf",
    "ResumeShanathiaDyer.pdf",
    "ResumeDelethaBrooks.pdf",
    "ResumeMinwooNam.pdf",
    "ResumeKimberlyGreen.pdf",
    "ResumePriscillaJohnson.pdf",
    "ResumeAbrianChampion.pdf",
    "ResumeAARONGRATE.pdf",
    "ResumeMylicVanison.pdf",
    "ResumeTajahLewis.pdf",
    "ResumeShahidahMubarak-Hadi.pdf",
    "ResumeJhonatanAlvarez.pdf",
    "ResumeNataviaColeman.pdf",
    "ResumeEricFigueroa.pdf",
    "ResumeStuartDorsey.pdf",
    "ResumeSedrickHicks.pdf",
    "ResumeSamuelRobinson.pdf",
    "Resumeneveenwahbi.pdf",
    "ResumeBrandonSawyer.pdf",
    "ResumeCarmenRelerford.pdf",
    "ResumeCandiceThomas.pdf",
    "ResumeDavidCathey.pdf",
    "ResumeJoesiahGarmon.pdf",
    "ResumeRannesiaChumney.pdf",
    "ResumeMichaelThompson.pdf",
    "ResumeChadSteinwinder.pdf",
    "ResumeAlzhanMailibai.pdf",
    "ResumeLanenciaAndrews.pdf",
    "ResumeDiamondHarris-Moore.pdf",
    "ResumeRodrickDurden.pdf",
    "ResumeGwendolynJackson.pdf",
    "ResumeEricRiggins.pdf",
    "ResumeYolandaDaniel.pdf",
    "ResumeSimonTrinidad.pdf",
    "ResumeJamarGraham.pdf",
    "ResumeIrisHernández.pdf",
    "ResumeCarlosReinoso.pdf",
    "ResumeDanielMurrell.pdf",
    "ResumeAnnaButler.pdf",
    "ResumeROBERTORAWLINS.pdf",
    "ResumeJesseRoot.pdf",
]


def find_resumes(search_root: Path) -> dict:
    """Recursively search for target resumes. Returns {filename: full_path}"""
    found = {}
    target_set = {f.lower() for f in TARGET_RESUMES}
    
    print(f"Searching {search_root} for {len(TARGET_RESUMES)} resumes...")
    
    for root, dirs, files in os.walk(search_root):
        # Skip hidden dirs and staging folder
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '_rescore_staging']
        
        for f in files:
            if f.lower() in target_set and f.lower() not in {v.name.lower() for v in found.values()}:
                found[f] = Path(root) / f
    
    return found


def main():
    if len(sys.argv) < 2:
        print("Usage: python rescore_unweighted_cbm.py /path/to/#PEAKATS")
        print("\nPoint this at your #PEAKATS folder (or parent). It will:")
        print("  1. Find the 42 UNWEIGHTED resumes in subfolders")
        print("  2. Stage them in a temp folder")
        print("  3. Run the RIG processor (Gemini 3 Flash)")
        print("  4. Clean up")
        sys.exit(1)
    
    search_root = Path(sys.argv[1]).expanduser()
    if not search_root.exists():
        print(f"❌ Path not found: {search_root}")
        sys.exit(1)
    
    # Step 1: Find resumes
    found = find_resumes(search_root)
    missing = [f for f in TARGET_RESUMES if f not in found]
    
    print(f"\n✅ Found: {len(found)}/{len(TARGET_RESUMES)}")
    if missing:
        print(f"⚠️  Missing: {len(missing)}")
        for m in missing:
            print(f"    - {m}")
    
    if not found:
        print("❌ No resumes found. Check your path.")
        sys.exit(1)
    
    # Step 2: Stage resumes
    staging = search_root / "_rescore_staging"
    staging.mkdir(exist_ok=True)
    
    print(f"\nStaging {len(found)} resumes to {staging}...")
    for filename, source_path in found.items():
        shutil.copy2(str(source_path), str(staging / filename))
    
    # Step 3: Find processor
    processor_candidates = [
        search_root / "scripts" / "peak_rig_processor_v2.py",
        search_root / "peak_rig_processor_v2.py",
        Path.cwd() / "peak_rig_processor_v2.py",
    ]
    
    processor_path = None
    for p in processor_candidates:
        if p.exists():
            processor_path = p
            break
    
    if not processor_path:
        print(f"\n⚠️  Could not find peak_rig_processor_v2.py automatically.")
        print(f"   Resumes are staged at: {staging}")
        print(f"   Run manually: python peak_rig_processor_v2.py {staging} cbm")
        return
    
    print(f"\nUsing processor: {processor_path}")
    print(f"Running RIG on {len(found)} resumes (client=cbm)...\n")
    print("=" * 60)
    
    # Step 4: Run processor
    result = subprocess.run(
        [sys.executable, str(processor_path), str(staging), "cbm"],
        cwd=str(processor_path.parent)
    )
    
    print("=" * 60)
    
    # Step 5: Cleanup
    if result.returncode == 0:
        print(f"\n🧹 Cleaning up staging folder...")
        shutil.rmtree(staging, ignore_errors=True)
        print("✅ Done! Check PEAKATS for updated scores.")
    else:
        print(f"\n⚠️  Processor exited with code {result.returncode}")
        print(f"   Staging folder preserved at: {staging}")
        print("   Review errors above, then delete staging manually.")


if __name__ == "__main__":
    main()
