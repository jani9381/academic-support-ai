import csv
import os
from datetime import datetime, timedelta


DATA_DIR = "data"


# ==========================================================
# ROUTING RULES
# ==========================================================

ROUTING_RULES = {
    "FINANCIAL_AID": "Financial Aid Team",
    "REGISTRATION": "Registrar Team",
    "IT": "IT Support Team",
    "ACCESSIBILITY": "Accessibility Team",
}


# ==========================================================
# SLA RULES
# ==========================================================

SLA_HOURS = {
    "CRITICAL": 4,
    "HIGH": 8,
    "MEDIUM": 24,
    "LOW": 72,
}


# ==========================================================
# LOAD CSV
# ==========================================================

def load_csv(filename):

    path = os.path.join(
        DATA_DIR,
        filename
    )

    if not os.path.exists(path):
        return []

    with open(
        path,
        "r",
        encoding="utf-8",
        newline=""
    ) as f:

        return list(
            csv.DictReader(f)
        )


# ==========================================================
# LOAD CATEGORIES
# ==========================================================

def load_categories():

    return load_csv(
        "category.csv"
    )


# ==========================================================
# LOAD TICKETS
# ==========================================================

def load_tickets():

    return load_csv(
        "ticket.csv"
    )


# ==========================================================
# FIND CATEGORY DOMAIN
# ==========================================================

def get_category_domain(
    category_id,
    categories=None
):

    if categories is None:
        categories = load_categories()

    for category in categories:

        if category["category_id"] == category_id:

            return category["category_name"]

    return None


# ==========================================================
# ROUTE TICKET
# ==========================================================

def route_ticket(ticket):

    categories = load_categories()

    category_id = ticket.get(
        "category_id",
        ""
    )

    domain = get_category_domain(
        category_id,
        categories
    )

    if domain in ROUTING_RULES:

        assigned_team = ROUTING_RULES[
            domain
        ]

        routing_status = "AUTO_ROUTED"

    else:

        assigned_team = "Human Review Team"

        routing_status = "ESCALATED"

    return {

        "ticket_id": ticket.get(
            "ticket_id"
        ),

        "domain": domain,

        "assigned_team": assigned_team,

        "routing_status": routing_status,
    }


# ==========================================================
# CALCULATE SLA HOURS
# ==========================================================

def calculate_sla(priority):

    priority = str(
        priority
    ).upper()

    return SLA_HOURS.get(
        priority,
        24
    )


# ==========================================================
# CALCULATE SLA DETAILS
# ==========================================================

def calculate_sla_details(ticket):

    priority = str(
        ticket.get(
            "priority",
            "MEDIUM"
        )
    ).upper()

    sla_hours = calculate_sla(
        priority
    )

    created_at = ticket.get(
        "created_at",
        ""
    )

    start_time = None

    # ------------------------------------------------------
    # Parse ticket creation time
    # ------------------------------------------------------

    if created_at:

        try:

            start_time = datetime.strptime(
                created_at,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            try:

                start_time = datetime.fromisoformat(
                    created_at
                )

            except Exception:

                start_time = None

    # ------------------------------------------------------
    # Fallback
    # ------------------------------------------------------

    if start_time is None:

        start_time = datetime(
            2026,
            1,
            1,
            0,
            0,
            0
        )

    due_at = (
        start_time
        + timedelta(hours=sla_hours)
    )

    return {

        "priority": priority,

        "sla_hours": sla_hours,

        "started_at": start_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "due_at": due_at.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }


# ==========================================================
# ESCALATION DECISION
# ==========================================================

def check_escalation(
    ticket,
    routing=None,
    sla=None
):

    priority = str(
        ticket.get(
            "priority",
            "MEDIUM"
        )
    ).upper()

    status = str(
        ticket.get(
            "status",
            ""
        )
    ).upper()

    # ------------------------------------------------------
    # RULE 1
    # Critical tickets require escalation
    # ------------------------------------------------------

    if priority == "CRITICAL":

        return True

    # ------------------------------------------------------
    # RULE 2
    # Unknown/unrecognized routing requires human review
    # ------------------------------------------------------

    if routing:

        if routing.get(
            "routing_status"
        ) == "ESCALATED":

            return True

    # ------------------------------------------------------
    # RULE 3
    # Resolved/closed tickets should not be escalated
    # simply because their historical SLA date is in the past.
    # ------------------------------------------------------

    if status in {
        "RESOLVED",
        "CLOSED"
    }:

        return False

    # ------------------------------------------------------
    # RULE 4
    # Active overdue ticket
    #
    # IMPORTANT:
    # Only compare SLA time for active tickets.
    # We intentionally do NOT compare historical resolved
    # tickets with datetime.now().
    # ------------------------------------------------------

    active_statuses = {
        "OPEN",
        "IN_PROGRESS",
        "PENDING",
        "ASSIGNED"
    }

    if (
        status in active_statuses
        and sla
    ):

        due_at = sla.get(
            "due_at"
        )

        if due_at:

            try:

                due_time = datetime.strptime(
                    due_at,
                    "%Y-%m-%d %H:%M:%S"
                )

                if datetime.now() > due_time:

                    return True

            except Exception:

                pass

    # ------------------------------------------------------
    # Default
    # ------------------------------------------------------

    return False


# ==========================================================
# COMPLETE TICKET PROCESSING
# ==========================================================

def process_ticket(ticket):

    routing = route_ticket(
        ticket
    )

    sla = calculate_sla_details(
        ticket
    )

    escalation = check_escalation(
        ticket,
        routing,
        sla
    )

    return {

        "ticket_id": ticket.get(
            "ticket_id"
        ),

        "routing": routing,

        "sla": sla,

        "escalation": escalation,
    }


# ==========================================================
# TEST
# ==========================================================

def main():

    print()
    print("=" * 60)
    print(
        "ACADEMIC SUPPORT AI ROUTING ENGINE"
    )
    print("=" * 60)

    tickets = load_tickets()

    print()
    print(
        f"Loaded tickets: {len(tickets)}"
    )

    print()

    for ticket in tickets[:5]:

        routing = route_ticket(
            ticket
        )

        sla = calculate_sla_details(
            ticket
        )

        escalation = check_escalation(
            ticket,
            routing,
            sla
        )

        escalation_text = (
            "YES"
            if escalation
            else "NO"
        )

        print(
            f"{ticket['ticket_id']} | "
            f"{routing['domain']} | "
            f"{routing['assigned_team']} | "
            f"SLA: {sla['sla_hours']}h | "
            f"Status: {ticket['status']} | "
            f"Escalation: {escalation_text}"
        )

    print()
    print(
        "Routing engine test completed."
    )


if __name__ == "__main__":

    main()