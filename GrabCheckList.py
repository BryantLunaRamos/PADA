"""
Bryant Luna-Ramos
6/16/26
"""
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time

API_URL = "https://www.checkbooknyc.com/api"
AGENCY_CODE = "040"     # NYC DOE's agency code
BUDGET_CODE = "7719"    # DIIT budget code
PAGE_SIZE   = 1000      # records to pull per call, can handle max of 20k

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
