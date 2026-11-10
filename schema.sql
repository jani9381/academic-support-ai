-- ============================================================
-- ACADEMIC SUPPORT AI
-- RELATIONAL DATABASE SCHEMA
-- SQLite
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. ROLE
-- ============================================================

CREATE TABLE IF NOT EXISTS role (
    role_id TEXT PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE
);

-- ============================================================
-- 2. REQUESTER
-- ============================================================

CREATE TABLE IF NOT EXISTS requester (
    requester_id TEXT PRIMARY KEY,
    requester_name TEXT NOT NULL,
    role_id TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,

    FOREIGN KEY (role_id)
        REFERENCES role(role_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- ============================================================
-- 3. CATEGORY
-- ============================================================

CREATE TABLE IF NOT EXISTS category (
    category_id TEXT PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE,
    owning_team TEXT NOT NULL
);

-- ============================================================
-- 4. TERM
-- ============================================================

CREATE TABLE IF NOT EXISTS term (
    term_id TEXT PRIMARY KEY,
    term_name TEXT NOT NULL UNIQUE,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,

    CHECK (start_date < end_date)
);

-- ============================================================
-- 5. POLICY DOCUMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS policy_document (
    policy_id TEXT PRIMARY KEY,
    policy_title TEXT NOT NULL,
    domain TEXT NOT NULL,
    version TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    policy_text TEXT NOT NULL,
    source_url TEXT,

    CHECK (
        effective_to IS NULL
        OR effective_from <= effective_to
    )
);

-- ============================================================
-- 6. KNOWLEDGE ARTICLE
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge_article (
    article_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    title TEXT NOT NULL,
    domain TEXT NOT NULL,
    content TEXT NOT NULL,
    version TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    status TEXT NOT NULL,

    FOREIGN KEY (policy_id)
        REFERENCES policy_document(policy_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CHECK (
        effective_to IS NULL
        OR effective_from <= effective_to
    ),

    CHECK (
        status IN (
            'DRAFT',
            'PUBLISHED',
            'ARCHIVED',
            'RETIRED'
        )
    )
);

-- ============================================================
-- 7. TICKET
-- ============================================================

CREATE TABLE IF NOT EXISTS ticket (
    ticket_id TEXT PRIMARY KEY,

    requester_id TEXT NOT NULL,
    category_id TEXT NOT NULL,
    term_id TEXT NOT NULL,

    subject TEXT NOT NULL,
    description TEXT NOT NULL,

    priority TEXT NOT NULL,
    status TEXT NOT NULL,

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolved_at TEXT,

    FOREIGN KEY (requester_id)
        REFERENCES requester(requester_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (category_id)
        REFERENCES category(category_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (term_id)
        REFERENCES term(term_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CHECK (
        priority IN (
            'CRITICAL',
            'HIGH',
            'MEDIUM',
            'LOW'
        )
    ),

    CHECK (
        status IN (
            'OPEN',
            'IN_PROGRESS',
            'WAITING',
            'RESOLVED',
            'CLOSED',
            'ESCALATED'
        )
    ),

    CHECK (
        updated_at >= created_at
    ),

    CHECK (
        resolved_at IS NULL
        OR resolved_at >= created_at
    ),

    CHECK (
        (
            status IN ('RESOLVED', 'CLOSED')
            AND resolved_at IS NOT NULL
        )
        OR
        (
            status NOT IN ('RESOLVED', 'CLOSED')
        )
    )
);

-- ============================================================
-- 8. MESSAGE
-- ============================================================

CREATE TABLE IF NOT EXISTS message (
    message_id TEXT PRIMARY KEY,

    ticket_id TEXT NOT NULL,

    sender_type TEXT NOT NULL,
    sender_id TEXT,

    message_text TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES ticket(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CHECK (
        sender_type IN (
            'REQUESTER',
            'AGENT',
            'SYSTEM'
        )
    )
);

-- ============================================================
-- 9. ASSIGNMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS assignment (
    assignment_id TEXT PRIMARY KEY,

    ticket_id TEXT NOT NULL,

    assigned_team TEXT NOT NULL,
    assigned_by TEXT NOT NULL,

    assigned_at TEXT NOT NULL,
    routing_method TEXT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES ticket(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CHECK (
        routing_method IN (
            'RULE_BASED',
            'MANUAL',
            'AI_ASSISTED',
            'ESCALATION'
        )
    )
);

-- ============================================================
-- 10. ASSIGNMENT SOURCE
-- ============================================================

CREATE TABLE IF NOT EXISTS assignment_source (
    assignment_source_id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticket_id TEXT NOT NULL,
    assignment_id TEXT NOT NULL,

    source_type TEXT NOT NULL,
    source_reference TEXT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES ticket(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (assignment_id)
        REFERENCES assignment(assignment_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE (
        ticket_id,
        assignment_id,
        source_type,
        source_reference
    ),

    CHECK (
        source_type IN (
            'POLICY',
            'KNOWLEDGE_ARTICLE',
            'ROUTING_RULE',
            'SYSTEM_RULE'
        )
    )
);

-- ============================================================
-- 11. SLA
-- ============================================================

CREATE TABLE IF NOT EXISTS sla (
    sla_id TEXT PRIMARY KEY,

    ticket_id TEXT NOT NULL,

    priority TEXT NOT NULL,
    sla_hours INTEGER NOT NULL,

    started_at TEXT NOT NULL,
    due_at TEXT NOT NULL,

    breached INTEGER NOT NULL DEFAULT 0,
    breached_at TEXT,

    escalation_required INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (ticket_id)
        REFERENCES ticket(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CHECK (
        priority IN (
            'CRITICAL',
            'HIGH',
            'MEDIUM',
            'LOW'
        )
    ),

    CHECK (
        sla_hours > 0
    ),

    CHECK (
        due_at >= started_at
    ),

    CHECK (
        breached IN (0, 1)
    ),

    CHECK (
        escalation_required IN (0, 1)
    ),

    CHECK (
        (
            breached = 1
            AND breached_at IS NOT NULL
        )
        OR
        (
            breached = 0
            AND breached_at IS NULL
        )
    )
);

-- ============================================================
-- 12. EVENT HISTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS event_history (
    event_id TEXT PRIMARY KEY,

    ticket_id TEXT NOT NULL,

    event_type TEXT NOT NULL,

    old_status TEXT,
    new_status TEXT,

    event_timestamp TEXT NOT NULL,

    actor_type TEXT,
    actor_id TEXT,

    event_reason TEXT,

    FOREIGN KEY (ticket_id)
        REFERENCES ticket(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CHECK (
        event_type IN (
            'CREATED',
            'ROUTED',
            'STATUS_CHANGE',
            'RESOLUTION',
            'ESCALATION',
            'MESSAGE_RECEIVED',
            'MESSAGE_SENT',
            'SLA_BREACH'
        )
    )
);

-- ============================================================
-- 13. RESOLUTION FEEDBACK
-- ============================================================

CREATE TABLE IF NOT EXISTS resolution_feedback (
    feedback_id TEXT PRIMARY KEY,

    ticket_id TEXT NOT NULL UNIQUE,

    rating INTEGER,
    feedback_text TEXT,
    resolution_status TEXT,
    submitted_at TEXT,

    FOREIGN KEY (ticket_id)
        REFERENCES ticket(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CHECK (
        rating IS NULL
        OR rating BETWEEN 1 AND 5
    )
);

-- ============================================================
-- 14. GROUND TRUTH
-- ============================================================

-- Ground truth is evaluation metadata.
-- It must never be used as an input feature by the routing,
-- retrieval, SLA, or anomaly detection logic.

CREATE TABLE IF NOT EXISTS ground_truth (
    ground_truth_id TEXT PRIMARY KEY,

    ticket_id TEXT NOT NULL UNIQUE,

    expected_team TEXT,
    expected_sla_hours INTEGER,
    expected_escalation INTEGER,

    issue_type TEXT NOT NULL,

    expected_policy_id TEXT,
    expected_source_valid INTEGER,

    expected_anomaly INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (ticket_id)
        REFERENCES ticket(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (expected_policy_id)
        REFERENCES policy_document(policy_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CHECK (
        expected_escalation IS NULL
        OR expected_escalation IN (0, 1)
    ),

    CHECK (
        expected_source_valid IS NULL
        OR expected_source_valid IN (0, 1)
    ),

    CHECK (
        expected_anomaly IN (0, 1)
    ),

    CHECK (
        issue_type IN (
            'NONE',
            'expired_policy_citation',
            'unauthorized_routing',
            'unsupported_fact',
            'business_hours_sla_bug',
            'missing_escalation'
        )
    )
);

-- ============================================================
-- 15. SOURCE MANIFEST
-- ============================================================

CREATE TABLE IF NOT EXISTS source_manifest (
    source_id TEXT PRIMARY KEY,

    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,

    source_url TEXT,
    version TEXT,
    retrieval_date TEXT,

    license TEXT,
    attribution TEXT,

    transformation_notes TEXT
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_requester_role
    ON requester(role_id);

CREATE INDEX IF NOT EXISTS idx_ticket_requester
    ON ticket(requester_id);

CREATE INDEX IF NOT EXISTS idx_ticket_category
    ON ticket(category_id);

CREATE INDEX IF NOT EXISTS idx_ticket_term
    ON ticket(term_id);

CREATE INDEX IF NOT EXISTS idx_ticket_status
    ON ticket(status);

CREATE INDEX IF NOT EXISTS idx_ticket_priority
    ON ticket(priority);

CREATE INDEX IF NOT EXISTS idx_ticket_created_at
    ON ticket(created_at);

CREATE INDEX IF NOT EXISTS idx_message_ticket
    ON message(ticket_id);

CREATE INDEX IF NOT EXISTS idx_message_created_at
    ON message(created_at);

CREATE INDEX IF NOT EXISTS idx_assignment_ticket
    ON assignment(ticket_id);

CREATE INDEX IF NOT EXISTS idx_assignment_team
    ON assignment(assigned_team);

CREATE INDEX IF NOT EXISTS idx_assignment_source_ticket
    ON assignment_source(ticket_id);

CREATE INDEX IF NOT EXISTS idx_assignment_source_assignment
    ON assignment_source(assignment_id);

CREATE INDEX IF NOT EXISTS idx_sla_ticket
    ON sla(ticket_id);

CREATE INDEX IF NOT EXISTS idx_sla_due_at
    ON sla(due_at);

CREATE INDEX IF NOT EXISTS idx_sla_breached
    ON sla(breached);

CREATE INDEX IF NOT EXISTS idx_event_ticket
    ON event_history(ticket_id);

CREATE INDEX IF NOT EXISTS idx_event_timestamp
    ON event_history(event_timestamp);

CREATE INDEX IF NOT EXISTS idx_event_type
    ON event_history(event_type);

CREATE INDEX IF NOT EXISTS idx_feedback_ticket
    ON resolution_feedback(ticket_id);

CREATE INDEX IF NOT EXISTS idx_ground_truth_ticket
    ON ground_truth(ticket_id);

CREATE INDEX IF NOT EXISTS idx_ground_truth_issue_type
    ON ground_truth(issue_type);

CREATE INDEX IF NOT EXISTS idx_ground_truth_anomaly
    ON ground_truth(expected_anomaly);

-- ============================================================
-- END OF SCHEMA
-- ============================================================