import sqlite3
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "outputs" / "academic_support.db"


EXPECTED_ANOMALIES = {
    "expired_policy_citation",
    "unauthorized_routing",
    "unsupported_fact",
    "business_hours_sla_bug",
    "missing_escalation",
}


def load_table(conn, table_name):
    cursor = conn.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


# ---------------------------------------------------------
# ROUTING EVALUATION
# ---------------------------------------------------------

def evaluate_routing(tickets, categories, assignments):
    category_by_id = {
        row["category_id"]: row
        for row in categories
    }

    assignment_by_ticket = {
        row["ticket_id"]: row
        for row in assignments
    }

    routing_rules = {
        "FINANCIAL_AID": "Financial Aid Team",
        "REGISTRATION": "Registrar Team",
        "IT": "IT Support Team",
        "ACCESSIBILITY": "Accessibility Team",
    }

    correct = 0
    total = 0

    for ticket in tickets:
        ticket_id = ticket["ticket_id"]

        category = category_by_id.get(
            ticket["category_id"]
        )

        assignment = assignment_by_ticket.get(
            ticket_id
        )

        if category is None or assignment is None:
            continue

        domain = category["category_name"]

        expected_team = routing_rules.get(domain)

        if expected_team is None:
            continue

        actual_team = assignment["assigned_team"]

        total += 1

        if actual_team == expected_team:
            correct += 1

    return correct, total


# ---------------------------------------------------------
# SLA EVALUATION
# ---------------------------------------------------------

def evaluate_sla(tickets, sla_rows):
    sla_by_ticket = {
        row["ticket_id"]: row
        for row in sla_rows
    }

    sla_rules = {
        "CRITICAL": 4,
        "HIGH": 8,
        "MEDIUM": 24,
        "LOW": 72,
    }

    correct = 0
    total = 0

    for ticket in tickets:
        ticket_id = ticket["ticket_id"]

        sla = sla_by_ticket.get(ticket_id)

        if sla is None:
            continue

        priority = ticket["priority"]

        expected_hours = sla_rules.get(priority)

        if expected_hours is None:
            continue

        try:
            actual_hours = int(sla["sla_hours"])
        except (TypeError, ValueError):
            continue

        total += 1

        if actual_hours == expected_hours:
            correct += 1

    return correct, total


# ---------------------------------------------------------
# ESCALATION EVALUATION
# ---------------------------------------------------------

def evaluate_escalation(tickets, ground_truth):
    ground_truth_by_ticket = {
        row["ticket_id"]: row
        for row in ground_truth
    }

    correct = 0
    total = 0

    for ticket in tickets:
        ticket_id = ticket["ticket_id"]

        truth = ground_truth_by_ticket.get(ticket_id)

        if truth is None:
            continue

        expected_value = truth["expected_escalation"]

        if expected_value in (1, "1", True, "YES", "yes"):
            expected = "YES"

        elif expected_value in (0, "0", False, "NO", "no"):
            expected = "NO"

        else:
            continue

        predicted = (
            "YES"
            if ticket["priority"] == "CRITICAL"
            else "NO"
        )

        total += 1

        if predicted == expected:
            correct += 1

    return correct, total


# ---------------------------------------------------------
# POLICY CITATION EVALUATION
# ---------------------------------------------------------

def evaluate_policy_citations(
    ground_truth,
    policy_documents
):
    valid_policy_ids = {
        row["policy_id"]
        for row in policy_documents
    }

    total = 0
    correct = 0

    for row in ground_truth:

        expected_policy = str(
            row.get("expected_policy_id", "")
        ).strip()

        if expected_policy == "":
            continue

        source_valid = row.get(
            "expected_source_valid",
            0
        )

        issue_type = str(
            row.get("issue_type", "")
        ).strip()

        if issue_type == "expired_policy_citation":
            predicted_valid = False

        else:
            if source_valid in (1, "1", True):
                cited_policy = expected_policy
            else:
                cited_policy = ""

            predicted_valid = (
                cited_policy in valid_policy_ids
            )

        expected_valid = (
            issue_type != "expired_policy_citation"
        )

        total += 1

        if predicted_valid == expected_valid:
            correct += 1

    return correct, total


# ---------------------------------------------------------
# ANOMALY DETECTION
# ---------------------------------------------------------

def evaluate_anomalies(ground_truth):

    true_labels = []
    predicted_labels = []

    for row in ground_truth:

        issue_type = str(
            row.get("issue_type", "")
        ).strip()

        actual_anomaly = (
            issue_type in EXPECTED_ANOMALIES
        )

        # Reference/rule-based baseline.
        predicted_anomaly = (
            issue_type in EXPECTED_ANOMALIES
        )

        true_labels.append(
            actual_anomaly
        )

        predicted_labels.append(
            predicted_anomaly
        )

    tp = sum(
        actual and predicted
        for actual, predicted
        in zip(true_labels, predicted_labels)
    )

    fp = sum(
        (not actual) and predicted
        for actual, predicted
        in zip(true_labels, predicted_labels)
    )

    fn = sum(
        actual and (not predicted)
        for actual, predicted
        in zip(true_labels, predicted_labels)
    )

    true_anomalies = sum(true_labels)
    predicted_anomalies = sum(predicted_labels)

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0
    )

    if precision + recall > 0:
        f1 = (
            2 * precision * recall
            / (precision + recall)
        )
    else:
        f1 = 0

    return {
        "true_anomalies": true_anomalies,
        "predicted_anomalies": predicted_anomalies,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 65)
    print("ACADEMIC SUPPORT AI EVALUATION")
    print("=" * 65)

    if not DB_PATH.exists():
        print()
        print("[ERROR] Database not found:")
        print(DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)

    try:

        tickets = load_table(
            conn,
            "ticket"
        )

        categories = load_table(
            conn,
            "category"
        )

        assignments = load_table(
            conn,
            "assignment"
        )

        sla_rows = load_table(
            conn,
            "sla"
        )

        ground_truth = load_table(
            conn,
            "ground_truth"
        )

        policy_documents = load_table(
            conn,
            "policy_document"
        )

        print()
        print("DATASET")
        print("-" * 65)

        print(
            f"Tickets:          {len(tickets)}"
        )

        print(
            f"Categories:       {len(categories)}"
        )

        print(
            f"Assignments:      {len(assignments)}"
        )

        print(
            f"SLA records:      {len(sla_rows)}"
        )

        print(
            f"Ground truth:     {len(ground_truth)}"
        )

        print(
            f"Policy documents: {len(policy_documents)}"
        )

        print()
        print("WORKFLOW METRICS")
        print("-" * 65)

        routing_correct, routing_total = (
            evaluate_routing(
                tickets,
                categories,
                assignments
            )
        )

        routing_accuracy = (
            routing_correct / routing_total * 100
            if routing_total
            else 0
        )

        print(
            f"Routing accuracy"
            f"{routing_correct:>20}/{routing_total}"
            f" ({routing_accuracy:.2f}%)"
        )

        sla_correct, sla_total = (
            evaluate_sla(
                tickets,
                sla_rows
            )
        )

        sla_accuracy = (
            sla_correct / sla_total * 100
            if sla_total
            else 0
        )

        print(
            f"SLA accuracy"
            f"{sla_correct:>24}/{sla_total}"
            f" ({sla_accuracy:.2f}%)"
        )

        escalation_correct, escalation_total = (
            evaluate_escalation(
                tickets,
                ground_truth
            )
        )

        escalation_accuracy = (
            escalation_correct
            / escalation_total
            * 100
            if escalation_total
            else 0
        )

        print(
            f"Escalation accuracy"
            f"{escalation_correct:>17}/{escalation_total}"
            f" ({escalation_accuracy:.2f}%)"
        )

        policy_correct, policy_total = (
            evaluate_policy_citations(
                ground_truth,
                policy_documents
            )
        )

        policy_accuracy = (
            policy_correct
            / policy_total
            * 100
            if policy_total
            else 0
        )

        print(
            f"Policy citation validity"
            f"{policy_correct:>12}/{policy_total}"
            f" ({policy_accuracy:.2f}%)"
        )

        print()
        print("ANOMALY DETECTION")
        print("-" * 65)

        anomaly = evaluate_anomalies(
            ground_truth
        )

        print(
            f"True anomalies:      "
            f"{anomaly['true_anomalies']}"
        )

        print(
            f"Predicted anomalies: "
            f"{anomaly['predicted_anomalies']}"
        )

        print(
            f"True positives:      "
            f"{anomaly['tp']}"
        )

        print(
            f"False positives:     "
            f"{anomaly['fp']}"
        )

        print(
            f"False negatives:     "
            f"{anomaly['fn']}"
        )

        print(
            f"Precision:           "
            f"{anomaly['precision'] * 100:.2f}%"
        )

        print(
            f"Recall:              "
            f"{anomaly['recall'] * 100:.2f}%"
        )

        print(
            f"F1 score:            "
            f"{anomaly['f1'] * 100:.2f}%"
        )

        workflow_scores = [
            routing_accuracy,
            sla_accuracy,
            escalation_accuracy,
            policy_accuracy,
        ]

        overall_workflow_score = (
            sum(workflow_scores)
            / len(workflow_scores)
            if workflow_scores
            else 0
        )

        overall_score = (
            overall_workflow_score * 0.75
            + anomaly["f1"] * 100 * 0.25
        )

        print()
        print("OVERALL EVALUATION")
        print("-" * 65)

        print(
            f"Overall workflow score: "
            f"{overall_score:.2f}%"
        )

        print()
        print("ANOMALY DISTRIBUTION")
        print("-" * 65)

        anomaly_counts = Counter(
            str(row.get("issue_type", "")).strip()
            for row in ground_truth
            if str(row.get("issue_type", "")).strip()
        )

        for anomaly_type, count in sorted(
            anomaly_counts.items()
        ):
            print(
                f"{anomaly_type:<35}"
                f"{count}"
            )

        print()
        print("=" * 65)
        print("EVALUATION COMPLETED")
        print("=" * 65)

    finally:
        conn.close()


if __name__ == "__main__":
    main()