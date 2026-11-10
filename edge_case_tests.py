import csv
import os
from collections import Counter


DATA_DIR = "data"


REQUIRED_EDGE_CASES = {
    "expired_policy_citation",
    "unauthorized_routing",
    "unsupported_fact",
    "business_hours_sla_bug",
    "missing_escalation",
}


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)

    with open(
        path,
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def check_expired_policy(rows):
    matches = [
        row
        for row in rows
        if row["issue_type"] == "expired_policy_citation"
    ]

    return len(matches) > 0, len(matches)


def check_unauthorized_routing(rows):
    matches = [
        row
        for row in rows
        if row["issue_type"] == "unauthorized_routing"
    ]

    return len(matches) > 0, len(matches)


def check_unsupported_fact(rows):
    matches = [
        row
        for row in rows
        if row["issue_type"] == "unsupported_fact"
    ]

    return len(matches) > 0, len(matches)


def check_business_hours_sla(rows):
    matches = [
        row
        for row in rows
        if row["issue_type"] == "business_hours_sla_bug"
    ]

    return len(matches) > 0, len(matches)


def check_missing_escalation(rows):
    matches = [
        row
        for row in rows
        if row["issue_type"] == "missing_escalation"
    ]

    return len(matches) > 0, len(matches)


def main():

    print("=" * 65)
    print("ACADEMIC SUPPORT AI EDGE-CASE TESTS")
    print("=" * 65)

    ground_truth = load_csv("ground_truth.csv")

    print()
    print(f"Ground-truth records loaded: {len(ground_truth)}")

    print()
    print("REQUIRED EDGE CASES")
    print("-" * 65)

    tests = [
        (
            "Expired policy citation",
            check_expired_policy
        ),
        (
            "Unauthorized routing",
            check_unauthorized_routing
        ),
        (
            "Unsupported fact",
            check_unsupported_fact
        ),
        (
            "Business-hours SLA bug",
            check_business_hours_sla
        ),
        (
            "Missing escalation",
            check_missing_escalation
        ),
    ]

    passed = 0
    failed = 0

    for name, test_function in tests:

        success, count = test_function(
            ground_truth
        )

        if success:
            print(
                f"[PASS] {name:<35} "
                f"detected {count} records"
            )
            passed += 1

        else:
            print(
                f"[FAIL] {name:<35} "
                f"detected 0 records"
            )
            failed += 1

    print()
    print("ANOMALY DISTRIBUTION")
    print("-" * 65)

    counts = Counter(
        row["issue_type"]
        for row in ground_truth
    )

    for issue_type, count in sorted(
        counts.items()
    ):
        print(
            f"{issue_type:<35} "
            f"{count}"
        )

    print()
    print("=" * 65)

    print(
        f"Tests passed: {passed}/{len(tests)}"
    )

    print(
        f"Tests failed: {failed}/{len(tests)}"
    )

    if failed == 0:
        print("STATUS: PASS")
    else:
        print("STATUS: REVIEW REQUIRED")

    print("=" * 65)


if __name__ == "__main__":
    main()