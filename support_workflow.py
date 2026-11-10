import csv
import os
import json
from datetime import datetime

from routing import (
    route_ticket,
    calculate_sla,
    calculate_sla_details,
    check_escalation,
)

from policy_retriever import (
    retrieve_policy,
    build_grounded_answer,
)


DATA_DIR = "data"


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_ticket(ticket_id):
    tickets = load_csv("ticket.csv")

    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            return ticket

    return None


def load_messages(ticket_id):
    messages = load_csv("message.csv")

    return [
        message
        for message in messages
        if message["ticket_id"] == ticket_id
    ]


def determine_request_date(ticket):
    created_at = ticket.get("created_at", "")

    if created_at:
        return created_at[:10]

    return "2026-01-01"


def process_ticket(ticket_id):

    # --------------------------------------------------
    # LOAD TICKET
    # --------------------------------------------------

    ticket = load_ticket(ticket_id)

    if not ticket:
        raise ValueError(
            f"Ticket not found: {ticket_id}"
        )

    request_date = determine_request_date(ticket)

    # --------------------------------------------------
    # 1. ROUTING
    # --------------------------------------------------

    routing = route_ticket(ticket)

    # --------------------------------------------------
    # 2. SLA
    # --------------------------------------------------

    # Calculate SLA hours from ticket priority
    sla_hours = calculate_sla(
        ticket["priority"]
    )

    # Calculate complete SLA details
    # including started_at and due_at
    sla = calculate_sla_details(ticket)

    # Make sure the SLA hours are consistent
    sla["sla_hours"] = sla_hours

    # --------------------------------------------------
    # 3. ESCALATION
    # --------------------------------------------------

    # IMPORTANT:
    # check_escalation() expects the complete ticket
    # dictionary, not ticket["priority"].
    escalation = check_escalation(
        ticket,
        routing,
        sla
    )

    # --------------------------------------------------
    # 4. POLICY RETRIEVAL
    # --------------------------------------------------

    query = ticket.get(
        "subject",
        ""
    )

    if not query:
        query = ticket.get(
            "description",
            ""
        )

    retrieval = retrieve_policy(
        query=query,
        request_date=request_date,
        domain=routing["domain"],
        top_k=3,
    )

    # --------------------------------------------------
    # 5. GROUNDED ANSWER
    # --------------------------------------------------

    answer = build_grounded_answer(
        query,
        retrieval
    )

    # --------------------------------------------------
    # 6. TRACEABILITY
    # --------------------------------------------------

    sources = []

    for source in retrieval.get("sources", []):

        sources.append({
            "source_type": source.get(
                "source_type",
                ""
            ),

            "source_id": source.get(
                "source_id",
                ""
            ),

            "title": source.get(
                "title",
                ""
            ),

            "version": source.get(
                "version",
                ""
            ),

            "effective": source.get(
                "effective",
                False
            ),

            "score": round(
                float(
                    source.get(
                        "score",
                        0
                    )
                ),
                4
            ),
        })

    # --------------------------------------------------
    # 7. MESSAGE HISTORY
    # --------------------------------------------------

    messages = load_messages(ticket_id)

    # --------------------------------------------------
    # 8. FINAL WORKFLOW RESULT
    # --------------------------------------------------

    return {

        "ticket": {
            "ticket_id": ticket["ticket_id"],
            "requester_id": ticket["requester_id"],
            "category_id": ticket["category_id"],
            "priority": ticket["priority"],
            "status": ticket["status"],
            "created_at": ticket.get(
                "created_at"
            ),
        },

        "decision": {

            "routing": routing,

            "sla_hours": sla_hours,

            "sla": {
                "priority": sla.get(
                    "priority"
                ),

                "sla_hours": sla.get(
                    "sla_hours"
                ),

                "started_at": sla.get(
                    "started_at"
                ),

                "due_at": sla.get(
                    "due_at"
                ),
            },

            "escalation_required": escalation,
        },

        "policy": {

            "retrieval_status": retrieval.get(
                "status"
            ),

            "confidence": retrieval.get(
                "confidence"
            ),

            "sources": sources,
        },

        "response": {

            "answer": answer.get(
                "answer",
                ""
            ),

            "citation": answer.get(
                "citation",
                ""
            ),

            "grounded": answer.get(
                "grounded",
                False
            ),
        },

        "traceability": {

            "request_date": request_date,

            "message_count": len(
                messages
            ),

            "source_count": len(
                sources
            ),

            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
        },
    }


def save_result(
    result,
    filename="outputs/workflow_result.json"
):

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=2
        )


def main():

    tickets = load_csv(
        "ticket.csv"
    )

    if not tickets:
        print("No tickets found.")
        return

    test_ticket_id = tickets[0]["ticket_id"]

    print()
    print("=" * 60)
    print(
        "ACADEMIC SUPPORT AI END-TO-END WORKFLOW"
    )
    print("=" * 60)

    print()
    print(
        "Processing:",
        test_ticket_id
    )

    result = process_ticket(
        test_ticket_id
    )

    # --------------------------------------------------
    # ROUTING
    # --------------------------------------------------

    print()
    print("ROUTING")
    print("-------")

    print(
        "Domain:",
        result["decision"]["routing"]["domain"]
    )

    print(
        "Team:",
        result["decision"]["routing"]["assigned_team"]
    )

    print(
        "Routing status:",
        result["decision"]["routing"]["routing_status"]
    )

    # --------------------------------------------------
    # SLA
    # --------------------------------------------------

    print()
    print("SLA")
    print("---")

    print(
        "SLA hours:",
        result["decision"]["sla_hours"]
    )

    print(
        "Started at:",
        result["decision"]["sla"]["started_at"]
    )

    print(
        "Due at:",
        result["decision"]["sla"]["due_at"]
    )

    # --------------------------------------------------
    # ESCALATION
    # --------------------------------------------------

    print()
    print("ESCALATION")
    print("----------")

    print(
        "Required:",
        result["decision"]["escalation_required"]
    )

    # --------------------------------------------------
    # POLICY RETRIEVAL
    # --------------------------------------------------

    print()
    print("POLICY RETRIEVAL")
    print("----------------")

    print(
        "Status:",
        result["policy"]["retrieval_status"]
    )

    print(
        "Confidence:",
        result["policy"]["confidence"]
    )

    print(
        "Sources:",
        result["traceability"]["source_count"]
    )

    # --------------------------------------------------
    # GROUNDED RESPONSE
    # --------------------------------------------------

    print()
    print("GROUNDED RESPONSE")
    print("------------------")

    print(
        result["response"]["answer"]
    )

    print()
    print("Citation:")

    print(
        result["response"]["citation"]
    )

    print()
    print(
        "Grounded:",
        result["response"]["grounded"]
    )

    # --------------------------------------------------
    # TRACEABILITY
    # --------------------------------------------------

    print()
    print("TRACEABILITY")
    print("------------")

    print(
        "Messages:",
        result["traceability"]["message_count"]
    )

    print(
        "Policy sources:",
        result["traceability"]["source_count"]
    )

    print(
        "Request date:",
        result["traceability"]["request_date"]
    )

    # --------------------------------------------------
    # SAVE RESULT
    # --------------------------------------------------

    save_result(
        result
    )

    print()
    print(
        "Saved: outputs/workflow_result.json"
    )

    print()
    print("=" * 60)
    print(
        "WORKFLOW TEST COMPLETED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()