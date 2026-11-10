import csv
import os
from collections import Counter


DATA_DIR = "data"


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def check_file_exists(filename):
    path = os.path.join(DATA_DIR, filename)

    if os.path.exists(path):
        print(f"[PASS] Required file exists: {filename}")
        return True

    print(f"[FAIL] Missing required file: {filename}")
    return False


def check_unique_ids(rows, id_column, table_name):

    ids = [
        row[id_column]
        for row in rows
        if row.get(id_column)
    ]

    duplicates = [
        value
        for value, count in Counter(ids).items()
        if count > 1
    ]

    if duplicates:
        print(
            f"[FAIL] {table_name}.{id_column} "
            f"has {len(duplicates)} duplicate IDs"
        )
        return False

    print(
        f"[PASS] {table_name}.{id_column} "
        f"unique: {len(ids)} records"
    )

    return True


def check_foreign_keys(
    child_rows,
    child_column,
    parent_rows,
    parent_column,
    relationship_name
):

    parent_ids = {
        row[parent_column]
        for row in parent_rows
    }

    invalid = [
        row[child_column]
        for row in child_rows
        if row.get(child_column)
        and row[child_column] not in parent_ids
    ]

    if invalid:
        print(
            f"[FAIL] {relationship_name}: "
            f"{len(invalid)} invalid foreign keys"
        )
        return False

    print(
        f"[PASS] {relationship_name}"
    )

    return True


def check_enum(rows, column, allowed, table_name):

    invalid = [
        row[column]
        for row in rows
        if row.get(column)
        and row[column] not in allowed
    ]

    if invalid:
        print(
            f"[FAIL] {table_name}.{column}: "
            f"{len(invalid)} invalid values"
        )
        return False

    print(
        f"[PASS] {table_name}.{column} enum validation"
    )

    return True


def check_date_order(
    rows,
    start_column,
    end_column,
    table_name
):

    failures = 0

    for row in rows:

        start = row.get(start_column, "")
        end = row.get(end_column, "")

        if start and end:

            if start > end:
                failures += 1

    if failures:
        print(
            f"[FAIL] {table_name}: "
            f"{failures} invalid date ranges"
        )
        return False

    print(
        f"[PASS] {table_name} date ordering"
    )

    return True


def check_ticket_counts(tickets):

    expected = 5000

    actual = len(tickets)

    if actual == expected:
        print(
            f"[PASS] Ticket count: {actual}"
        )
        return True

    print(
        f"[FAIL] Ticket count: "
        f"expected {expected}, found {actual}"
    )

    return False


def check_message_counts(messages):

    expected = 20000

    actual = len(messages)

    if actual == expected:
        print(
            f"[PASS] Message count: {actual}"
        )
        return True

    print(
        f"[FAIL] Message count: "
        f"expected {expected}, found {actual}"
    )

    return False


def check_article_counts(articles):

    expected = 200

    actual = len(articles)

    if actual == expected:
        print(
            f"[PASS] Knowledge article count: {actual}"
        )
        return True

    print(
        f"[FAIL] Knowledge article count: "
        f"expected {expected}, found {actual}"
    )

    return False


def check_ground_truth(tickets, ground_truth):

    ticket_ids = {
        row["ticket_id"]
        for row in tickets
    }

    truth_ids = {
        row["ticket_id"]
        for row in ground_truth
    }

    missing = ticket_ids - truth_ids
    extra = truth_ids - ticket_ids

    if missing or extra:

        print(
            "[FAIL] Ground truth coverage mismatch"
        )

        if missing:
            print(
                f"       Missing: {len(missing)}"
            )

        if extra:
            print(
                f"       Extra: {len(extra)}"
            )

        return False

    print(
        "[PASS] Ground truth covers all tickets"
    )

    return True


def check_event_history(events):

    ticket_ids = {
        row["ticket_id"]
        for row in load_csv("ticket.csv")
    }

    invalid = [
        row["ticket_id"]
        for row in events
        if row.get("ticket_id")
        and row["ticket_id"] not in ticket_ids
    ]

    if invalid:

        print(
            f"[FAIL] Event history: "
            f"{len(invalid)} invalid ticket references"
        )

        return False

    print(
        f"[PASS] Event history references valid tickets: "
        f"{len(events)} events"
    )

    return True


def check_anomaly_labels(ground_truth):

    required_types = {
        "expired_policy_citation",
        "unauthorized_routing",
        "unsupported_fact",
        "business_hours_sla_bug",
        "missing_escalation",
    }

    found_types = {
        row.get("issue_type")
        for row in ground_truth
        if row.get("issue_type")
    }

    missing = required_types - found_types

    if missing:

        print(
            "[FAIL] Missing anomaly types:"
        )

        for item in sorted(missing):
            print(
                f"       - {item}"
            )

        return False

    print(
        "[PASS] Required anomaly types present"
    )

    for anomaly_type in sorted(required_types):

        count = sum(
            1
            for row in ground_truth
            if row.get("issue_type")
            == anomaly_type
        )

        print(
            f"       {anomaly_type}: {count}"
        )

    return True


def main():

    print()
    print("=" * 65)
    print("ACADEMIC SUPPORT AI DATA VALIDATION")
    print("=" * 65)

    required_files = [
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

    results = []

    print()
    print("1. REQUIRED FILES")
    print("-----------------")

    for filename in required_files:
        results.append(
            check_file_exists(filename)
        )

    requester = load_csv("requester.csv")
    roles = load_csv("role.csv")
    categories = load_csv("category.csv")
    terms = load_csv("term.csv")
    policies = load_csv("policy_document.csv")
    articles = load_csv("knowledge_article.csv")
    tickets = load_csv("ticket.csv")
    messages = load_csv("message.csv")
    assignments = load_csv("assignment.csv")
    assignment_sources = load_csv(
        "assignment_source.csv"
    )
    sla = load_csv("sla.csv")
    events = load_csv("event_history.csv")
    feedback = load_csv(
        "resolution_feedback.csv"
    )
    ground_truth = load_csv(
        "ground_truth.csv"
    )

    print()
    print("2. PRIMARY KEY CHECKS")
    print("---------------------")

    results.append(
        check_unique_ids(
            requester,
            "requester_id",
            "requester"
        )
    )

    results.append(
        check_unique_ids(
            roles,
            "role_id",
            "role"
        )
    )

    results.append(
        check_unique_ids(
            categories,
            "category_id",
            "category"
        )
    )

    results.append(
        check_unique_ids(
            terms,
            "term_id",
            "term"
        )
    )

    results.append(
        check_unique_ids(
            policies,
            "policy_id",
            "policy_document"
        )
    )

    results.append(
        check_unique_ids(
            articles,
            "article_id",
            "knowledge_article"
        )
    )

    results.append(
        check_unique_ids(
            tickets,
            "ticket_id",
            "ticket"
        )
    )

    results.append(
        check_unique_ids(
            messages,
            "message_id",
            "message"
        )
    )

    results.append(
        check_unique_ids(
            assignments,
            "assignment_id",
            "assignment"
        )
    )

    results.append(
        check_unique_ids(
            sla,
            "sla_id",
            "sla"
        )
    )

    print()
    print("3. FOREIGN KEY CHECKS")
    print("---------------------")

    results.append(
        check_foreign_keys(
            requester,
            "role_id",
            roles,
            "role_id",
            "requester.role_id -> role.role_id"
        )
    )

    results.append(
        check_foreign_keys(
            tickets,
            "requester_id",
            requester,
            "requester_id",
            "ticket.requester_id -> requester.requester_id"
        )
    )

    results.append(
        check_foreign_keys(
            tickets,
            "category_id",
            categories,
            "category_id",
            "ticket.category_id -> category.category_id"
        )
    )

    results.append(
        check_foreign_keys(
            tickets,
            "term_id",
            terms,
            "term_id",
            "ticket.term_id -> term.term_id"
        )
    )

    results.append(
        check_foreign_keys(
            articles,
            "policy_id",
            policies,
            "policy_id",
            "article.policy_id -> policy.policy_id"
        )
    )

    results.append(
        check_foreign_keys(
            messages,
            "ticket_id",
            tickets,
            "ticket_id",
            "message.ticket_id -> ticket.ticket_id"
        )
    )

    results.append(
        check_foreign_keys(
            assignments,
            "ticket_id",
            tickets,
            "ticket_id",
            "assignment.ticket_id -> ticket.ticket_id"
        )
    )

    results.append(
        check_foreign_keys(
            assignment_sources,
            "ticket_id",
            tickets,
            "ticket_id",
            "assignment_source.ticket_id -> ticket.ticket_id"
        )
    )

    results.append(
        check_foreign_keys(
            assignment_sources,
            "assignment_id",
            assignments,
            "assignment_id",
            "assignment_source.assignment_id -> assignment.assignment_id"
        )
    )

    results.append(
        check_foreign_keys(
            sla,
            "ticket_id",
            tickets,
            "ticket_id",
            "sla.ticket_id -> ticket.ticket_id"
        )
    )

    results.append(
        check_foreign_keys(
            events,
            "ticket_id",
            tickets,
            "ticket_id",
            "event_history.ticket_id -> ticket.ticket_id"
        )
    )

    results.append(
        check_foreign_keys(
            feedback,
            "ticket_id",
            tickets,
            "ticket_id",
            "feedback.ticket_id -> ticket.ticket_id"
        )
    )

    print()
    print("4. ENUM CHECKS")
    print("--------------")

    results.append(
        check_enum(
            tickets,
            "priority",
            {
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW",
            },
            "ticket"
        )
    )

    results.append(
        check_enum(
            tickets,
            "status",
            {
                "OPEN",
                "IN_PROGRESS",
                "WAITING",
                "RESOLVED",
                "CLOSED",
                "ESCALATED",
            },
            "ticket"
        )
    )

    print()
    print("5. DATE CHECKS")
    print("--------------")

    results.append(
        check_date_order(
            policies,
            "effective_from",
            "effective_to",
            "policy_document"
        )
    )

    print()
    print("6. SCALE CHECKS")
    print("---------------")

    results.append(
        check_ticket_counts(tickets)
    )

    results.append(
        check_message_counts(messages)
    )

    results.append(
        check_article_counts(articles)
    )

    print()
    print("7. GROUND TRUTH CHECK")
    print("----------------------")

    results.append(
        check_ground_truth(
            tickets,
            ground_truth
        )
    )

    print()
    print("8. EVENT HISTORY CHECK")
    print("----------------------")

    results.append(
        check_event_history(events)
    )

    print()
    print("9. ANOMALY COVERAGE")
    print("-------------------")

    results.append(
        check_anomaly_labels(
            ground_truth
        )
    )

    passed = sum(
        1
        for result in results
        if result
    )

    total = len(results)

    print()
    print("=" * 65)
    print(
        f"VALIDATION RESULT: "
        f"{passed}/{total} CHECKS PASSED"
    )
    print("=" * 65)

    if passed == total:
        print("STATUS: PASS")
    else:
        print("STATUS: REVIEW REQUIRED")


if __name__ == "__main__":
    main()