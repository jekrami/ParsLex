#!/usr/bin/env python3
"""Generate golden benchmark datasets for iran-oil-gas domain pack."""

import json
from pathlib import Path

PACK_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "packs" / "iran-oil-gas" / "benchmarks"

QA_TOPICS = [
    ("epc_liability", "What is the standard limitation of liability cap in Iranian EPC contracts?",
     "EPC contracts typically cap liability at 100% of contract value with exclusions for fraud and willful misconduct.",
     "iogc-epc-guidelines", "limitation_of_liability"),
    ("force_majeure", "What events qualify as force majeure in oil & gas contracts?",
     "Force majeure includes war, natural disasters, government actions, and sanctions affecting performance.",
     "iogc-epc-guidelines", "force_majeure"),
    ("hse_requirements", "What HSE standards apply to offshore oil operations?",
     "HSE requirements include compliance with national environmental regulations and industry API standards.",
     "iogc-hse-regulations", "health_safety_environment"),
    ("local_content", "What are the local content requirements for petroleum procurement?",
     "Local content requirements mandate minimum domestic manufacturing and employment percentages.",
     "iogc-local-content", "local_content"),
    ("payment_milestone", "How are milestone payments structured in EPC contracts?",
     "Milestone payments are tied to engineering, procurement, and construction completion stages.",
     "iogc-epc-guidelines", "payment_terms"),
    ("procurement_tender", "What is the minimum bid bond for petroleum tenders?",
     "Bid bonds are typically required at 1-2% of estimated contract value per tender regulations.",
     "iogc-tender-regulations", "performance_guarantee"),
    ("nda_duration", "What is the standard confidentiality period in oil & gas NDAs?",
     "Confidentiality obligations typically survive 3-5 years after agreement termination.",
     "iogc-nioc-standard-contracts", "confidentiality"),
    ("jv_governance", "How is governance structured in oil & gas joint ventures?",
     "JV governance includes board composition, voting thresholds, and reserved matters.",
     "iogc-foreign-investment", "governing_law"),
    ("insurance_coverage", "What insurance is required for EPC contractors?",
     "Contractors must maintain CAR, third-party liability, and professional indemnity insurance.",
     "iogc-epc-guidelines", "insurance"),
    ("dispute_resolution", "What dispute resolution mechanisms are used in NIOC contracts?",
     "Disputes may be resolved through negotiation, mediation, or ICC arbitration per contract terms.",
     "iogc-nioc-standard-contracts", "jurisdiction_dispute"),
]

DOCUMENT_TYPES = [
    "epc_contract", "procurement_contract", "service_agreement",
    "equipment_supply_contract", "confidentiality_agreement", "joint_venture_agreement", "tender_document"
]

CLAUSE_CHECKS = [
    ("limitation_of_liability", "high", True),
    ("force_majeure", "medium", True),
    ("health_safety_environment", "high", True),
    ("payment_terms", "medium", True),
    ("governing_law", "high", True),
    ("confidentiality", "high", False),
    ("local_content", "medium", False),
    ("anti_corruption", "high", False),
    ("insurance", "medium", True),
    ("warranties", "medium", True),
]


def generate_qa() -> list[dict]:
    items = []
    idx = 1
    for topic_id, question, answer, corpus, clause in QA_TOPICS:
        for lang in ("en", "fa"):
            items.append({
                "id": f"qa-{idx:03d}",
                "topic": topic_id,
                "language": lang,
                "question": question if lang == "en" else f"[FA] {question}",
                "expected_answer_contains": answer.split(".")[0].lower()[:40],
                "expected_sources": [{"corpus_id": corpus, "clause_type": clause}],
                "difficulty": "medium",
            })
            idx += 1

    # Additional synthetic Q&A to reach 55+
    extra_questions = [
        ("retention_money", "What is the typical retention percentage in EPC contracts?", "retention", "payment_terms"),
        ("liquidated_damages", "How are liquidated damages calculated for delay?", "liquidated", "liquidated_damages"),
        ("change_order", "What is the process for change orders in EPC projects?", "change order", "change_order"),
        ("warranty_period", "What is the standard warranty period for equipment supply?", "warranty", "warranties"),
        ("performance_bank_guarantee", "What percentage is required for performance bank guarantee?", "performance guarantee", "performance_guarantee"),
        ("environmental_permit", "What environmental permits are needed for drilling?", "environmental", "compliance_obligation"),
        ("labor_visa", "What are foreign worker visa requirements for oil projects?", "labor", "compliance_obligation"),
        ("tax_withholding", "What withholding tax applies to foreign contractors?", "withholding", "payment_obligation"),
        ("intellectual_property", "Who owns IP for engineering designs in service contracts?", "intellectual property", "intellectual_property"),
        ("termination_convenience", "Can the employer terminate EPC contract for convenience?", "termination", "termination"),
        ("suspension_rights", "What are employer suspension rights during EPC execution?", "suspension", "termination"),
        ("defects_liability", "What is the defects liability period for construction works?", "defects liability", "warranties"),
        ("price_escalation", "Are price escalation clauses allowed in long-term supply contracts?", "escalation", "payment_terms"),
        ("currency_risk", "How is currency risk allocated in petroleum contracts?", "currency", "payment_terms"),
        ("subcontracting", "What are subcontracting approval requirements?", "subcontract", "scope_of_work"),
        ("assignment_restrictions", "Can contractors assign rights without employer consent?", "assignment", "termination"),
        ("parent_company_guarantee", "When is a parent company guarantee required?", "parent company", "performance_guarantee"),
        ("safety_incident_reporting", "What is the timeline for reporting HSE incidents?", "incident reporting", "hse_obligation"),
        ("bank_guarantee_validity", "How long must bid bonds remain valid after bid opening?", "bid bond", "performance_guarantee"),
        ("advance_payment_guarantee", "Is an advance payment guarantee required for EPC contracts?", "advance payment", "payment_terms"),
        ("materials_testing", "What materials testing standards apply to pipeline construction?", "testing", "scope_of_work"),
        ("commissioning_handover", "What are commissioning and handover requirements?", "commissioning", "delivery_obligation"),
        ("spare_parts", "Are spare parts obligations included in equipment supply contracts?", "spare parts", "warranties"),
        ("training_obligation", "Must suppliers provide operator training?", "training", "performance_obligation"),
        ("export_control", "How do sanctions affect petroleum equipment imports?", "sanctions", "compliance_obligation"),
        ("data_protection", "What data protection rules apply to seismic survey data?", "data protection", "confidentiality"),
        ("audit_rights", "Do employers have audit rights over contractor accounts?", "audit", "reporting_obligation"),
        ("set_off_rights", "Can employers set off claims against milestone payments?", "set off", "payment_terms"),
        ("consequential_damages", "Are consequential damages typically excluded?", "consequential", "limitation_of_liability"),
        ("indemnity_scope", "What is the scope of indemnification for third-party claims?", "indemnif", "indemnification"),
        ("permits_responsibility", "Who obtains operating permits for oil facilities?", "permits", "compliance_obligation"),
        ("decommissioning", "What decommissioning obligations apply at contract end?", "decommission", "scope_of_work"),
        ("title_transfer", "When does title to equipment transfer to buyer?", "title", "delivery_obligation"),
        ("packaging_shipping", "What Incoterms are standard for equipment supply?", "incoterm", "delivery_schedule"),
        ("quality_inspection", "What third-party inspection is required before shipment?", "inspection", "warranties"),
        ("penalty_cap", "Is there a cap on liquidated damages for delay?", "cap", "liquidated_damages"),
        ("notice_provisions", "What notice periods apply for contract termination?", "notice", "termination"),
    ]

    for topic_id, question, keyword, clause in extra_questions:
        items.append({
            "id": f"qa-{idx:03d}",
            "topic": topic_id,
            "language": "en",
            "question": question,
            "expected_answer_contains": keyword,
            "expected_sources": [{"corpus_id": "iogc-epc-guidelines", "clause_type": clause}],
            "difficulty": "medium",
        })
        idx += 1

    return items


def generate_analysis() -> list[dict]:
    items = []
    for i, doc_type in enumerate(DOCUMENT_TYPES):
        for j, (clause, severity, required) in enumerate(CLAUSE_CHECKS):
            case_id = f"analysis-{i * len(CLAUSE_CHECKS) + j + 1:03d}"
            items.append({
                "id": case_id,
                "document_type": doc_type,
                "description": f"Test {clause} detection in {doc_type}",
                "input_summary": f"Sample {doc_type} with {'present' if required else 'missing'} {clause} clause",
                "expected_clauses": [
                    {
                        "type": clause,
                        "present": required if doc_type in ("epc_contract", "procurement_contract", "service_agreement") else False,
                    }
                ],
                "expected_compliance": [
                    {
                        "rule_id": f"{doc_type}_{clause}_check",
                        "severity": severity,
                        "passed": required if doc_type == "epc_contract" else None,
                    }
                ] if doc_type == "epc_contract" else [],
                "expected_obligations_min": 2 if doc_type in ("epc_contract", "service_agreement") else 1,
                "expected_risk_score_range": [40, 95],
            })
    return items[:25]


def main():
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    qa = {
        "version": "1.0.0",
        "pack_id": "iran-oil-gas",
        "description": "Golden Q&A benchmark for Iranian Oil & Gas domain pack",
        "items": generate_qa(),
    }
    analysis = {
        "version": "1.0.0",
        "pack_id": "iran-oil-gas",
        "description": "Golden contract analysis benchmark for Iranian Oil & Gas domain pack",
        "items": generate_analysis(),
    }

    (PACK_DIR / "qa-golden.json").write_text(
        json.dumps(qa, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (PACK_DIR / "analysis-golden.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Generated {len(qa['items'])} Q&A items and {len(analysis['items'])} analysis cases")


if __name__ == "__main__":
    main()
