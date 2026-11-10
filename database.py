import csv
import os
import sqlite3
from datetime import datetime, timedelta


# ============================================================
# PATHS
# ============================================================

ROOT = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(ROOT, "data")
OUTPUT_DIR = os.path.join(ROOT, "outputs")

DB_PATH = os.path.join(
    OUTPUT_DIR,
    "academic_support.db"
)

SCHEMA_PATH = os.path.join(
    ROOT,
    "schema.sql"
)


# ============================================================
# TABLE LOAD ORDER
# ============================================================

TABLE_FILES = [
    ("role", "role.csv"),
    ("requester", "requester.csv"),
    ("category", "category.csv"),
    ("term", "term.csv"),
    ("policy_document", "policy_document.csv"),
    ("knowledge_article", "knowledge_article.csv"),
    ("ticket", "ticket.csv"),
    ("message", "message.csv"),
    ("assignment", "assignment.csv"),
    ("assignment_source", "assignment_source.csv"),
    ("sla", "sla.csv"),
    ("event_history", "event_history.csv"),
    ("resolution_feedback", "resolution_feedback.csv"),
    ("ground_truth", "ground_truth.csv"),
    ("source_manifest", "source_manifest.csv"),
]


# ============================================================
# DEFAULT BUSINESS RULES
# ============================================================

DEFAULT_SLA_HOURS = {
    "CRITICAL": 4,
    "HIGH": 8,
    "MEDIUM": 24,
    "LOW": 72,
}


ALLOWED_PRIORITIES = {
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
}


ALLOWED_SENDER_TYPES = {
    "REQUESTER",
    "AGENT",
    "SYSTEM",
}


ALLOWED_ACTOR_TYPES = {
    "REQUESTER",
    "AGENT",
    "SYSTEM",
}


ALLOWED_ROUTING_METHODS = {
    "RULE_BASED",
    "MANUAL",
    "ESCALATION",
}


ALLOWED_SOURCE_TYPES = {
    "POLICY",
    "KNOWLEDGE_ARTICLE",
    "ROUTING_RULE",
    "SYSTEM_RULE",
}


# These are the event types used by the academic-support workflow.
# Unknown generator event names are safely mapped below.
ALLOWED_EVENT_TYPES = {
    "CREATED",
    "ROUTED",
    "STATUS_CHANGE",
    "RESOLUTION",
    "ESCALATION",
    "MESSAGE_RECEIVED",
    "MESSAGE_SENT",
    "SLA_BREACH",
}


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_value(value):
    """
    Convert empty CSV values into None.
    Preserve useful non-empty values.
    """

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def parse_datetime(value):
    """
    Convert timestamp text into datetime.

    Supports:
    - 2026-01-01T09:00:00
    - 2026-01-01 09:00:00
    - timestamps ending in Z
    """

    value = clean_value(value)

    if not value:
        return None

    text = value.replace("Z", "")

    try:
        return datetime.fromisoformat(text)
    except ValueError:

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                pass

    return None


def iso(value):
    """
    Convert datetime into SQLite-friendly ISO text.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def safe_datetime(
    value,
    fallback="2026-01-01T09:00:00"
):
    """
    Always return a valid timestamp string.
    """

    parsed = parse_datetime(value)

    if parsed:
        return parsed.isoformat()

    return fallback


def safe_int(value, default=None):
    """
    Safely convert a value to integer.
    """

    value = clean_value(value)

    if value is None:
        return default

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def read_csv(filename):
    """
    Read a CSV file from data/.
    """

    path = os.path.join(
        DATA_DIR,
        filename
    )

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"CSV file not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        return list(reader)


# ============================================================
# TRANSFORM: TICKET
# ============================================================

def transform_ticket(row):

    created_at = safe_datetime(
        row.get("created_at")
    )

    status = clean_value(
        row.get("status")
    )

    if not status:
        status = "OPEN"

    description = clean_value(
        row.get("description")
        or row.get("request_text")
    )

    if not description:
        description = "Academic support request"

    subject = clean_value(
        row.get("subject")
    )

    if not subject:
        subject = description[:100]

    priority = clean_value(
        row.get("priority")
    )

    if priority:
        priority = priority.upper()

    if priority not in ALLOWED_PRIORITIES:
        priority = "MEDIUM"

    # --------------------------------------------------------
    # Resolution timestamps
    # --------------------------------------------------------

    resolved_at = None

    if status in {
        "RESOLVED",
        "CLOSED"
    }:

        created_dt = parse_datetime(
            created_at
        )

        if created_dt:

            resolved_at = iso(
                created_dt + timedelta(hours=2)
            )

    # --------------------------------------------------------
    # Updated timestamp
    # --------------------------------------------------------

    created_dt = parse_datetime(
        created_at
    )

    if created_dt:

        if status in {
            "RESOLVED",
            "CLOSED"
        }:

            updated_at = iso(
                created_dt + timedelta(hours=2)
            )

        elif status in {
            "IN_PROGRESS",
            "WAITING",
            "ESCALATED"
        }:

            updated_at = iso(
                created_dt + timedelta(minutes=30)
            )

        else:

            updated_at = created_at

    else:

        updated_at = created_at

    return {
        "ticket_id": clean_value(
            row.get("ticket_id")
        ),

        "requester_id": clean_value(
            row.get("requester_id")
        ),

        "category_id": clean_value(
            row.get("category_id")
        ),

        "term_id": clean_value(
            row.get("term_id")
        ),

        "subject": subject,

        "description": description,

        "priority": priority,

        "status": status,

        "created_at": created_at,

        "updated_at": updated_at,

        "resolved_at": resolved_at,
    }


# ============================================================
# TRANSFORM: MESSAGE
# ============================================================

def transform_message(row):

    raw_sender_type = clean_value(
        row.get("sender_type")
    )

    if raw_sender_type:
        raw_sender_type = raw_sender_type.upper()

    sender_mapping = {
        "REQUESTER": "REQUESTER",
        "STUDENT": "REQUESTER",
        "LEARNER": "REQUESTER",

        "SUPPORT_AGENT": "AGENT",
        "AGENT": "AGENT",
        "STAFF": "AGENT",

        "SYSTEM": "SYSTEM",
    }

    sender_type = sender_mapping.get(
        raw_sender_type,
        "SYSTEM"
    )

    # Deterministic sender IDs
    if sender_type == "REQUESTER":

        sender_id = clean_value(
            row.get("sender_id")
        )

        if not sender_id:
            sender_id = "REQ-000001"

    elif sender_type == "AGENT":

        sender_id = clean_value(
            row.get("sender_id")
        )

        if not sender_id:
            sender_id = "AGENT-001"

    else:

        sender_id = "SYSTEM-001"

    created_at = safe_datetime(
        row.get("created_at")
        or row.get("sent_at")
    )

    message_text = clean_value(
        row.get("message_text")
        or row.get("message")
    )

    if not message_text:
        message_text = "Support workflow event."

    return {
        "message_id": clean_value(
            row.get("message_id")
        ),

        "ticket_id": clean_value(
            row.get("ticket_id")
        ),

        "sender_type": sender_type,

        "sender_id": sender_id,

        "message_text": message_text,

        "created_at": created_at,
    }


# ============================================================
# TRANSFORM: ASSIGNMENT
# ============================================================

def transform_assignment(row):

    assignment_status = clean_value(
        row.get("assignment_status")
    )

    if assignment_status:
        assignment_status = assignment_status.upper()

    assigned_team = clean_value(
        row.get("assigned_team")
    )

    if not assigned_team:
        assigned_team = "Academic Support Team"

    assigned_at = safe_datetime(
        row.get("assigned_at")
        or row.get("created_at")
    )

    if assignment_status == "MANUAL":
        routing_method = "MANUAL"

    elif assignment_status == "ESCALATED":
        routing_method = "ESCALATION"

    else:
        routing_method = "RULE_BASED"

    return {
        "assignment_id": clean_value(
            row.get("assignment_id")
        ),

        "ticket_id": clean_value(
            row.get("ticket_id")
        ),

        "assigned_team": assigned_team,

        "assigned_by": (
            clean_value(row.get("assigned_by"))
            or "routing_engine"
        ),

        "assigned_at": assigned_at,

        "routing_method": routing_method,
    }


# ============================================================
# TRANSFORM: ASSIGNMENT SOURCE
# ============================================================

def transform_assignment_source(row):

    source_id = clean_value(
        row.get("source_id")
    )

    ticket_id = clean_value(
        row.get("ticket_id")
    )

    # --------------------------------------------------------
    # Source primary key
    # --------------------------------------------------------

    assignment_source_id = safe_int(
        source_id.replace("SRC-", "")
        if source_id
        else None
    )

    # --------------------------------------------------------
    # Assignment ID
    # --------------------------------------------------------

    assignment_id = clean_value(
        row.get("assignment_id")
    )

    if not assignment_id and ticket_id:

        ticket_number = (
            ticket_id.split("-")[-1]
        )

        assignment_id = (
            f"ASN-{ticket_number}"
        )

    # --------------------------------------------------------
    # Source reference
    # --------------------------------------------------------

    policy_id = clean_value(
        row.get("policy_id")
    )

    article_id = clean_value(
        row.get("article_id")
    )

    source_reference = clean_value(
        row.get("source_reference")
    )

    if not source_reference:

        if policy_id:

            source_reference = policy_id

        elif article_id:

            source_reference = article_id

        elif ticket_id:

            source_reference = (
                f"TICKET:{ticket_id}"
            )

        else:

            source_reference = (
                "SYSTEM_RULE:DEFAULT"
            )

    # --------------------------------------------------------
    # Source type
    # --------------------------------------------------------

    raw_source_type = clean_value(
        row.get("source_type")
    )

    if raw_source_type:
        raw_source_type = (
            raw_source_type.upper()
        )

    mapping = {
        "POLICY": "POLICY",
        "POLICY_DOCUMENT": "POLICY",

        "ARTICLE": "KNOWLEDGE_ARTICLE",
        "KNOWLEDGE": "KNOWLEDGE_ARTICLE",
        "KNOWLEDGE_ARTICLE":
            "KNOWLEDGE_ARTICLE",

        "ROUTING":
            "ROUTING_RULE",

        "ROUTING_RULE":
            "ROUTING_RULE",

        "SYSTEM":
            "SYSTEM_RULE",

        "SYSTEM_RULE":
            "SYSTEM_RULE",

        "RULE":
            "SYSTEM_RULE",
    }

    source_type = mapping.get(
        raw_source_type,
        "POLICY"
    )

    return {
        "assignment_source_id":
            assignment_source_id,

        "ticket_id":
            ticket_id,

        "assignment_id":
            assignment_id,

        "source_type":
            source_type,

        "source_reference":
            source_reference,
    }


# ============================================================
# TRANSFORM: SLA
# ============================================================

def transform_sla(row):

    ticket_id = clean_value(
        row.get("ticket_id")
    )

    sla_id = clean_value(
        row.get("sla_id")
    )

    priority = clean_value(
        row.get("priority")
    )

    if priority:
        priority = priority.upper()

    if priority not in ALLOWED_PRIORITIES:
        priority = "MEDIUM"

    # --------------------------------------------------------
    # SLA HOURS
    # --------------------------------------------------------

    sla_hours = safe_int(
        row.get("sla_hours")
    )

    if sla_hours is None or sla_hours <= 0:

        sla_hours = DEFAULT_SLA_HOURS[
            priority
        ]

    # --------------------------------------------------------
    # START TIME
    # --------------------------------------------------------

    started_at = safe_datetime(
        row.get("started_at")
        or row.get("created_at")
    )

    # --------------------------------------------------------
    # DUE TIME
    # --------------------------------------------------------

    due_at = clean_value(
        row.get("due_at")
    )

    if not due_at:

        started_dt = parse_datetime(
            started_at
        )

        if started_dt:

            due_at = iso(
                started_dt +
                timedelta(hours=sla_hours)
            )

        else:

            due_at = started_at

    else:

        due_at = safe_datetime(
            due_at
        )

    # --------------------------------------------------------
    # BREACHED
    # --------------------------------------------------------

    raw_breached = clean_value(
        row.get("breached")
    )

    if raw_breached:

        breached = (
            1
            if raw_breached.lower()
            in {
                "1",
                "true",
                "yes",
                "y"
            }
            else 0
        )

    else:

        breached = 0

    # --------------------------------------------------------
    # BREACHED AT
    # --------------------------------------------------------

    breached_at = clean_value(
        row.get("breached_at")
    )

    if breached == 0:
        breached_at = None

    elif not breached_at:

        breached_at = due_at

    else:

        breached_at = safe_datetime(
            breached_at
        )

    # --------------------------------------------------------
    # ESCALATION
    # --------------------------------------------------------

    raw_escalation = clean_value(
        row.get("escalation_required")
    )

    if raw_escalation:

        escalation_required = (
            1
            if raw_escalation.lower()
            in {
                "1",
                "true",
                "yes",
                "y"
            }
            else 0
        )

    else:

        escalation_required = (
            1
            if priority == "CRITICAL"
            else 0
        )

    return {
        "sla_id": sla_id,

        "ticket_id": ticket_id,

        "priority": priority,

        "sla_hours": sla_hours,

        "started_at": started_at,

        "due_at": due_at,

        "breached": breached,

        "breached_at": breached_at,

        "escalation_required":
            escalation_required,
    }


# ============================================================
# TRANSFORM: EVENT HISTORY
# ============================================================

# ============================================================
# TRANSFORM: EVENT HISTORY
# ============================================================

def transform_event(row):
    """
    Transform event_history.csv into the database schema.

    Generator/source event names are normalized into the exact
    event_type values required by schema.sql.
    """

    # --------------------------------------------------------
    # EVENT ID
    # --------------------------------------------------------

    event_id = clean_value(
        row.get("event_id")
    )

    # --------------------------------------------------------
    # TICKET ID
    # --------------------------------------------------------

    ticket_id = clean_value(
        row.get("ticket_id")
    )

    # --------------------------------------------------------
    # EVENT TYPE
    # --------------------------------------------------------

    raw_event_type = clean_value(
        row.get("event_type")
        or row.get("event")
        or row.get("type")
    )

    if raw_event_type:
        raw_event_type = raw_event_type.upper().strip()

    # --------------------------------------------------------
    # IMPORTANT
    #
    # The CSV may contain event names such as:
    #
    # CREATED
    # ASSIGNED
    # ROUTED
    # IN_PROGRESS
    # STATUS_CHANGED
    # RESOLVED
    # CLOSED
    # ESCALATED
    # SLA_BREACHED
    # REOPENED
    # POLICY_RETRIEVED
    # RESPONSE_SENT
    # FEEDBACK_RECEIVED
    #
    # But schema.sql allows only:
    #
    # CREATED
    # ROUTED
    # STATUS_CHANGE
    # RESOLUTION
    # ESCALATION
    # MESSAGE_RECEIVED
    # MESSAGE_SENT
    # SLA_BREACH
    #
    # Therefore EVERYTHING is normalized here.
    # --------------------------------------------------------

    event_mapping = {

        # Ticket creation
        "CREATED":
            "CREATED",

        # Assignment/routing
        "ASSIGNED":
            "ROUTED",

        "ROUTED":
            "ROUTED",

        # Status changes
        "IN_PROGRESS":
            "STATUS_CHANGE",

        "STATUS_CHANGED":
            "STATUS_CHANGE",

        "STATUS_CHANGE":
            "STATUS_CHANGE",

        "REOPENED":
            "STATUS_CHANGE",

        # Resolution
        "RESOLVED":
            "RESOLUTION",

        "RESOLUTION":
            "RESOLUTION",

        "CLOSED":
            "RESOLUTION",

        # Escalation
        "ESCALATED":
            "ESCALATION",

        "ESCALATION":
            "ESCALATION",

        # SLA
        "SLA_BREACHED":
            "SLA_BREACH",

        "SLA_BREACH":
            "SLA_BREACH",

        # Messages
        "MESSAGE_RECEIVED":
            "MESSAGE_RECEIVED",

        "MESSAGE_RECIEVED":
            "MESSAGE_RECEIVED",

        "MESSAGE_SENT":
            "MESSAGE_SENT",

        # These generator events are represented
        # as message events in the database.
        "RESPONSE_SENT":
            "MESSAGE_SENT",

        # Policy retrieval is represented as
        # a system-generated message event.
        "POLICY_RETRIEVED":
            "MESSAGE_RECEIVED",

        # Feedback is also represented as a
        # received message/event.
        "FEEDBACK_RECEIVED":
            "MESSAGE_RECEIVED",
    }

    event_type = event_mapping.get(
        raw_event_type
    )

    # --------------------------------------------------------
    # SAFE FALLBACK
    # --------------------------------------------------------

    if event_type is None:

        if not raw_event_type:
            event_type = "STATUS_CHANGE"

        elif "CREAT" in raw_event_type:
            event_type = "CREATED"

        elif (
            "ASSIGN" in raw_event_type
            or "ROUT" in raw_event_type
        ):
            event_type = "ROUTED"

        elif (
            "STATUS" in raw_event_type
            or "PROGRESS" in raw_event_type
            or "REOPEN" in raw_event_type
        ):
            event_type = "STATUS_CHANGE"

        elif (
            "RESOLV" in raw_event_type
            or "CLOS" in raw_event_type
        ):
            event_type = "RESOLUTION"

        elif "ESCALAT" in raw_event_type:
            event_type = "ESCALATION"

        elif "BREACH" in raw_event_type:
            event_type = "SLA_BREACH"

        elif "RECEIV" in raw_event_type:
            event_type = "MESSAGE_RECEIVED"

        elif "SENT" in raw_event_type:
            event_type = "MESSAGE_SENT"

        else:
            # Final safe value.
            event_type = "STATUS_CHANGE"

    # --------------------------------------------------------
    # FINAL SAFETY CHECK
    # --------------------------------------------------------

    if event_type not in ALLOWED_EVENT_TYPES:
        event_type = "STATUS_CHANGE"

    # --------------------------------------------------------
    # STATUS VALUES
    # --------------------------------------------------------

    old_status = clean_value(
        row.get("old_status")
        or row.get("previous_status")
    )

    new_status = clean_value(
        row.get("new_status")
        or row.get("current_status")
        or row.get("status")
    )

    # --------------------------------------------------------
    # DERIVE STATUS WHEN MISSING
    # --------------------------------------------------------

    if event_type == "CREATED":

        old_status = None

        if not new_status:
            new_status = "OPEN"

    elif event_type == "ROUTED":

        if not old_status:
            old_status = "OPEN"

        if not new_status:
            new_status = old_status

    elif event_type == "STATUS_CHANGE":

        if not old_status:
            old_status = "OPEN"

        if not new_status:
            new_status = "IN_PROGRESS"

    elif event_type == "RESOLUTION":

        if not old_status:
            old_status = "IN_PROGRESS"

        if not new_status:
            new_status = "RESOLVED"

    elif event_type == "ESCALATION":

        if not old_status:
            old_status = "OPEN"

        if not new_status:
            new_status = "ESCALATED"

    # --------------------------------------------------------
    # MESSAGE EVENTS
    # --------------------------------------------------------

    elif event_type == "MESSAGE_RECEIVED":

        if not old_status:
            old_status = None

        if not new_status:
            new_status = old_status

    elif event_type == "MESSAGE_SENT":

        if not old_status:
            old_status = None

        if not new_status:
            new_status = old_status

    # --------------------------------------------------------
    # SLA BREACH
    # --------------------------------------------------------

    elif event_type == "SLA_BREACH":

        if not old_status:
            old_status = "OPEN"

        if not new_status:
            new_status = old_status

    # --------------------------------------------------------
    # EVENT TIMESTAMP
    # --------------------------------------------------------

    event_timestamp = safe_datetime(

        row.get("event_timestamp")
        or row.get("event_at")
        or row.get("created_at")
        or row.get("timestamp")
    )

    # --------------------------------------------------------
    # ACTOR TYPE
    # --------------------------------------------------------

    raw_actor_type = clean_value(
        row.get("actor_type")
        or row.get("actor")
        or row.get("sender_type")
    )

    if raw_actor_type:
        raw_actor_type = raw_actor_type.upper().strip()

    actor_mapping = {

        "REQUESTER":
            "REQUESTER",

        "STUDENT":
            "REQUESTER",

        "LEARNER":
            "REQUESTER",

        "USER":
            "REQUESTER",

        "AGENT":
            "AGENT",

        "SUPPORT_AGENT":
            "AGENT",

        "STAFF":
            "AGENT",

        "ADMIN":
            "AGENT",

        "ACADEMIC_ADMINISTRATOR":
            "AGENT",

        "SYSTEM":
            "SYSTEM",

        "AUTO":
            "SYSTEM",

        "AUTOMATED":
            "SYSTEM",
    }

    actor_type = actor_mapping.get(
        raw_actor_type,
        "SYSTEM"
    )

    # --------------------------------------------------------
    # ACTOR ID
    # --------------------------------------------------------

    actor_id = clean_value(
        row.get("actor_id")
        or row.get("sender_id")
    )

    if not actor_id:

        if actor_type == "REQUESTER":
            actor_id = "REQ-000001"

        elif actor_type == "AGENT":
            actor_id = "AGENT-001"

        else:
            actor_id = "SYSTEM-001"

    # --------------------------------------------------------
    # EVENT REASON
    # --------------------------------------------------------

    event_reason = clean_value(
        row.get("event_reason")
        or row.get("details")
        or row.get("reason")
        or row.get("description")
    )

    if not event_reason:

        event_reason = (
            f"{event_type} event for {ticket_id}"
        )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "event_id":
            event_id,

        "ticket_id":
            ticket_id,

        "event_type":
            event_type,

        "old_status":
            old_status,

        "new_status":
            new_status,

        "event_timestamp":
            event_timestamp,

        "actor_type":
            actor_type,

        "actor_id":
            actor_id,

        "event_reason":
            event_reason,
    }


# ============================================================
# TRANSFORM: RESOLUTION FEEDBACK
# ============================================================

def transform_feedback(row):

    feedback_id = clean_value(
        row.get("feedback_id")
    )

    ticket_id = clean_value(
        row.get("ticket_id")
    )

    rating = safe_int(
        row.get("rating")
    )

    if rating is None:
        rating = 3

    # Keep rating inside normal 1-5 range.
    if rating < 1:
        rating = 1

    if rating > 5:
        rating = 5

    feedback_text = clean_value(
        row.get("feedback_text")
        or row.get("comment")
    )

    if not feedback_text:
        feedback_text = (
            "Synthetic resolution feedback."
        )

    raw_resolution_status = clean_value(
        row.get("resolution_status")
    )

    if raw_resolution_status:
        resolution_status = (
            raw_resolution_status.upper()
        )

    else:

        resolution_status = (
            "RESOLVED"
            if rating >= 3
            else "OPEN"
        )

    submitted_at = safe_datetime(
        row.get("submitted_at")
        or row.get("created_at")
    )

    return {
        "feedback_id":
            feedback_id,

        "ticket_id":
            ticket_id,

        "rating":
            rating,

        "feedback_text":
            feedback_text,

        "resolution_status":
            resolution_status,

        "submitted_at":
            submitted_at,
    }


# ============================================================
# TRANSFORM: GROUND TRUTH
# ============================================================

def transform_ground_truth(row):

    ticket_id = clean_value(
        row.get("ticket_id")
    )

    ground_truth_id = clean_value(
        row.get("ground_truth_id")
    )

    if not ground_truth_id:

        if ticket_id:

            ground_truth_id = (
                f"GT-{ticket_id}"
            )

    expected_team = clean_value(
        row.get("expected_team")
        or row.get("actual_team")
    )

    if not expected_team:
        expected_team = (
            "Academic Support Team"
        )

    # --------------------------------------------------------
    # SLA
    # --------------------------------------------------------

    expected_sla = safe_int(
        row.get("expected_sla_hours")
        or row.get("sla_hours")
    )

    if expected_sla is None:

        priority = clean_value(
            row.get("priority")
        )

        if priority:
            priority = priority.upper()

        expected_sla = DEFAULT_SLA_HOURS.get(
            priority,
            24
        )

    # --------------------------------------------------------
    # ESCALATION
    # --------------------------------------------------------

    raw_escalation = clean_value(
        row.get("expected_escalation")
    )

    if raw_escalation:

        expected_escalation = (
            1
            if raw_escalation.upper()
            in {
                "YES",
                "TRUE",
                "1",
                "Y"
            }
            else 0
        )

    else:

        expected_escalation = 0

    # --------------------------------------------------------
    # ISSUE TYPE
    # --------------------------------------------------------

    issue_type = clean_value(
        row.get("issue_type")
    )

    if not issue_type:
        issue_type = "NONE"

    # --------------------------------------------------------
    # EXPECTED POLICY
    # --------------------------------------------------------

    expected_policy_id = clean_value(
        row.get("expected_policy_id")
        or row.get("cited_policy_id")
    )

    # --------------------------------------------------------
    # SOURCE VALIDITY
    # --------------------------------------------------------

    raw_source_valid = clean_value(
        row.get("expected_source_valid")
    )

    if raw_source_valid is not None:

        expected_source_valid = (
            1
            if str(raw_source_valid).lower()
            in {
                "1",
                "true",
                "yes"
            }
            else 0
        )

    else:

        expected_source_valid = (
            0
            if issue_type ==
            "expired_policy_citation"
            else 1
        )

    # --------------------------------------------------------
    # ANOMALY
    # --------------------------------------------------------

    raw_anomaly = clean_value(
        row.get("expected_anomaly")
        or row.get("record_status")
    )

    if raw_anomaly:

        expected_anomaly = (
            1
            if str(raw_anomaly).upper()
            in {
                "1",
                "TRUE",
                "YES",
                "ANOMALY"
            }
            else 0
        )

    else:

        expected_anomaly = (
            0
            if issue_type == "NONE"
            else 1
        )

    return {
        "ground_truth_id":
            ground_truth_id,

        "ticket_id":
            ticket_id,

        "expected_team":
            expected_team,

        "expected_sla_hours":
            expected_sla,

        "expected_escalation":
            expected_escalation,

        "issue_type":
            issue_type,

        "expected_policy_id":
            expected_policy_id,

        "expected_source_valid":
            expected_source_valid,

        "expected_anomaly":
            expected_anomaly,
    }


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_table_columns(
    conn,
    table_name
):

    cursor = conn.execute(
        f"PRAGMA table_info({table_name})"
    )

    return [
        row[1]
        for row in cursor.fetchall()
    ]


def build_insert_sql(
    table_name,
    columns
):

    column_text = ", ".join(
        f'"{column}"'
        for column in columns
    )

    placeholders = ", ".join(
        "?"
        for _ in columns
    )

    return (
        f'INSERT INTO "{table_name}" '
        f'({column_text}) '
        f'VALUES ({placeholders})'
    )


# ============================================================
# LOAD ROWS
# ============================================================

def load_rows(
    conn,
    table_name,
    rows
):

    if not rows:

        print(
            f"[PASS] {table_name:<30} 0 rows"
        )

        return

    columns = get_table_columns(
        conn,
        table_name
    )

    values = []

    for row in rows:

        converted = []

        for column in columns:

            converted.append(
                clean_value(
                    row.get(column)
                )
            )

        values.append(
            tuple(converted)
        )

    sql = build_insert_sql(
        table_name,
        columns
    )

    conn.executemany(
        sql,
        values
    )

    print(
        f"[PASS] {table_name:<30} "
        f"{len(values)} rows"
    )


# ============================================================
# LOAD TABLE
# ============================================================

def load_table(
    conn,
    table_name,
    filename
):

    rows = read_csv(filename)

    if table_name == "ticket":

        rows = [
            transform_ticket(row)
            for row in rows
        ]

    elif table_name == "message":

        rows = [
            transform_message(row)
            for row in rows
        ]

    elif table_name == "assignment":

        rows = [
            transform_assignment(row)
            for row in rows
        ]

    elif table_name == "assignment_source":

        rows = [
            transform_assignment_source(row)
            for row in rows
        ]

    elif table_name == "sla":

        rows = [
            transform_sla(row)
            for row in rows
        ]

    elif table_name == "event_history":

        rows = [
            transform_event(row)
            for row in rows
        ]

    elif table_name == "resolution_feedback":

        rows = [
            transform_feedback(row)
            for row in rows
        ]

    elif table_name == "ground_truth":

        rows = [
            transform_ground_truth(row)
            for row in rows
        ]

    # Parent tables are already compatible
    # with the database schema.

    load_rows(
        conn,
        table_name,
        rows
    )


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database(conn):

    if not os.path.exists(
        SCHEMA_PATH
    ):

        raise FileNotFoundError(
            f"schema.sql not found: "
            f"{SCHEMA_PATH}"
        )

    with open(
        SCHEMA_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        schema_sql = f.read()

    conn.executescript(
        schema_sql
    )

    print(
        "[PASS] Database schema created"
    )


# ============================================================
# PRINT SCHEMA
# ============================================================

def print_schema(conn):

    print()
    print("=" * 60)
    print("DATABASE SCHEMA")
    print("=" * 60)

    cursor = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )

    tables = [
        row[0]
        for row in cursor.fetchall()
    ]

    for table in tables:

        print()
        print(table)

        info = conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()

        for item in info:

            print(
                f"  - {item[1]} ({item[2]})"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    print("=" * 60)
    print(
        "ACADEMIC SUPPORT AI DATABASE BUILDER"
    )
    print("=" * 60)

    print(
        f"Data directory: {DATA_DIR}"
    )

    print(
        f"Database path:  {DB_PATH}"
    )

    print()

    # Always rebuild database from scratch.
    if os.path.exists(DB_PATH):

        os.remove(DB_PATH)

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    try:

        create_database(conn)

        print_schema(conn)

        print()
        print("=" * 60)
        print("LOADING CSV DATA")
        print("=" * 60)

        for table_name, filename in TABLE_FILES:

            load_table(
                conn,
                table_name,
                filename
            )

        conn.commit()

        print()
        print("=" * 60)
        print("DATABASE BUILD COMPLETED")
        print("=" * 60)

        print()

        print(
            "Database created successfully:"
        )

        print(
            DB_PATH
        )

    except Exception as exc:

        conn.rollback()

        print()
        print("=" * 60)
        print("DATABASE BUILD FAILED")
        print("=" * 60)

        print(
            f"Error: {exc}"
        )

        raise

    finally:

        conn.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()