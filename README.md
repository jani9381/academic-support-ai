# Academic Support AI

An end-to-end AI-powered academic support workflow that routes learner/faculty requests, retrieves policy-grounded answers, calculates SLA and escalation decisions, preserves event traceability, and evaluates workflow accuracy.

## 1. Project Overview

The system simulates an academic support environment where learners and faculty submit requests related to:

- Financial Aid
- Registration
- IT Support
- Accessibility

The workflow performs:

1. Ticket intake
2. Category-based routing
3. SLA calculation
4. Escalation decision
5. Policy/knowledge retrieval
6. Grounded response generation
7. Source citation
8. Event traceability
9. Resolution feedback
10. Evaluation against documented ground truth
11. Edge-case/anomaly validation

The project uses deterministic synthetic data so the complete workflow can be reproduced locally.

---

## 2. Key Features

### Request Routing

Tickets are automatically routed to the appropriate support team:

| Category | Team |
|---|---|
| FINANCIAL_AID | Financial Aid Team |
| REGISTRATION | Registrar Team |
| IT | IT Support Team |
| ACCESSIBILITY | Accessibility Team |

### SLA Management

SLA targets are determined from ticket priority:

| Priority | SLA |
|---|---:|
| CRITICAL | 4 hours |
| HIGH | 8 hours |
| MEDIUM | 24 hours |
| LOW | 72 hours |

### Escalation

Escalation considers:

- Critical priority
- Unknown/invalid routing
- Current ticket lifecycle status
- SLA deadline
- SLA breach conditions

### Policy-Grounded Responses

The retrieval workflow searches policy documents and knowledge articles and returns:

- Retrieved source
- Source type
- Confidence
- Effective-date validation
- Grounded answer
- Citation/reference ID

### Traceability

The system preserves:

- Ticket history
- Message history
- Assignment records
- Assignment sources
- SLA records
- Policy citations
- Resolution feedback
- Event history

Historical state changes are stored as events instead of overwriting previous states.

---

## 3. Technology Stack

- Python
- Pandas
- NumPy
- SQLite
- Streamlit
- Rule-based routing
- Policy retrieval
- Synthetic data generation
- Automated validation
- Workflow evaluation

---

## 4. Project Structure

```text
academic-support-ai-final/
│
├── data/
│   ├── requester.csv
│   ├── role.csv
│   ├── category.csv
│   ├── term.csv
│   ├── policy_document.csv
│   ├── knowledge_article.csv
│   ├── ticket.csv
│   ├── message.csv
│   ├── assignment.csv
│   ├── assignment_source.csv
│   ├── sla.csv
│   ├── event_history.csv
│   ├── resolution_feedback.csv
│   ├── ground_truth.csv
│   └── source_manifest.csv
│
├── outputs/
│   ├── academic_support.db
│   ├── generation_summary.json
│   ├── validation_summary.json
│   ├── workflow_result.json
│   └── evaluation_summary.json
│
├── generate_data.py
├── validation.py
├── database.py
├── policy_retriever.py
├── routing.py
├── support_workflow.py
├── evaluation.py
├── edge_case_tests.py
├── app.py
├── schema.sql
├── requirements.txt
├── README.md
└── .gitignore