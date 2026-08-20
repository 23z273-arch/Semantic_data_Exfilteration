"""
data/synthetic_documents.py — Four synthetic protected vault documents.

These are entirely fictional records designed to test the detection pipeline.
All names, numbers, and details are fabricated.
"""
from typing import Any, Dict, List


VAULT_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "name": "Executive_Compensation_2026_Q2.txt",
        "category": "HR_RECORD",
        "classification": "TOP_SECRET",
        "lineage_tag": "VAULT-HR-EXEC-2026-Q2",
        "department": "Human Resources",
        "data_owner": "CHRO — Diana Westfall",
        "content": """
STRICTLY CONFIDENTIAL — EXECUTIVE COMPENSATION SCHEDULE Q2 2026
Prepared by: Meridian Global HR / Authorized Recipients Only

NAME: Sarah Jenkins
TITLE: Senior Vice President, Clinical Development
EMPLOYEE ID: EMP-00492
BASE SALARY: $240,000 annually
PERFORMANCE BONUS TARGET: 15% of base ($36,000)
RESTRICTED STOCK UNITS (RSUs): 4,000 units, vesting 25% per year, cliff at 12 months
SIGN-ON BONUS: $25,000 (paid at 6-month mark)
HEALTH PLAN: Executive Platinum, fully employer-funded
START DATE: March 1, 2026
REPORTING TO: Dr. Marcus Chen, Chief Medical Officer

NAME: Robert Tanaka
TITLE: Chief Financial Officer
EMPLOYEE ID: EMP-00101
BASE SALARY: $385,000 annually
PERFORMANCE BONUS TARGET: 30% of base ($115,500)
RESTRICTED STOCK UNITS (RSUs): 12,000 units, vesting over 4 years
LONG-TERM INCENTIVE PLAN (LTIP): $200,000 target, paid at 3-year mark subject to TSR goals
REPORTING TO: Board Compensation Committee

NAME: Priya Mehta
TITLE: VP Engineering & AI Systems
EMPLOYEE ID: EMP-00278
BASE SALARY: $295,000 annually
PERFORMANCE BONUS TARGET: 20% of base ($59,000)
RESTRICTED STOCK UNITS (RSUs): 6,500 units
EQUITY REFRESH GRANT: 2,000 units per year for top-quartile performance rating
REPORTING TO: CTO — Alan Forsythe

DOCUMENT CLASSIFICATION: TOP SECRET
ACCESS: HR Leadership, Board Compensation Committee, Legal only
EXPIRY: Document is valid for fiscal year 2026 only.
""",
        "meta_data": {"fiscal_year": 2026, "document_version": "v1.2"},
    },
    {
        "name": "Clinical_Trial_TX9082_PatientManifest_2025.txt",
        "category": "MEDICAL",
        "classification": "TOP_SECRET",
        "lineage_tag": "VAULT-MED-TRIAL-TX9082",
        "department": "Clinical Research",
        "data_owner": "Dr. Helen Vasquez — Principal Investigator",
        "content": """
CLINICAL TRIAL PATIENT MANIFEST — PROTOCOL TX-9082
SPONSOR: Meridian Biosciences Inc.
IND NUMBER: FDA-IND-2024-18821
TRIAL PHASE: Phase II — Open-Label Extension
PRINCIPAL INVESTIGATOR: Dr. Helen Vasquez, MD PhD

PATIENT RECORD — STRICTLY CONFIDENTIAL

Patient ID: PT-0042
Patient Name: John Doe (PSEUDONYMISED)
Date of Birth: April 12, 1981 (Age 44)
Gender: Male
Primary Diagnosis: Stage 2 Neuroendocrine Tumor, Pancreatic Origin
Genetic Mutation Confirmed: MEN1 positive (multiple endocrine neoplasia type 1)
Concurrent Conditions: Mild hypercalcemia, managed with bisphosphonates

Trial Enrollment Date: January 15, 2024
Trial Arm: Arm B — Investigational Compound TX-9082
Dosage Regimen: 45mg oral tablet, weekly administration, fasted state
Dose Escalation Flag: No escalation — stable on 45mg since enrollment
Prior Treatments: Somatostatin analogue octreotide 20mg monthly (discontinued March 2023)

Adverse Events Logged:
  - Week 4: Grade 1 nausea, resolved without intervention
  - Week 12: Grade 2 fatigue, dose held for 1 week, resumed
  - Week 28: Grade 1 peripheral edema, managed with dietary sodium restriction

Latest Assessment (Week 52): Stable disease. No tumor progression per RECIST 1.1 criteria.
Next Assessment: Week 78 (scheduled October 2026)

Emergency Contact: Jane Doe (spouse), +1-555-0194-2281 [REDACTED FROM EXTERNAL COPIES]
Site: Meridian Medical Center, Building C, Suite 410

DATA CLASSIFICATION: TOP SECRET — HIPAA PROTECTED
Authorized Access: Trial Investigator, Clinical Data Manager, IRB only
""",
        "meta_data": {"trial_id": "TX-9082", "phase": 2, "regulatory_ref": "FDA-IND-2024-18821"},
    },
    {
        "name": "Nexus_Corp_Acquisition_Strategy_Memo_2026.txt",
        "category": "FINANCIAL",
        "classification": "TOP_SECRET",
        "lineage_tag": "VAULT-FIN-MA-NEXUS-2026",
        "department": "Corporate Strategy",
        "data_owner": "CEO — Jonathan Park",
        "content": """
STRICTLY CONFIDENTIAL — MATERIAL NON-PUBLIC INFORMATION
M&A STRATEGIC ACQUISITION MEMO
DATE: June 3, 2026
FROM: Corporate Strategy & M&A Advisory (Goldman Sachs)
TO: Board of Directors, Meridian Global Inc.
RE: Proposed Acquisition of Nexus Corp (NASDAQ: NXSC)

EXECUTIVE SUMMARY
Meridian Global has entered advanced-stage negotiations to acquire Nexus Corp,
a mid-market AI infrastructure company headquartered in Austin, Texas.

TRANSACTION DETAILS
Target Company: Nexus Corp
Target Ticker: NXSC (NASDAQ)
Proposed Enterprise Value: $4,200,000,000 (four billion, two hundred million USD)
EV/EBITDA Multiple: 8.3x (based on projected 2026 EBITDA of $506M)
Cash/Stock Split: 60% cash ($2.52B), 40% Meridian stock ($1.68B)
Regulatory Filing Target: Q3 2026 (FTC pre-merger notification)
Expected Deal Close: Q1 2027, subject to shareholder and regulatory approval
Break-Up Fee: $126 million (3% of deal value)

STRATEGIC RATIONALE
- Nexus Corp's proprietary NexusGuard AI security platform complements Meridian's
  enterprise governance stack and adds $800M in ARR immediately on close.
- Combined entity will hold 34% market share in enterprise AI compliance tooling.
- Anticipated synergies of $150M annually within 24 months post-close.

FINANCING
Meridian has secured a $2.0B bridge loan commitment from JP Morgan and Citibank
at SOFR + 175 bps, to be refinanced with a bond issuance within 90 days of close.

CONFIDENTIALITY NOTICE
This document contains material non-public information. Disclosure to any
person outside the authorized distribution list constitutes a securities law
violation. Distribution restricted to: Board members, Legal, C-suite, Deal Advisors.
""",
        "meta_data": {"deal_code": "PROJECT-NOVA", "last_updated": "2026-06-03"},
    },
    {
        "name": "Production_Network_Infrastructure_Credentials_2026.txt",
        "category": "INFRASTRUCTURE",
        "classification": "RESTRICTED",
        "lineage_tag": "VAULT-IT-INFRA-PROD-NET",
        "department": "IT Security",
        "data_owner": "CISO — Marcus Webb",
        "content": """
RESTRICTED — IT SECURITY INTERNAL ONLY
PRODUCTION NETWORK INFRASTRUCTURE REFERENCE
Last Updated: July 2026
Maintained by: Network Security Engineering Team

PRODUCTION VPC CONFIGURATION
Environment: AWS us-east-1 (Primary), eu-west-1 (DR)
Primary VPC ID: vpc-0a7f3c924e18b1f2d
CIDR Block: 10.18.0.0/16

SUBNET ALLOCATION
Public Subnets (ALB / NAT):
  10.18.1.0/24 — us-east-1a
  10.18.2.0/24 — us-east-1b
Private Application Subnets:
  10.18.10.0/24 — us-east-1a (app tier)
  10.18.11.0/24 — us-east-1b (app tier)
Private Database Subnets:
  10.18.20.0/24 — us-east-1a (DB tier)
  10.18.21.0/24 — us-east-1b (DB tier)

JUMP HOST
Hostname: bastion.internal.meridian.corp
IP: 10.18.1.50
Access: Key-based SSH only; RSA-4096; MFA required via Okta
Jump User: bastion-svc (no password login)

ADMIN CREDENTIALS (ROTATE EVERY 90 DAYS — NEXT ROTATION: Oct 1, 2026)
Database Admin: VaultAdmin@2026! (temporary; stored in AWS Secrets Manager arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/db/admin)
RDS Endpoint: prod-db.cluster-xyz987abc.us-east-1.rds.amazonaws.com
Redis Endpoint: prod-cache.xyz987abc.0001.use1.cache.amazonaws.com:6379

VPN ENDPOINT
WireGuard VPN: vpn.meridian.corp:51820
PSK Location: AWS Secrets Manager (arn:aws:secretsmanager:us-east-1:123456789012:secret:vpn/psk)

SECURITY NOTICE: This document must not be transmitted outside the internal
Meridian network. Violation is grounds for immediate termination and legal action.
""",
        "meta_data": {"environment": "production", "last_audit": "2026-07-01"},
    },
]
