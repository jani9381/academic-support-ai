"""
Academic Support AI - Synthetic Data Generator

Generates deterministic synthetic data for the academic support workflow.

Baseline:
    Tickets   : 5,000
    Articles  : 200
    Messages  : 20,000
    Seed      : 20261022
    Anomalies : 100

Usage:
    .\venv313\Scripts\python.exe generate_data.py

Custom scale:
    .\venv313\Scripts\python.exe generate_data.py \
        --tickets 5000 \
        --articles 200 \
        --messages 20000 \
        --seed 20261022 \
        --anomalies 100
"""

import argparse
import csv
import hashlib
import json
import os
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

DEFAULT_TICKETS = 5000
DEFAULT_ARTICLES = 200
DEFAULT_MESSAGES = 20000
DEFAULT_SEED = 20261022
DEFAULT_ANOMALIES = 100


# ============================================================
# MASTER DATA
# ============================================================

ROLES = [
    {
        "role_id": "ROLE-001",
        "role_name": "Learner",
    },
    {
        "role_id": "ROLE-002",
        "role_name": "Instructor",
    },
    {
        "role_id": "ROLE-003",
        "role_name": "Academic Administrator",
    },
    {
        "role_id": "ROLE-004",
        "role_name": "Support Staff",
    },
    {
        "role_id": "ROLE-005",
        "role_name": "Platform Administrator",
    },
]


CATEGORIES = [
    {
        "category_id": "CAT-001",
        "category_name": "FINANCIAL_AID",
        "owning_team": "Financial Aid Team",
    },
    {
        "category_id": "CAT-002",
        "category_name": "REGISTRATION",
        "owning_team": "Registrar Team",
    },
    {
        "category_id": "CAT-003",
        "category_name": "IT",
        "owning_team": "IT Support Team",
    },
    {
        "category_id": "CAT-004",
        "category_name": "ACCESSIBILITY",
        "owning_team": "Accessibility Team",
    },
]


TERMS = [
    {
        "term_id": "TERM-2025-FALL",
        "term_name": "Fall 2025",
        "start_date": "2025-08-01",
        "end_date": "2025-12-20",
    },
    {
        "term_id": "TERM-2026-SPRING",
        "term_name": "Spring 2026",
        "start_date": "2026-01-05",
        "end_date": "2026-05-15",
    },
    {
        "term_id": "TERM-2026-FALL",
        "term_name": "Fall 2026",
        "start_date": "2026-08-01",
        "end_date": "2026-12-20",
    },
]


POLICY_IDS = {
    "FINANCIAL_AID": "POL-FINANCIAL-AID-2026-001",
    "REGISTRATION": "POL-REGISTRATION-2026-001",
    "IT": "POL-IT-2026-001",
    "ACCESSIBILITY": "POL-ACCESSIBILITY-2026-001",
    "GENERAL": "POL-GENERAL-2026-001",
}


POLICY_CONTENT = {
    "FINANCIAL_AID": (
        "Students must submit financial aid applications before the "
        "published deadline. Late applications may require manual review."
    ),
    "REGISTRATION": (
        "Students must complete registration changes before the published "
        "registration deadline. Exceptions require approval from the "
        "appropriate academic administrator."
    ),
    "IT": (
        "Technology support requests should include the affected service, "
        "device information, and a description of the problem. Critical "
        "service outages must be escalated to IT support."
    ),
    "ACCESSIBILITY": (
        "Accessibility accommodation requests should be handled through "
        "the accessibility support process. Sensitive accommodation "
        "information should only be shared with authorized staff."
    ),
    "GENERAL": (
        "Academic support requests should be routed to the responsible "
        "support team and answered using current, approved institutional "
        "policy information."
    ),
}


DOMAIN_KEYWORDS = {
    "FINANCIAL_AID": [
        "financial aid",
        "scholarship",
        "grant",
        "fafsa",
        "funding",
        "aid application",
        "financial",
    ],
    "REGISTRATION": [
        "registration",
        "register",
        "course",
        "enrollment",
        "drop",
        "add",
        "withdraw",
    ],
    "IT": [
        "password",
        "login",
        "computer",
        "wifi",
        "network",
        "software",
        "portal",
        "technology",
        "system",
    ],
    "ACCESSIBILITY": [
        "accessibility",
        "accommodation",
        "disability",
        "screen reader",
        "assistive",
        "accessible",
    ],
}


TICKET_SUBJECTS = {
    "FINANCIAL_AID": [
        "Financial aid application deadline",
        "Scholarship application question",
        "Grant eligibility question",
        "Financial aid status",
        "Late financial aid submission",
    ],
    "REGISTRATION": [
        "Course registration issue",
        "Unable to register for course",
        "Registration deadline question",
        "Course withdrawal request",
        "Enrollment change question",
    ],
    "IT": [
        "Unable to log in",
        "Campus Wi-Fi not working",
        "Student portal issue",
        "Password reset request",
        "Software access problem",
    ],
    "ACCESSIBILITY": [
        "Accommodation request",
        "Accessibility support question",
        "Screen reader issue",
        "Accessible course material request",
        "Disability support request",
    ],
}


TICKET_DESCRIPTIONS = {
    "FINANCIAL_AID": [
        "I need help understanding the financial aid application deadline.",
        "Can you tell me when I need to submit my financial aid application?",
        "I have a question about my scholarship application.",
        "I submitted my aid application and need to know the next step.",
        "I may have missed the financial aid deadline and need assistance.",
    ],
    "REGISTRATION": [
        "I am unable to register for one of my courses.",
        "I need help with a registration change.",
        "Can I withdraw from this course before the deadline?",
        "I have a question about the registration deadline.",
        "The registration system is not allowing me to enroll.",
    ],
    "IT": [
        "I cannot log in to the student portal.",
        "The campus Wi-Fi is not working for me.",
        "I am unable to reset my password.",
        "The student portal is showing an error.",
        "I need access to a required software application.",
    ],
    "ACCESSIBILITY": [
        "I need help submitting an accommodation request.",
        "I need accessible course materials.",
        "My screen reader is not working with the course portal.",
        "I need information about accessibility support.",
        "I need assistance with an accommodation request.",
    ],
}


SENDER_TYPES = [
    "LEARNER",
    "INSTRUCTOR",
    "SUPPORT_STAFF",
    "ACADEMIC_ADMIN",
    "SYSTEM",
]


ROUTING_METHODS = [
    "RULE_BASED",
    "POLICY_BASED",
    "MANUAL",
]


EVENT_TYPES = [
    "CREATED",
    "ROUTED",
    "SLA_STARTED",
    "MESSAGE_RECEIVED",
    "ESCALATED",
    "RESOLVED",
    "CLOSED",
]


ISSUE_TYPES = [
    "NONE",
    "expired_policy_citation",
    "unauthorized_routing",
    "unsupported_fact",
    "business_hours_sla_bug",
    "missing_escalation",
]


SLA_HOURS = {
    "CRITICAL": 4,
    "HIGH": 8,
    "MEDIUM": 24,
    "LOW": 72,
}


PRIORITIES = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
]


STATUS_VALUES = [
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def ensure_directories():
    """
    Prepare output directories without deleting the existing data folder.

    This is intentionally NOT using shutil.rmtree(DATA_DIR).

    OneDrive/Windows can lock files inside the data directory and cause
    PermissionError. Existing CSV files are overwritten individually.
    """

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def write_csv(filename, rows, fieldnames):
    """
    Write records to data/<filename>.
    """

    path = DATA_DIR / filename

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)

    print(f"Created: {filename} -> {len(rows)} records")


def iso_datetime(value):
    """
    Convert datetime to consistent ISO format.
    """

    return value.strftime("%Y-%m-%dT%H:%M:%S")


def random_datetime(rng, start, end):
    """
    Generate deterministic random datetime between start and end.
    """

    total_seconds = int((end - start).total_seconds())

    if total_seconds <= 0:
        return start

    return start + timedelta(
        seconds=rng.randint(0, total_seconds)
    )


def random_choice(rng, values):
    return values[rng.randrange(len(values))]


def sha256_file(path):
    """
    Calculate SHA256 checksum for reproducibility.
    """

    h = hashlib.sha256()

    with open(path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def calculate_row_count(path):
    with open(path, "r", encoding="utf-8") as file:
        return max(sum(1 for _ in file) - 1, 0)


def safe_resolved_timestamp(created_at, proposed_resolved_at):
    """
    IMPORTANT DATABASE SAFETY RULE:

    resolved_at must never be earlier than created_at.

    This prevents the schema constraint:

        resolved_at IS NULL
        OR resolved_at >= created_at

    from failing.
    """

    if proposed_resolved_at is None:
        return None

    if proposed_resolved_at < created_at:
        return created_at

    return proposed_resolved_at


# ============================================================
# MASTER TABLE GENERATORS
# ============================================================

def build_roles():
    return [dict(row) for row in ROLES]


def build_categories():
    return [dict(row) for row in CATEGORIES]


def build_terms():
    return [dict(row) for row in TERMS]


def build_requesters(rng, count=100):
    rows = []

    first_names = [
        "Aarav",
        "Aisha",
        "Rahul",
        "Priya",
        "Arjun",
        "Ananya",
        "Rohan",
        "Sneha",
        "Kiran",
        "Meera",
        "Vikram",
        "Nisha",
        "Aditya",
        "Kavya",
        "Ravi",
        "Isha",
        "Sanjay",
        "Pooja",
        "Varun",
        "Neha",
    ]

    last_names = [
        "Sharma",
        "Reddy",
        "Kumar",
        "Patel",
        "Singh",
        "Verma",
        "Rao",
        "Das",
        "Gupta",
        "Khan",
    ]

    for i in range(1, count + 1):

        requester_id = f"REQ-{i:06d}"

        name = (
            f"{random_choice(rng, first_names)} "
            f"{random_choice(rng, last_names)}"
        )

        role = random_choice(
            rng,
            ROLES[:4],
        )

        email_name = (
            name.lower()
            .replace(" ", ".")
        )

        rows.append(
            {
                "requester_id": requester_id,
                "requester_name": name,
                "role_id": role["role_id"],
                "email": f"{email_name}{i}@example.edu",
            }
        )

    return rows


def build_policies():
    """
    Build policy documents.

    IMPORTANT:
    Policy IDs consistently use hyphens.

    Example:
        POL-FINANCIAL-AID-2026-001

    NOT:
        POL-FINANCIAL_AID-2026-001
    """

    policies = []

    policy_metadata = [
        (
            "FINANCIAL_AID",
            "Financial Aid Application Policy",
            "1.0",
        ),
        (
            "REGISTRATION",
            "Course Registration Policy",
            "1.0",
        ),
        (
            "IT",
            "IT Support Policy",
            "1.0",
        ),
        (
            "ACCESSIBILITY",
            "Accessibility Accommodation Policy",
            "1.0",
        ),
        (
            "GENERAL",
            "General Academic Support Policy",
            "1.0",
        ),
    ]

    for domain, title, version in policy_metadata:

        effective_from = "2026-01-01"
        effective_to = "2026-12-31"

        policies.append(
            {
                "policy_id": POLICY_IDS[domain],
                "policy_title": title,
                "domain": domain,
                "version": version,
                "effective_from": effective_from,
                "effective_to": effective_to,
                "policy_text": POLICY_CONTENT[domain],
                "source_url": (
                    f"https://example.edu/policies/"
                    f"{domain.lower()}"
                ),
            }
        )

    return policies


# ============================================================
# KNOWLEDGE ARTICLES
# ============================================================

def build_articles(rng, count):
    rows = []

    domains = [
        "FINANCIAL_AID",
        "REGISTRATION",
        "IT",
        "ACCESSIBILITY",
    ]

    for i in range(1, count + 1):

        domain = domains[(i - 1) % len(domains)]

        article_id = f"KB-{i:06d}"

        article_title = (
            f"{domain.replace('_', ' ').title()} "
            f"Knowledge Article {i:04d}"
        )

        keywords = DOMAIN_KEYWORDS[domain]

        keyword = random_choice(rng, keywords)

        content = (
            f"This knowledge article provides approved guidance "
            f"for {keyword}. "
            f"{POLICY_CONTENT[domain]} "
            f"Students and faculty should contact the appropriate "
            f"support team when the standard process does not resolve "
            f"the request."
        )

        rows.append(
            {
                "article_id": article_id,
                "policy_id": POLICY_IDS[domain],
                "title": article_title,
                "domain": domain,
                "content": content,
                "version": "1.0",
                "effective_from": "2026-01-01",
                "effective_to": "2026-12-31",
                "status": "PUBLISHED",
            }
        )

    return rows


# ============================================================
# TICKETS
# ============================================================

def build_tickets(
    rng,
    count,
    requester_rows,
    category_rows,
    term_rows,
):
    rows = []

    start = datetime(2026, 1, 5, 8, 0, 0)
    end = datetime(2026, 11, 1, 18, 0, 0)

    requester_ids = [
        row["requester_id"]
        for row in requester_rows
    ]

    category_map = {
        row["category_name"]: row["category_id"]
        for row in category_rows
    }

    term_ids = [
        row["term_id"]
        for row in term_rows
    ]

    for i in range(1, count + 1):

        ticket_id = f"TKT-2026-{i:06d}"

        domain = random_choice(
            rng,
            [
                "FINANCIAL_AID",
                "REGISTRATION",
                "IT",
                "ACCESSIBILITY",
            ],
        )

        priority = random_choice(
            rng,
            PRIORITIES,
        )

        status = random_choice(
            rng,
            STATUS_VALUES,
        )

        created_dt = random_datetime(
            rng,
            start,
            end,
        )

        # ----------------------------------------------------
        # IMPORTANT FIX
        # ----------------------------------------------------
        #
        # Generate resolution time from CREATED TIME.
        #
        # This guarantees:
        #
        #     resolved_at >= created_at
        #
        # ----------------------------------------------------

        resolved_dt = None

        if status in ["RESOLVED", "CLOSED"]:

            resolution_hours = rng.randint(1, 96)

            proposed_resolved_dt = (
                created_dt
                + timedelta(hours=resolution_hours)
            )

            # Final safety check.
            resolved_dt = safe_resolved_timestamp(
                created_dt,
                proposed_resolved_dt,
            )

        updated_dt = created_dt

        if resolved_dt is not None:

            updated_dt = resolved_dt

        else:

            update_hours = rng.randint(0, 48)

            proposed_updated_dt = (
                created_dt
                + timedelta(hours=update_hours)
            )

            if proposed_updated_dt < created_dt:
                proposed_updated_dt = created_dt

            updated_dt = proposed_updated_dt

        requester_id = random_choice(
            rng,
            requester_ids,
        )

        category_id = category_map[domain]

        term_id = random_choice(
            rng,
            term_ids,
        )

        subject = random_choice(
            rng,
            TICKET_SUBJECTS[domain],
        )

        description = random_choice(
            rng,
            TICKET_DESCRIPTIONS[domain],
        )

        rows.append(
            {
                "ticket_id": ticket_id,
                "requester_id": requester_id,
                "category_id": category_id,
                "term_id": term_id,
                "subject": subject,
                "description": description,
                "priority": priority,
                "status": status,
                "created_at": iso_datetime(created_dt),
                "updated_at": iso_datetime(updated_dt),
                "resolved_at": (
                    iso_datetime(resolved_dt)
                    if resolved_dt
                    else ""
                ),
            }
        )

    return rows


# ============================================================
# MESSAGES
# ============================================================

def build_messages(rng, count, ticket_rows):
    rows = []

    ticket_count = len(ticket_rows)

    message_templates = [
        "I need help with this request.",
        "Can you please provide an update?",
        "Thank you for the information.",
        "I have attached the required details.",
        "Could you clarify the applicable policy?",
        "I still need assistance with this issue.",
        "Is there a deadline I should be aware of?",
        "Please let me know what I should do next.",
        "Thank you for resolving my request.",
    ]

    for i in range(1, count + 1):

        ticket = ticket_rows[(i - 1) % ticket_count]

        ticket_id = ticket["ticket_id"]

        message_id = (
            f"MSG-{ticket_id}-{i:04d}"
        )

        sender_type = random_choice(
            rng,
            SENDER_TYPES,
        )

        created_at = ticket["created_at"]

        try:
            created_dt = datetime.fromisoformat(
                created_at
            )
        except ValueError:
            created_dt = datetime(2026, 1, 1)

        message_dt = (
            created_dt
            + timedelta(
                minutes=rng.randint(1, 4320)
            )
        )

        sender_id = ""

        if sender_type == "LEARNER":
            sender_id = ticket["requester_id"]

        elif sender_type == "INSTRUCTOR":
            sender_id = "ROLE-002"

        elif sender_type == "SUPPORT_STAFF":
            sender_id = "ROLE-004"

        elif sender_type == "ACADEMIC_ADMIN":
            sender_id = "ROLE-003"

        elif sender_type == "SYSTEM":
            sender_id = "SYSTEM"

        rows.append(
            {
                "message_id": message_id,
                "ticket_id": ticket_id,
                "sender_type": sender_type,
                "sender_id": sender_id,
                "message_text": random_choice(
                    rng,
                    message_templates,
                ),
                "created_at": iso_datetime(
                    message_dt
                ),
            }
        )

    return rows


# ============================================================
# ASSIGNMENTS
# ============================================================

def build_assignments(
    rng,
    ticket_rows,
    category_rows,
):
    rows = []

    category_team = {
        row["category_name"]: row["owning_team"]
        for row in category_rows
    }

    category_name_by_id = {
        row["category_id"]: row["category_name"]
        for row in category_rows
    }

    for i, ticket in enumerate(ticket_rows, start=1):

        ticket_id = ticket["ticket_id"]

        category_name = category_name_by_id[
            ticket["category_id"]
        ]

        assigned_team = category_team[
            category_name
        ]

        assignment_id = (
            f"ASN-{i:06d}"
        )

        routing_method = random_choice(
            rng,
            ROUTING_METHODS,
        )

        # Normal data is policy/rule routed.
        # Manual routing is still a valid operational state.
        if i % 10 != 0:
            routing_method = (
                "POLICY_BASED"
                if i % 2 == 0
                else "RULE_BASED"
            )

        rows.append(
            {
                "assignment_id": assignment_id,
                "ticket_id": ticket_id,
                "assigned_team": assigned_team,
                "assigned_by": "SYSTEM",
                "assigned_at": ticket["created_at"],
                "routing_method": routing_method,
            }
        )

    return rows


# ============================================================
# ASSIGNMENT SOURCES
# ============================================================

def build_assignment_sources(
    ticket_rows,
    assignment_rows,
):
    rows = []

    for ticket, assignment in zip(
        ticket_rows,
        assignment_rows,
    ):

        rows.append(
            {
                "assignment_source_id": (
                    f"ASRC-{assignment['assignment_id']}"
                ),
                "ticket_id": ticket["ticket_id"],
                "assignment_id": assignment[
                    "assignment_id"
                ],
                "source_type": "POLICY_RULE",
                "source_reference": (
                    POLICY_IDS[
                        category_to_domain(
                            ticket["category_id"]
                        )
                    ]
                ),
            }
        )

    return rows


def category_to_domain(category_id):
    mapping = {
        "CAT-001": "FINANCIAL_AID",
        "CAT-002": "REGISTRATION",
        "CAT-003": "IT",
        "CAT-004": "ACCESSIBILITY",
    }

    return mapping.get(
        category_id,
        "GENERAL",
    )


# ============================================================
# SLA
# ============================================================

def build_sla(
    rng,
    ticket_rows,
):
    rows = []

    for i, ticket in enumerate(
        ticket_rows,
        start=1,
    ):

        priority = ticket["priority"]

        sla_hours = SLA_HOURS[
            priority
        ]

        started_at = ticket["created_at"]

        started_dt = datetime.fromisoformat(
            started_at
        )

        due_dt = (
            started_dt
            + timedelta(
                hours=sla_hours
            )
        )

        breached = False

        breached_at = ""

        # Create deterministic SLA states.
        if ticket["status"] in [
            "RESOLVED",
            "CLOSED",
        ]:

            resolved_dt = None

            if ticket["resolved_at"]:
                resolved_dt = datetime.fromisoformat(
                    ticket["resolved_at"]
                )

            if resolved_dt is not None:

                if resolved_dt > due_dt:

                    breached = True
                    breached_at = iso_datetime(
                        due_dt
                    )

        escalation_required = (
            priority in [
                "CRITICAL",
                "HIGH",
            ]
        )

        rows.append(
            {
                "sla_id": f"SLA-{ticket['ticket_id']}",
                "ticket_id": ticket["ticket_id"],
                "priority": priority,
                "sla_hours": sla_hours,
                "started_at": started_at,
                "due_at": iso_datetime(
                    due_dt
                ),
                "breached": (
                    "1"
                    if breached
                    else "0"
                ),
                "breached_at": breached_at,
                "escalation_required": (
                    "1"
                    if escalation_required
                    else "0"
                ),
            }
        )

    return rows


# ============================================================
# EVENT HISTORY
# ============================================================

def build_event_history(
    rng,
    ticket_rows,
):
    rows = []

    event_id = 1

    for ticket in ticket_rows:

        ticket_id = ticket["ticket_id"]

        created_at = datetime.fromisoformat(
            ticket["created_at"]
        )

        # CREATED
        rows.append(
            {
                "event_id": f"EVT-{event_id:08d}",
                "ticket_id": ticket_id,
                "event_type": "CREATED",
                "old_status": "",
                "new_status": "OPEN",
                "event_timestamp": iso_datetime(
                    created_at
                ),
                "actor_type": "SYSTEM",
                "actor_id": "SYSTEM",
                "event_reason": "Ticket created",
            }
        )

        event_id += 1

        # ROUTED
        routed_time = created_at + timedelta(
            minutes=5
        )

        rows.append(
            {
                "event_id": f"EVT-{event_id:08d}",
                "ticket_id": ticket_id,
                "event_type": "ROUTED",
                "old_status": "OPEN",
                "new_status": "OPEN",
                "event_timestamp": iso_datetime(
                    routed_time
                ),
                "actor_type": "SYSTEM",
                "actor_id": "SYSTEM",
                "event_reason": "Ticket routed",
            }
        )

        event_id += 1

        # SLA
        sla_time = created_at + timedelta(
            minutes=6
        )

        rows.append(
            {
                "event_id": f"EVT-{event_id:08d}",
                "ticket_id": ticket_id,
                "event_type": "SLA_STARTED",
                "old_status": "OPEN",
                "new_status": "OPEN",
                "event_timestamp": iso_datetime(
                    sla_time
                ),
                "actor_type": "SYSTEM",
                "actor_id": "SYSTEM",
                "event_reason": "SLA clock started",
            }
        )

        event_id += 1

        # RESOLVED
        if ticket["resolved_at"]:

            resolved_dt = datetime.fromisoformat(
                ticket["resolved_at"]
            )

            rows.append(
                {
                    "event_id": f"EVT-{event_id:08d}",
                    "ticket_id": ticket_id,
                    "event_type": "RESOLVED",
                    "old_status": (
                        "IN_PROGRESS"
                    ),
                    "new_status": (
                        "RESOLVED"
                    ),
                    "event_timestamp": iso_datetime(
                        resolved_dt
                    ),
                    "actor_type": "SUPPORT_STAFF",
                    "actor_id": "ROLE-004",
                    "event_reason": (
                        "Ticket resolved"
                    ),
                }
            )

            event_id += 1

        # CLOSED
        if ticket["status"] == "CLOSED":

            closed_dt = (
                datetime.fromisoformat(
                    ticket["updated_at"]
                )
            )

            if ticket["resolved_at"]:

                resolved_dt = (
                    datetime.fromisoformat(
                        ticket["resolved_at"]
                    )
                )

                if closed_dt < resolved_dt:
                    closed_dt = resolved_dt

            rows.append(
                {
                    "event_id": f"EVT-{event_id:08d}",
                    "ticket_id": ticket_id,
                    "event_type": "CLOSED",
                    "old_status": (
                        "RESOLVED"
                    ),
                    "new_status": (
                        "CLOSED"
                    ),
                    "event_timestamp": iso_datetime(
                        closed_dt
                    ),
                    "actor_type": "SYSTEM",
                    "actor_id": "SYSTEM",
                    "event_reason": (
                        "Ticket closed"
                    ),
                }
            )

            event_id += 1

    return rows


# ============================================================
# RESOLUTION FEEDBACK
# ============================================================

def build_resolution_feedback(
    rng,
    ticket_rows,
):
    rows = []

    feedback_text = {
        1: "The issue was not resolved.",
        2: "The response was not very helpful.",
        3: "The issue was partially resolved.",
        4: "The support response was helpful.",
        5: "The issue was resolved quickly and clearly.",
    }

    for i, ticket in enumerate(
        ticket_rows,
        start=1,
    ):

        rating = rng.randint(1, 5)

        rows.append(
            {
                "feedback_id": f"FDB-{i:06d}",
                "ticket_id": ticket["ticket_id"],
                "rating": rating,
                "feedback_text": feedback_text[
                    rating
                ],
                "resolution_status": (
                    "RESOLVED"
                    if ticket["status"]
                    in [
                        "RESOLVED",
                        "CLOSED",
                    ]
                    else "PENDING"
                ),
                "submitted_at": (
                    ticket["updated_at"]
                ),
            }
        )

    return rows


# ============================================================
# GROUND TRUTH
# ============================================================

def build_ground_truth(
    ticket_rows,
    assignment_rows,
    sla_rows,
    anomaly_count,
    seed,
):
    """
    Ground truth is intentionally kept separate from the
    operational input tables.

    This prevents evaluation labels from leaking directly
    into model input features.
    """

    rows = []

    # Exactly 5 anomaly types.
    anomaly_types = [
        "expired_policy_citation",
        "unauthorized_routing",
        "unsupported_fact",
        "business_hours_sla_bug",
        "missing_escalation",
    ]

    total_tickets = len(ticket_rows)

    # Make sure anomaly_count does not exceed ticket count.
    anomaly_count = min(
        anomaly_count,
        total_tickets,
    )

    anomaly_per_type = (
        anomaly_count // len(anomaly_types)
    )

    remainder = (
        anomaly_count
        % len(anomaly_types)
    )

    anomaly_assignments = {}

    position = 0

    for index, issue_type in enumerate(
        anomaly_types
    ):

        count = anomaly_per_type

        if index < remainder:
            count += 1

        for _ in range(count):

            if position < total_tickets:

                ticket_id = ticket_rows[
                    position
                ]["ticket_id"]

                anomaly_assignments[
                    ticket_id
                ] = issue_type

                position += 1

    for ticket, assignment, sla in zip(
        ticket_rows,
        assignment_rows,
        sla_rows,
    ):

        ticket_id = ticket["ticket_id"]

        domain = category_to_domain(
            ticket["category_id"]
        )

        expected_team = {
            "FINANCIAL_AID":
                "Financial Aid Team",

            "REGISTRATION":
                "Registrar Team",

            "IT":
                "IT Support Team",

            "ACCESSIBILITY":
                "Accessibility Team",
        }[domain]

        expected_sla = SLA_HOURS[
            ticket["priority"]
        ]

        expected_escalation = (
            ticket["priority"]
            in [
                "CRITICAL",
                "HIGH",
            ]
        )

        issue_type = anomaly_assignments.get(
            ticket_id,
            "NONE",
        )

        expected_policy_id = POLICY_IDS[
            domain
        ]

        expected_source_valid = (
            "1"
        )

        expected_anomaly = (
            "1"
            if issue_type != "NONE"
            else "0"
        )

        rows.append(
            {
                "ground_truth_id": (
                    f"GT-{ticket_id}"
                ),
                "ticket_id": ticket_id,
                "expected_team": expected_team,
                "expected_sla_hours": (
                    expected_sla
                ),
                "expected_escalation": (
                    "1"
                    if expected_escalation
                    else "0"
                ),
                "issue_type": issue_type,
                "expected_policy_id": (
                    expected_policy_id
                ),
                "expected_source_valid": (
                    expected_source_valid
                ),
                "expected_anomaly": (
                    expected_anomaly
                ),
            }
        )

    return rows


# ============================================================
# SOURCE MANIFEST
# ============================================================

def build_source_manifest():
    """
    Since this project uses synthetic data, no external source
    data is required.

    The manifest documents that fact explicitly.
    """

    return [
        {
            "source_id": "SRC-001",
            "source_name": "Synthetic Academic Support Dataset",
            "source_type": "SYNTHETIC",
            "source_url": "",
            "version": "1.0",
            "retrieval_date": (
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
            ),
            "license": "Synthetic/Internal",
            "attribution": "Generated for assessment",
            "transformation_notes": (
                "Generated deterministically using "
                "seed 20261022. No external personal "
                "or institutional data used."
            ),
        }
    ]


# ============================================================
# GENERATION SUMMARY
# ============================================================

def build_generation_summary(
    seed,
    ticket_count,
    article_count,
    message_count,
    anomaly_count,
):
    summary = {
        "project": "Academic Support AI",
        "seed": seed,
        "tickets_requested": ticket_count,
        "articles_requested": article_count,
        "messages_requested": message_count,
        "anomalies_requested": anomaly_count,
        "generated_at": datetime.now().isoformat(),
        "data_directory": str(DATA_DIR),
        "deterministic_generation": True,
        "external_data_used": False,
    }

    return summary


# ============================================================
# MAIN
# ============================================================

def generate_data(
    tickets=DEFAULT_TICKETS,
    articles=DEFAULT_ARTICLES,
    messages=DEFAULT_MESSAGES,
    seed=DEFAULT_SEED,
    anomalies=DEFAULT_ANOMALIES,
):

    print()
    print("=" * 65)
    print("ACADEMIC SUPPORT AI - DATA GENERATION")
    print("=" * 65)

    print(f"Seed: {seed}")
    print(f"Tickets requested: {tickets}")
    print(f"Articles requested: {articles}")
    print(f"Messages requested: {messages}")
    print(f"Anomalies requested: {anomalies}")
    print()

    rng = random.Random(seed)

    ensure_directories()

    # --------------------------------------------------------
    # 1. MASTER DATA
    # --------------------------------------------------------

    roles = build_roles()

    write_csv(
        "role.csv",
        roles,
        [
            "role_id",
            "role_name",
        ],
    )

    requesters = build_requesters(
        rng,
        100,
    )

    write_csv(
        "requester.csv",
        requesters,
        [
            "requester_id",
            "requester_name",
            "role_id",
            "email",
        ],
    )

    categories = build_categories()

    write_csv(
        "category.csv",
        categories,
        [
            "category_id",
            "category_name",
            "owning_team",
        ],
    )

    terms = build_terms()

    write_csv(
        "term.csv",
        terms,
        [
            "term_id",
            "term_name",
            "start_date",
            "end_date",
        ],
    )

    policies = build_policies()

    write_csv(
        "policy_document.csv",
        policies,
        [
            "policy_id",
            "policy_title",
            "domain",
            "version",
            "effective_from",
            "effective_to",
            "policy_text",
            "source_url",
        ],
    )

    # --------------------------------------------------------
    # 2. KNOWLEDGE ARTICLES
    # --------------------------------------------------------

    knowledge_articles = build_articles(
        rng,
        articles,
    )

    write_csv(
        "knowledge_article.csv",
        knowledge_articles,
        [
            "article_id",
            "policy_id",
            "title",
            "domain",
            "content",
            "version",
            "effective_from",
            "effective_to",
            "status",
        ],
    )

    # --------------------------------------------------------
    # 3. TICKETS
    # --------------------------------------------------------

    tickets_rows = build_tickets(
        rng,
        tickets,
        requesters,
        categories,
        terms,
    )

    write_csv(
        "ticket.csv",
        tickets_rows,
        [
            "ticket_id",
            "requester_id",
            "category_id",
            "term_id",
            "subject",
            "description",
            "priority",
            "status",
            "created_at",
            "updated_at",
            "resolved_at",
        ],
    )

    # --------------------------------------------------------
    # 4. MESSAGES
    # --------------------------------------------------------

    messages_rows = build_messages(
        rng,
        messages,
        tickets_rows,
    )

    write_csv(
        "message.csv",
        messages_rows,
        [
            "message_id",
            "ticket_id",
            "sender_type",
            "sender_id",
            "message_text",
            "created_at",
        ],
    )

    # --------------------------------------------------------
    # 5. ASSIGNMENTS
    # --------------------------------------------------------

    assignments = build_assignments(
        rng,
        tickets_rows,
        categories,
    )

    write_csv(
        "assignment.csv",
        assignments,
        [
            "assignment_id",
            "ticket_id",
            "assigned_team",
            "assigned_by",
            "assigned_at",
            "routing_method",
        ],
    )

    # --------------------------------------------------------
    # 6. ASSIGNMENT SOURCES
    # --------------------------------------------------------

    assignment_sources = (
        build_assignment_sources(
            tickets_rows,
            assignments,
        )
    )

    write_csv(
        "assignment_source.csv",
        assignment_sources,
        [
            "assignment_source_id",
            "ticket_id",
            "assignment_id",
            "source_type",
            "source_reference",
        ],
    )

    # --------------------------------------------------------
    # 7. SLA
    # --------------------------------------------------------

    sla_rows = build_sla(
        rng,
        tickets_rows,
    )

    write_csv(
        "sla.csv",
        sla_rows,
        [
            "sla_id",
            "ticket_id",
            "priority",
            "sla_hours",
            "started_at",
            "due_at",
            "breached",
            "breached_at",
            "escalation_required",
        ],
    )

    # --------------------------------------------------------
    # 8. EVENT HISTORY
    # --------------------------------------------------------

    event_rows = build_event_history(
        rng,
        tickets_rows,
    )

    write_csv(
        "event_history.csv",
        event_rows,
        [
            "event_id",
            "ticket_id",
            "event_type",
            "old_status",
            "new_status",
            "event_timestamp",
            "actor_type",
            "actor_id",
            "event_reason",
        ],
    )

    # --------------------------------------------------------
    # 9. RESOLUTION FEEDBACK
    # --------------------------------------------------------

    feedback_rows = (
        build_resolution_feedback(
            rng,
            tickets_rows,
        )
    )

    write_csv(
        "resolution_feedback.csv",
        feedback_rows,
        [
            "feedback_id",
            "ticket_id",
            "rating",
            "feedback_text",
            "resolution_status",
            "submitted_at",
        ],
    )

    # --------------------------------------------------------
    # 10. GROUND TRUTH
    # --------------------------------------------------------

    ground_truth_rows = build_ground_truth(
        tickets_rows,
        assignments,
        sla_rows,
        anomalies,
        seed,
    )

    write_csv(
        "ground_truth.csv",
        ground_truth_rows,
        [
            "ground_truth_id",
            "ticket_id",
            "expected_team",
            "expected_sla_hours",
            "expected_escalation",
            "issue_type",
            "expected_policy_id",
            "expected_source_valid",
            "expected_anomaly",
        ],
    )

    # --------------------------------------------------------
    # 11. SOURCE MANIFEST
    # --------------------------------------------------------

    source_manifest = (
        build_source_manifest()
    )

    write_csv(
        "source_manifest.csv",
        source_manifest,
        [
            "source_id",
            "source_name",
            "source_type",
            "source_url",
            "version",
            "retrieval_date",
            "license",
            "attribution",
            "transformation_notes",
        ],
    )

    # --------------------------------------------------------
    # 12. GENERATION SUMMARY
    # --------------------------------------------------------

    summary = build_generation_summary(
        seed,
        tickets,
        articles,
        messages,
        anomalies,
    )

    summary_path = (
        OUTPUT_DIR
        / "generation_summary.json"
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
        )

    # --------------------------------------------------------
    # 13. CHECKSUM MANIFEST
    # --------------------------------------------------------

    checksum_rows = []

    csv_files = sorted(
        DATA_DIR.glob("*.csv")
    )

    for csv_file in csv_files:

        checksum_rows.append(
            {
                "file_name": (
                    csv_file.name
                ),
                "row_count": (
                    calculate_row_count(
                        csv_file
                    )
                ),
                "sha256": (
                    sha256_file(
                        csv_file
                    )
                ),
            }
        )

    checksum_path = (
        OUTPUT_DIR
        / "data_checksums.json"
    )

    with open(
        checksum_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            checksum_rows,
            file,
            indent=2,
        )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print()
    print("=" * 65)
    print("DATA GENERATION COMPLETED")
    print("=" * 65)

    print(
        f"Data directory: {DATA_DIR}"
    )

    print(
        f"Summary: {summary_path}"
    )

    print(
        f"Checksums: {checksum_path}"
    )

    print()

    return 0


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic "
            "Academic Support AI data."
        )
    )

    parser.add_argument(
        "--tickets",
        type=int,
        default=DEFAULT_TICKETS,
        help="Number of tickets to generate.",
    )

    parser.add_argument(
        "--articles",
        type=int,
        default=DEFAULT_ARTICLES,
        help="Number of knowledge articles.",
    )

    parser.add_argument(
        "--messages",
        type=int,
        default=DEFAULT_MESSAGES,
        help="Number of messages.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed.",
    )

    parser.add_argument(
        "--anomalies",
        type=int,
        default=DEFAULT_ANOMALIES,
        help="Number of labeled anomaly records.",
    )

    args = parser.parse_args()

    if args.tickets <= 0:
        parser.error(
            "--tickets must be greater than 0"
        )

    if args.articles <= 0:
        parser.error(
            "--articles must be greater than 0"
        )

    if args.messages <= 0:
        parser.error(
            "--messages must be greater than 0"
        )

    if args.anomalies < 0:
        parser.error(
            "--anomalies cannot be negative"
        )

    return generate_data(
        tickets=args.tickets,
        articles=args.articles,
        messages=args.messages,
        seed=args.seed,
        anomalies=args.anomalies,
    )


if __name__ == "__main__":
    raise SystemExit(main())