import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
GENERATOR = BASE_DIR / "generate_data.py"
DATA_DIR = BASE_DIR / "data"

SEED = 20261022

TICKETS = 5000
ARTICLES = 200
MESSAGES = 20000
ANOMALIES = 100


FILES_TO_COMPARE = [
    "requester.csv",
    "role.csv",
    "category.csv",
    "term.csv",
    "policy_document.csv",
    "knowledge_article.csv",
    "ticket.csv",
    "message.csv",
    "assignment.csv",
    "assignment_source.csv",
    "sla.csv",
    "event_history.csv",
    "resolution_feedback.csv",
    "ground_truth.csv",
    "source_manifest.csv",
]


# ============================================================
# SHA256
# ============================================================

def sha256_file(path):

    sha = hashlib.sha256()

    with open(
        path,
        "rb",
    ) as f:

        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            sha.update(chunk)

    return sha.hexdigest()


# ============================================================
# CSV ROW COUNT
# ============================================================

def count_rows(path):

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        return max(
            sum(1 for _ in f) - 1,
            0,
        )


# ============================================================
# RUN GENERATOR
# ============================================================

def run_generator():

    command = [
        sys.executable,
        str(GENERATOR),

        "--tickets",
        str(TICKETS),

        "--articles",
        str(ARTICLES),

        "--messages",
        str(MESSAGES),

        "--seed",
        str(SEED),

        "--anomalies",
        str(ANOMALIES),
    ]

    env = os.environ.copy()

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    print(result.stdout)

    if result.returncode != 0:

        print(result.stderr)

        raise RuntimeError(
            "Data generator failed."
        )

    if not DATA_DIR.exists():

        raise RuntimeError(
            f"Data directory was not created: {DATA_DIR}"
        )


# ============================================================
# COPY GENERATED DATASET
# ============================================================

def snapshot_dataset(destination_dir):

    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    copied = 0

    for filename in FILES_TO_COMPARE:

        source = DATA_DIR / filename
        destination = destination_dir / filename

        if not source.exists():

            raise RuntimeError(
                f"Expected generated file not found: {source}"
            )

        shutil.copy2(
            source,
            destination,
        )

        copied += 1

    return copied


# ============================================================
# COMPARE TWO RUNS
# ============================================================

def compare_runs(
    run1_dir,
    run2_dir,
):

    print()
    print("=" * 65)
    print("COMPARISON")
    print("-" * 65)

    all_passed = True

    for filename in FILES_TO_COMPARE:

        file1 = run1_dir / filename
        file2 = run2_dir / filename

        # ----------------------------------------------------
        # Check RUN 1
        # ----------------------------------------------------

        if not file1.exists():

            print(
                f"[FAIL] {filename:<28} "
                "missing from RUN 1"
            )

            all_passed = False
            continue

        # ----------------------------------------------------
        # Check RUN 2
        # ----------------------------------------------------

        if not file2.exists():

            print(
                f"[FAIL] {filename:<28} "
                "missing from RUN 2"
            )

            all_passed = False
            continue

        # ----------------------------------------------------
        # Row counts
        # ----------------------------------------------------

        rows1 = count_rows(file1)
        rows2 = count_rows(file2)

        # ----------------------------------------------------
        # SHA256
        # ----------------------------------------------------

        hash1 = sha256_file(file1)
        hash2 = sha256_file(file2)

        # ----------------------------------------------------
        # Compare
        # ----------------------------------------------------

        if (
            rows1 == rows2
            and hash1 == hash2
        ):

            print(
                f"[PASS] {filename:<28} "
                f"rows={rows1:<6} "
                "SHA256 MATCH"
            )

        else:

            print(
                f"[FAIL] {filename:<28}"
            )

            print(
                f"       Rows: "
                f"{rows1} vs {rows2}"
            )

            print(
                f"       Hash 1: "
                f"{hash1}"
            )

            print(
                f"       Hash 2: "
                f"{hash2}"
            )

            all_passed = False

    print()
    print("=" * 65)

    if all_passed:

        print(
            "REPRODUCIBILITY RESULT: PASS"
        )

        print(
            "Same seed produced identical "
            "row counts and SHA256 checksums."
        )

    else:

        print(
            "REPRODUCIBILITY RESULT: FAIL"
        )

        print(
            "The two generated datasets "
            "are not identical."
        )

    print("=" * 65)

    return all_passed


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print(
        "ACADEMIC SUPPORT AI REPRODUCIBILITY TEST"
    )
    print("=" * 65)

    print(
        f"\nSeed: {SEED}"
    )

    print(
        f"Tickets: {TICKETS}"
    )

    print(
        f"Articles: {ARTICLES}"
    )

    print(
        f"Messages: {MESSAGES}"
    )

    print(
        f"Anomalies: {ANOMALIES}"
    )

    # --------------------------------------------------------
    # Create temporary comparison directory
    # --------------------------------------------------------

    temp_root = Path(
        tempfile.mkdtemp(
            prefix="academic_support_repro_"
        )
    )

    run1_dir = temp_root / "run1"
    run2_dir = temp_root / "run2"

    try:

        # ====================================================
        # RUN 1
        # ====================================================

        print()
        print("Generating RUN 1...")
        print()

        run_generator()

        copied1 = snapshot_dataset(
            run1_dir
        )

        print()
        print(
            f"RUN 1 snapshot saved: "
            f"{copied1} files"
        )

        # ====================================================
        # RUN 2
        # ====================================================

        print()
        print("Generating RUN 2...")
        print()

        run_generator()

        copied2 = snapshot_dataset(
            run2_dir
        )

        print()
        print(
            f"RUN 2 snapshot saved: "
            f"{copied2} files"
        )

        # ====================================================
        # COMPARE
        # ====================================================

        success = compare_runs(
            run1_dir,
            run2_dir,
        )

        print()

        print(
            "Temporary reproducibility "
            "test directory:"
        )

        print(temp_root)

        print()

        if success:

            print(
                "The dataset is reproducible."
            )

        else:

            print(
                "The dataset is NOT reproducible."
            )

        return success

    finally:

        # Keep temporary directory so it can be inspected
        # if the comparison fails.
        pass


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    success = main()

    sys.exit(
        0 if success else 1
    )