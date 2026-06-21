'''
Bryant Luna-Ramos
6/18/2026

A python test script to test the functionality of the Checkbook api. Suspected
that the API was non-functional in a production setting, this was meant to
provide concrete proof.
'''

import requests

API_URL = "https://www.checkbooknyc.com/api"

VALID_REQUEST = """<?xml version="1.0" encoding="UTF-8"?>
<request>
    <type_of_data>Contracts</type_of_data>
    <records_from>1</records_from>
    <max_records>5</max_records>
    <search_criteria>
        <criteria><name>status</name><type>value</type><value>registered</value></criteria>
        <criteria><name>category</name><type>value</type><value>expense</value></criteria>
        <criteria><name>agency_code</name><type>value</type><value>18</value></criteria>
    </search_criteria>
    <response_columns>
        <column>prime_contract_id</column>
        <column>prime_vendor</column>
        <column>prime_contract_purpose</column>
        <column>prime_contract_current_amount</column>
    </response_columns>
</request>"""

# Leaving out the required type_of_data elem to malform the request
MALFORMED_REQUEST = """<?xml version="1.0" encoding="UTF-8"?>
<request>
    <records_from>1</records_from>
    <max_records>5</max_records>
</request>"""

HEADERS = {
    "Content-Type": "application/xml",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}


def run_test(label: str, payload: str) -> None:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
    try:
        resp = requests.post(API_URL, data=payload.encode("utf-8"),
                              headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        print(f"REQUEST FAILED (connection-level): {e}")
        return

    print(f"HTTP status:     {resp.status_code}")
    print(f"Content-Length:  {resp.headers.get('content-length', '(not set)')}")
    print(f"x-cdn / WAF hdr: {resp.headers.get('x-cdn', '(not present)')}")
    print(f"Actual body len: {len(resp.content)} bytes")
    print(f"Body (first 500 chars):\n{resp.text[:500] or '(EMPTY)'}")


if __name__ == "__main__":
    run_test("TEST 1: Valid request of 5 DOE registered contracts", VALID_REQUEST)
    run_test("TEST 2: Malformed request with missing type_of_data (expect documented error XML)", MALFORMED_REQUEST)

    print(f"\n{'=' * 60}\n RESULTS \n{'=' * 60}")
    print("If Test 2's body is not empty and contains code 1000 / "
          "\"Required parameter 'type_of_data' is missing\" means the API is "
          "alive an healthy\n")
    print("If Test 2's body is empty despite a 200 status, conclusive dead"
          "(server side WAF/Imperva voiding all requests, not a "
          "parameter or agency_code issue)\n")