"""
Bryant Luna-Ramos
6/16/26


"""
import argparse
import csv
import re
import sqlite3

DB_PATH = "diit_contracts.db"

'''
CSV layer
'''

DIIT_KEYWORDS = [
    "DIIT", "information technology", "instructional technology", "technology",
    "software", "hardware", "network", "server", "laptop", "desktop", "tablet",
    "chromebook", "wireless", "data center", "cabling", "IT services",
    "IT support", "IT consulting", "cloud", "digital", "computer", "device", "cyber",
    "telecommunications", "infrastructure", "system",
]

DIIT_EXCLUDE_PHRASES = [
    "family child care",
    "crisis management system",
    "system-wide", "systemwide", "system wide",
    "fire alarm", "fire suppression", "sprinkler", "standpipe",
    "security system",
    "hvac", "air condition", "boiler", "plumbing", "backflow", "fuel oil",
    "public address system", "gas leak detection", "de-watering",
    "kitchen exhaust", "water treatment", "direct digital control",
    "window shades",
    "legal process server",
    "vendor does not have order in system", "doc posted in city",
]

REGISTERED_EXPENSE_COLUMNS = [
    "prime_contract_id", "contract_includes_sub_vendors", "prime_vendor",
    "prime_vendor_mwbe_category", "prime_contract_purpose",
    "prime_contract_original_amount", "prime_contract_current_amount",
    "prime_vendor_spent_to_date", "prime_contract_start_date",
    "prime_contract_end_date", "prime_contract_registration_date",
    "prime_contracting_agency", "prime_oca_number", "prime_contract_version",
    "parent_contract_id", "prime_contract_type", "prime_contract_award_method",
    "prime_contract_expense_category", "prime_contract_industry",
    "prime_contract_pin", "prime_woman_owned_business",
    "prime_emerging_business", "sub_vendor", "sub_contract_reference_id",
    "sub_vendor_mwbe_category", "sub_contract_purpose", "sub_contract_status",
    "sub_contract_original_amount", "sub_contract_current_amount",
    "sub_vendor_paid_to_date", "sub_contract_start_date",
    "sub_contract_end_date", "sub_woman_owned_business",
    "sub_emerging_business", "document_code", "year", "contract_class",
]

PENDING_COLUMNS = [
    "agency", "prime_vendor", "contract_id", "purpose", "parent_contract_id",
    "original_amount", "current_amount", "original_modified", "oca_number",
    "version", "received_date", "pin", "contract_type", "award_method",
    "start_date", "end_date", "industry", "document_code",
    "prime_mwbe_category", "woman_owned_business", "emerging_business",
    "contract_class",
]

REGISTERED_HEADER_MAP = {
    "primecontractid": "prime_contract_id",
    "contractincludessubvendors": "contract_includes_sub_vendors",
    "primevendor": "prime_vendor",
    "primevendormwbecategory": "prime_vendor_mwbe_category",
    "primecontractpurpose": "prime_contract_purpose",
    "primecontractoriginalamount": "prime_contract_original_amount",
    "primecontractcurrentamount": "prime_contract_current_amount",
    "primevendorspendtodate": "prime_vendor_spent_to_date",
    "primecontractstartdate": "prime_contract_start_date",
    "primecontractenddate": "prime_contract_end_date",
    "primecontractregistrationdate": "prime_contract_registration_date",
    "primecontractingagency": "prime_contracting_agency",
    "primeocanumber": "prime_oca_number",
    "primecontractversion": "prime_contract_version",
    "parentcontractid": "parent_contract_id",
    "primecontracttype": "prime_contract_type",
    "primecontractawardmethod": "prime_contract_award_method",
    "primecontractexpensecategory": "prime_contract_expense_category",
    "primecontractindustry": "prime_contract_industry",
    "primecontractpin": "prime_contract_pin",
    "primewomanownedbusiness": "prime_woman_owned_business",
    "primeemergingbusiness": "prime_emerging_business",
    "subvendor": "sub_vendor",
    "subcontractreferenceid": "sub_contract_reference_id",
    "subvendormwbecategory": "sub_vendor_mwbe_category",
    "subcontractpurpose": "sub_contract_purpose",
    "subcontractstatus": "sub_contract_status",
    "subcontractoriginalamount": "sub_contract_original_amount",
    "subcontractcurrentamount": "sub_contract_current_amount",
    "subvendorpaidtodate": "sub_vendor_paid_to_date",
    "subcontractstartdate": "sub_contract_start_date",
    "subcontractenddate": "sub_contract_end_date",
    "subwomanownedbusiness": "sub_woman_owned_business",
    "subemergingbusiness": "sub_emerging_business",
    "documentcode": "document_code",
    "year": "year",
    "contractclass": "contract_class",
}

PENDING_HEADER_MAP = {
    "agency": "agency",
    "primevendor": "prime_vendor",
    "contractid": "contract_id",
    "purpose": "purpose",
    "parentcontractid": "parent_contract_id",
    "originalamount": "original_amount",
    "currentamount": "current_amount",
    "originalmodified": "original_modified",
    "ocanumber": "oca_number",
    "version": "version",
    "receiveddate": "received_date",
    "pin": "pin",
    "contracttype": "contract_type",
    "awardmethod": "award_method",
    "startdate": "start_date",
    "enddate": "end_date",
    "industry": "industry",
    "documentcode": "document_code",
    "primemwbecategory": "prime_mwbe_category",
    "womanownedbusiness": "woman_owned_business",
    "emergingbusiness": "emerging_business",
    "contractclass": "contract_class",
}


'''
CSV layer
'''

def normalize_header(h: str) -> str:
    #Lowercase and strip all non-alphanumeric chars
    return re.sub(r"[^a-z0-9]", "", h.lower())



'''
Database layer
'''

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn




'''
Main
'''

if __name__ = "__main__":
    parser = argparse.Argumentparser(
        description="Loading CheckBookNYC Data Feeds CSV export into SQLite and run DIIT contract analysis."
    )
    parser.add_argument ("--registered", help="Path to registered status data feeds CSV export.")
    parser.add_argument ("--pending", help="Path to pending status data feeds CSV export.")
    args = parser.parse_args()

    if not args.registered and not args.pending"
    parser.error("Provide at least one of --registered or --pending CSV file path.")