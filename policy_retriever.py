import csv
import os
import re
from datetime import datetime


DATA_DIR = "data"


DOMAIN_KEYWORDS = {
    "FINANCIAL_AID": [
        "financial",
        "aid",
        "scholarship",
        "grant",
        "fee",
        "fund",
        "funding",
        "fafsa",
        "loan",
    ],
    "REGISTRATION": [
        "register",
        "registration",
        "course",
        "enroll",
        "enrollment",
        "drop",
        "withdraw",
        "semester",
    ],
    "IT": [
        "password",
        "login",
        "account",
        "computer",
        "system",
        "internet",
        "wifi",
        "lms",
        "technical",
    ],
    "ACCESSIBILITY": [
        "accessibility",
        "accommodation",
        "disability",
        "accessible",
        "support",
        "assistive",
    ],
}


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        return []

    with open(
        path,
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def load_policies():
    return load_csv("policy_document.csv")


def load_articles():
    return load_csv("knowledge_article.csv")


def tokenize(text):
    return set(
        re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
            str(text).lower()
        )
    )


def keyword_score(query, document_text):

    query_words = tokenize(query)
    document_words = tokenize(document_text)

    if not query_words:
        return 0.0

    overlap = query_words.intersection(
        document_words
    )

    return len(overlap) / len(query_words)


def domain_score(query, domain):

    query_lower = str(query).lower()

    keywords = DOMAIN_KEYWORDS.get(
        domain,
        []
    )

    if not keywords:
        return 0.0

    matches = sum(
        1
        for keyword in keywords
        if keyword in query_lower
    )

    return matches / len(keywords)


def is_policy_effective(policy, request_date):

    try:

        date_value = datetime.strptime(
            request_date,
            "%Y-%m-%d"
        ).date()

        start_date = datetime.strptime(
            policy["effective_from"],
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            policy["effective_to"],
            "%Y-%m-%d"
        ).date()

        return (
            start_date
            <= date_value
            <= end_date
        )

    except Exception:
        return False


def retrieve_policy(
    query,
    request_date=None,
    domain=None,
    top_k=3
):

    policies = load_policies()
    articles = load_articles()

    candidates = []

    # ==================================================
    # POLICY DOCUMENTS
    # ==================================================

    for policy in policies:

        # IMPORTANT:
        # policy_document.csv uses:
        # policy_title
        # policy_text
        policy_text = " ".join([
            policy.get(
                "domain",
                ""
            ),

            policy.get(
                "policy_title",
                ""
            ),

            policy.get(
                "policy_text",
                ""
            ),
        ])

        text_score = keyword_score(
            query,
            policy_text
        )

        domain_match = 0.0

        if domain:

            if policy.get(
                "domain"
            ) == domain:

                domain_match = 1.0

        calculated_score = (
            (text_score * 0.60)
            +
            (domain_match * 0.40)
        )

        effective = True

        if request_date:

            effective = is_policy_effective(
                policy,
                request_date
            )

        candidates.append({

            "source_type":
                "POLICY",

            "source_id":
                policy["policy_id"],

            "title":
                policy["policy_title"],

            "domain":
                policy["domain"],

            "version":
                policy["version"],

            "effective":
                effective,

            "score":
                calculated_score,

            "content":
                policy["policy_text"],
        })

    # ==================================================
    # KNOWLEDGE ARTICLES
    # ==================================================

    for article in articles:

        article_text = " ".join([
            article.get(
                "title",
                ""
            ),

            article.get(
                "content",
                ""
            ),

            article.get(
                "domain",
                ""
            ),
        ])

        text_score = keyword_score(
            query,
            article_text
        )

        domain_match = 0.0

        if domain:

            if article.get(
                "domain"
            ) == domain:

                domain_match = 1.0

        calculated_score = (
            (text_score * 0.60)
            +
            (domain_match * 0.40)
        )

        candidates.append({

            "source_type":
                "KNOWLEDGE_ARTICLE",

            "source_id":
                article["article_id"],

            "title":
                article["title"],

            "domain":
                article.get(
                    "domain",
                    ""
                ),

            "version":
                article.get(
                    "version",
                    ""
                ),

            "effective":
                True,

            "score":
                calculated_score,

            "content":
                article["content"],
        })

    # ==================================================
    # RANK SOURCES
    # ==================================================

    candidates.sort(
        key=lambda x: (
            x["effective"],
            x["score"]
        ),
        reverse=True
    )

    results = candidates[:top_k]

    if not results:

        return {
            "status":
                "NO_SOURCE",

            "confidence":
                "LOW",

            "sources":
                []
        }

    best_score = results[0]["score"]

    if best_score >= 0.60:

        confidence = "HIGH"

    elif best_score >= 0.30:

        confidence = "MEDIUM"

    else:

        confidence = "LOW"

    return {
        "status":
            "SOURCE_FOUND",

        "confidence":
            confidence,

        "sources":
            results,
    }


def build_grounded_answer(
    query,
    retrieval_result
):

    if not retrieval_result[
        "sources"
    ]:

        return {

            "answer":
                "I could not find sufficient policy-grounded information to answer this request. The request should be reviewed by support staff.",

            "citation":
                None,

            "grounded":
                False,
        }

    best = retrieval_result[
        "sources"
    ][0]

    if best["score"] < 0.30:

        return {

            "answer":
                "I found related information, but the available source does not provide enough evidence to answer confidently. Please escalate this request for human review.",

            "citation":
                best["source_id"],

            "grounded":
                False,
        }

    answer = (
        f"According to "
        f"{best['title']}: "
        f"{best['content']}"
    )

    return {

        "answer":
            answer,

        "citation":
            best["source_id"],

        "grounded":
            True,
    }


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    result = retrieve_policy(
        query="I need help with financial aid",
        request_date="2026-05-01",
        domain="FINANCIAL_AID",
    )

    print()
    print(
        "POLICY RETRIEVAL TEST"
    )
    print(
        "====================="
    )

    print(
        "Status:",
        result["status"]
    )

    print(
        "Confidence:",
        result["confidence"]
    )

    for source in result[
        "sources"
    ]:

        print(
            source["source_id"],
            "|",
            source["title"],
            "| score:",
            round(
                source["score"],
                3
            ),
            "| effective:",
            source["effective"]
        )

    answer = build_grounded_answer(
        "I need help with financial aid",
        result
    )

    print()
    print("ANSWER:")

    print(
        answer["answer"]
    )

    print()
    print("CITATION:")

    print(
        answer["citation"]
    )