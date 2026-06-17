"""
Bryant Luna-Ramos
6/16/26
"""
import requests
import sqlite3
import xml.etree.ElementTree as ET
import time

API_URL     = "https://www.checkbooknyc.com/api"
DB_PATH     = "diit_contracts.db"
AGENCY_CODE = "18"     # NYC DOE's agency code
PAGE_SIZE   = 1000      # records to pull per call, can handle max of 20k


# Keywords used to flag likely DIIT / tech contracts from the purpose text,
# since there's no server-side budget-code filter for Citywide agencies.
DIIT_KEYWORDS = [
    "DIIT", "information technology", "instructional technology", "technology",
    "software", "hardware", "network", "server", "laptop", "desktop", "tablet",
    "chromebook", "wireless", "data center", "cabling", "IT services",
    "computer", "device", "cyber", "telecommunications", "infrastructure", "system",
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
    "prime_contract_pin", "prime_woman_owned_business", "prime_emerging_business",
    "sub_vendor", "sub_contract_reference_id", "sub_vendor_mwbe_category",
    "sub_contract_purpose", "sub_contract_status", "sub_contract_original_amount",
    "sub_contract_current_amount", "sub_vendor_paid_to_date",
    "sub_contract_start_date", "sub_contract_end_date",
    "sub_woman_owned_business", "sub_emerging_business",
    "document_code", "year", "contract_class",
]

PENDING_COLUMNS = [
    "agency", "prime_vendor", "contract_id", "purpose", "parent_contract_id",
    "original_amount", "current_amount", "original_modified", "oca_number",
    "version", "received_date", "pin", "contract_type", "award_method",
    "start_date", "end_date", "industry", "document_code",
    "prime_mwbe_category", "woman_owned_business", "emerging_business",
    "contract_class",
]
 



def fetch_diit_contracts(records_from: int, max_records: int) -> str:
    xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
    <request>
        <type_of_data>Contracts</type_of_data>
        <records_from>{records_from}</records_from>
        <max_records>{max_records}</max_records>
        <search_criteria>
            <criteria>
                <name>agency_code</name>
                <type>value</type>
                <value>{AGENCY_CODE}</value>
            </criteria>
            <criteria>
                <name>budget_name</name>
                <type>value</type>
                <value>{BUDGET_CODE}</value>
            </criteria>
        </search_criteria>
        <response_columns>
            <column>contract_id</column>
            <column>vendor_name</column>
            <column>current_amount</column>
        </response_columns>
        
