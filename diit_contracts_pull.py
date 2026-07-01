"""
Bryant Luna-Ramos
6/16/26

How to run:
python diit_contracts_pull.py --registered registered.csv --pending pending.csv
"""

import argparse
import csv
import re
import openpyxl
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

PRINCIPALS_HEADER_MAP = {
    "vendorname": "vendor_name",
    "principalname": "principal_name",
    "currenttitle": "current_title",
    "principalownershiptype": "ownership_tye",
}

RELATED_ENTITIES_HEADER_MAP = {
    "vendorname": "vendor_name",
    "relatedentityname": "related_entity_name",
    "addressline1": "address_line_1",
    "addressline2": "address_line_2",
    "city": "city",
    "state": "state",
    "zipcode": "zip_code",
    "country": "country",
    "telephone": "telephone",
    "relationshiptovendor": "relationship_to_vendor",
}

OTHER_NAMES_HEADER_MAP = {
    "vendorname": "vendor_name",
    "othernametype": "other_name_type",
    "othername": "other_name",
    "fromdate": "from_date",
    "todate": "to_date",
}

ENTITY_SUMMARY_HEADER_MAP = {
    "vendorname": "vendor_name",
    "relatedentityname": "related_entity_name",
    "addressline1": "address_line_1",
    "addressline2": "address_line_2",
    "city": "city",
    "state": "state",
    "zipcode": "zip_code",
    "country": "country",
    "telephone": "telephone",
    "stockexchangesymbol": "stock_exchange_symbol",
    "forprofit": "for_profit",
    "dunsnumber": "duns_number",
    "grossrevenue": "gross_revenue",
}

TABLE_CONFIGS = {
    "contracts_registered": {
        "columns": REGISTERED_EXPENSE_COLUMNS,
        "amount_cols": {c for c in REGISTERED_EXPENSE_COLUMNS
                        if "amount" in c or "paid_to_date" in c or "spent_to_date" in c},
        "header_map": REGISTERED_EXPENSE_COLUMNS,
        "extra_columns": ["is_diit INTEGER DEFAULT 0"],
    },
    "pending_contracts": {
        "columns": PENDING_COLUMNS,
        "amount_cols": {c for c in PENDING_COLUMNS},
        "header_map": PENDING_COLUMNS,
        "extra_columns": {"is_diit INTEGERE DEFAULT 0"},
    },
    "passport_principals": {
        "columns": ["vendor_name", "principal_name", "current_title", "ownership_type"],
        "amount_cols": set(),
        "header_map": PRINCIPALS_HEADER_MAP,
        "extra_columns": [],
    },
    "passport_related_entities": {
        "columns": ["vendor_name", "related_entity_name", "address_line_1", "address_line_2", 
                                  "city", "state", "zip_code", "country", "telephone", "relationship_to_vendor"],
        "amount_cols": set(),
        "header_map": RELATED_ENTITIES_HEADER_MAP,
        "extra_columns": [],
    },
    "passport_other_names": {
        "columns": ["vendor_name", "other_name_type", "other_name", "from_date", "to_date"],
        "amount_cols": set(),
        "header_map": OTHER_NAMES_HEADER_MAP,
        "extra_columns": [],
    },
    "passport_entity_summary": {
        "colums": ["vendor_name", "related_entity_name", "address_line_1", "address_line_2", "city", "state",
                    "zip_code", "country", "telephone", "stock_exchange_symbol", "for_profit", "duns_number"
                    "gross_revenue"],
        "amount_col": set(),
        "header_map": ENTITY_SUMMARY_HEADER_MAP,
        "extra_columns": [],
    },
}

'''
CSV functions
'''


def normalize_header(h: str) -> str:
    #Lowercase and strip all non-alphanumeric chars
    return re.sub(r"[^a-z0-9]", "", h.lower())

def load_csv_rows(path: str, header_map: dict, label: str) -> list:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        raw_to_internal = {}
        unmapped = []
        for raw_header in fieldnames:
            norm = normalize_header(raw_header)
            if norm in header_map:
                raw_to_internal[raw_header] = header_map[norm]
            else:
                unmapped.append(raw_header)

        found_norms = {normalize_header(h) for h in fieldnames}
        missing = [internal for norm, internal in header_map.items() if norm not in found_norms]

        if unmapped:
            print(f"[{label}] NOTE: {len(unmapped)} CSV column(s) present but not used "
                  f"downstream (fine to ignore): {unmapped}")
        if missing:
            print(f"[{label}] WARNING: expected column(s) NOT FOUND in this CSV. "
                  f"those fields will be blank: {missing}")

        for raw_row in reader:
            row = {internal: (raw_row.get(raw_header) or "").strip()
                   for raw_header, internal in raw_to_internal.items()}
            rows.append(row)

    print(f"[{label}] Loaded {len(rows)} rows from {path}")
    return rows

def load_excel_rows(path: str, header_map: dict, label: str, max_search_rows: int = 20) -> list:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    header_row_idx = None
    raw_to_internal = {}
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=max_search_rows, values_only=True)):
        norm_cells = {normalize_header(str(v)): v for v in row if v}
        matches = {norm: header_map[norm] for norm in norm_cells if norm in header_map}
        if len(matches) >= max(2, len(header_map) // 2):
            header_row_idx = i + 1
            raw_to_internal = {norm_cells[norm]: internal for norm, internal in matches.items()}
            break
    
    if header_row_idx is None:
        print(f"[{label}] WARNING: could not locate a header row in the first "
                f"{max_search_rows} rows — check the file format.")
        wb.close()
        return []
    
    col_index = {}
    for row in ws.iter_rows(min_row=header_row_idx, max_row=header_row_idx, values_only=True):
        for j, val in enumerate(row):
            if val in raw_to_internal:
                col_index[j] = raw_to_internal[val]

    missing = [internal for internal in header_map.values() if internal not in col_index.values()]
    if missing:
        print(f"[{label}] WARNING: expected column(s) NOT FOUND — those fields will be blank: {missing}")

    rows = []
    for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
        if row is None or all(v is None for v in row):
            continue
        record = {internal: str(row[j]).strip() if row[j] is not None else ""
                  for j, internal in col_index.items()}
        rows.append(record)

    wb.close()
    print(f"[{label}] Loaded {len(rows)} rows from {path}")
    return rows

'''
Database layer
'''

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    DROP TABLE IF EXISTS contracts_registered;
    DROP TABLE IF EXISTS contracts_pending;
    DROP TABLE IF EXISTS contracts_unified;
    DROP TABLE IF EXISTS vendor_summary;
    
    CREATE TABLE contracts_registered (
        prime_contract_id               TEXT,
        contract_includes_sub_vendors   TEXT,
        prime_vendor                    TEXT,
        prime_vendor_mwbe_category      TEXT,
        prime_contract_purpose          TEXT,
        prime_contract_original_amount  REAL,
        prime_contract_current_amount   REAL,
        prime_vendor_spent_to_date      REAL,
        prime_contract_start_date       TEXT,
        prime_contract_end_date         TEXT,
        prime_contract_registration_date TEXT,
        prime_contracting_agency        TEXT,
        prime_oca_number                TEXT,
        prime_contract_version          TEXT,
        parent_contract_id              TEXT,
        prime_contract_type             TEXT,
        prime_contract_award_method     TEXT,
        prime_contract_expense_category TEXT,
        prime_contract_industry         TEXT,
        prime_contract_pin              TEXT,
        prime_woman_owned_business      TEXT,
        prime_emerging_business         TEXT,
        sub_vendor                      TEXT,
        sub_contract_reference_id       TEXT,
        sub_vendor_mwbe_category        TEXT,
        sub_contract_purpose            TEXT,
        sub_contract_status             TEXT,
        sub_contract_original_amount    TEXT,
        sub_contract_current_amount     TEXT,
        sub_vendor_paid_to_date         TEXT,
        sub_contract_start_date         TEXT,
        sub_contract_end_date           TEXT,
        sub_woman_owned_business        TEXT,
        sub_emerging_business           TEXT,
        document_code                   TEXT,
        year                            TEXT,
        contract_class                  TEXT,
        is_diit                         INTEGER DEFAULT 0            
    );

    CREATE TABLE contracts_pending (
        agency                          TEXT,
        prime_vendor                    TEXT,
        contract_id                     TEXT,
        purpose                         TEXT,
        parent_contract_id              TEXT,
        original_amount                 REAL,
        current_amount                  REAL,
        original_modified               TEXT,
        oca_number                      TEXT,
        version                         TEXT,
        received_date                   TEXT,
        pin                             TEXT,
        contract_type                   TEXT,
        award_method                    TEXT,
        start_date                      TEXT,
        end_date                        TEXT,
        industry                        TEXT,
        document_code                   TEXT,
        prime_mwbe_category             TEXT,
        woman_owned_business            TEXT,
        emerging_business               TEXT,
        contract_class                  TEXT,
        is_diit                         INTEGER DEFAULT 0
    );
                      
    CREATE TABLE contracts_unified (
        contract_id                     TEXT,
        vendor_name                     TEXT,
        vendor_role                     TEXT,   
        mwbe_category                   TEXT,
        purpose                         TEXT,
        current_amount                  REAL,
        original_amount                 REAL,
        award_method                    TEXT,
        contract_type                   TEXT,
        start_date                      TEXT,
        end_date                        TEXT,
        status                          TEXT,   
        is_diit                         INTEGER DEFAULT 0
    );
                      
    CREATE TABLE vendor_summary (
        vendor_name     TEXT PRIMARY KEY,
        num_contracts   INTEGER,
        total_amount    REAL,
        mwbe_category   TEXT,
        pct_of_total    REAL
    );
    """)
    conn.commit()


def parse_amount(val: str) -> float:
    if not val:
        return 0.0
    val = val.replace(",", "").replace("$", "").strip()
    if val in ("", "-"):
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0

def insert_registered(conn: sqlite3.Connection, rows: list) -> None:
    if not rows:
        return
    cols = REGISTERED_EXPENSE_COLUMNS
    amount_cols = {c for c in cols if "amount" in c or "paid_to_date" in c or "spent_to_date" in c}
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO contracts_registered ({', '.join(cols)}) VALUES ({placeholders})"

    values = []
    for r in rows:
        row_vals = []
        for c in cols:
            v = r.get(c, "")
            row_vals.append(parse_amount(v) if c in amount_cols else v)
        values.append(tuple(row_vals))

    conn.executemany(sql, values)
    conn.commit()


def insert_pending(conn: sqlite3.Connection, rows: list) -> None:
    if not rows:
        return
    cols = PENDING_COLUMNS
    amount_cols = {c for c in cols if "amount" in c}
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO contracts_pending ({', '.join(cols)}) VALUES ({placeholders})"

    values = []
    for r in rows:
        row_vals = []
        for c in cols:
            v = r.get(c, "")
            row_vals.append(parse_amount(v) if c in amount_cols else v)
        values.append(tuple(row_vals))

    conn.executemany(sql, values)
    conn.commit()


def flag_diit_sql(conn: sqlite3.Connection) -> None:
    like_clauses_prime = " OR ".join(f"prime_contract_purpose LIKE '%{kw}%'" for kw in DIIT_KEYWORDS)
    like_clauses_sub   = " OR ".join(f"sub_contract_purpose LIKE '%{kw}%'" for kw in DIIT_KEYWORDS)
    conn.execute(f"""
        UPDATE contracts_registered
        SET is_diit = 1
        WHERE {like_clauses_prime} OR {like_clauses_sub}
    """)

    like_clauses_pending = " OR ".join(f"purpose LIKE '%{kw}%'" for kw in DIIT_KEYWORDS)
    conn.execute(f"""
        UPDATE contracts_pending
        SET is_diit = 1
        WHERE {like_clauses_pending}
    """)

    exclude_clauses_prime = " OR ".join(f"prime_contract_purpose LIKE '%{p}%'" for p in DIIT_EXCLUDE_PHRASES)
    exclude_clauses_sub   = " OR ".join(f"sub_contract_purpose LIKE '%{p}%'" for p in DIIT_EXCLUDE_PHRASES)
    conn.execute(f"""
        UPDATE contracts_registered
        SET is_diit = 0
        WHERE is_diit = 1 AND ({exclude_clauses_prime} OR {exclude_clauses_sub})
    """)

    exclude_clauses_pending = " OR ".join(f"purpose LIKE '%{p}%'" for p in DIIT_EXCLUDE_PHRASES)
    conn.execute(f"""
        UPDATE contracts_pending
        SET is_diit = 0
        WHERE is_diit = 1 AND ({exclude_clauses_pending})
    """)
    conn.commit()


def build_unified_table(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM contracts_unified")

    conn.execute("""
        INSERT INTO contracts_unified
            (contract_id, vendor_name, vendor_role, mwbe_category, purpose,
            current_amount, original_amount, award_method, contract_type,
            start_date, end_date, status, is_diit)
        SELECT
            prime_contract_id, prime_vendor, 'prime', prime_vendor_mwbe_category,
            prime_contract_purpose, prime_contract_current_amount,
            prime_contract_original_amount, prime_contract_award_method,
            prime_contract_type, prime_contract_start_date, prime_contract_end_date,
            'registered', is_diit
        FROM contracts_registered
        WHERE prime_vendor IS NOT NULL AND prime_vendor != ''
    """)

    conn.execute("""
        INSERT INTO contracts_unified
            (contract_id, vendor_name, vendor_role, mwbe_category, purpose,
            current_amount, original_amount, award_method, contract_type,
            start_date, end_date, status, is_diit)
        SELECT
            contract_id, prime_vendor, 'prime', prime_mwbe_category, purpose,
            current_amount, original_amount, award_method, contract_type,
            start_date, end_date, 'pending', is_diit
        FROM contracts_pending
        WHERE prime_vendor IS NOT NULL AND prime_vendor != ''
    """)
    conn.commit()


def build_vendor_summary_sql(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM vendor_summary")
    conn.execute("""
        INSERT INTO vendor_summary (vendor_name, num_contracts, total_amount, mwbe_category, pct_of_total)
        SELECT
            vendor_name,
            COUNT(DISTINCT contract_id)                AS num_contracts,
            SUM(current_amount)                        AS total_amount,
            (SELECT mwbe_category FROM contracts_unified u2
            WHERE u2.vendor_name = u1.vendor_name AND u2.is_diit = 1
            GROUP BY mwbe_category ORDER BY COUNT(*) DESC LIMIT 1) AS mwbe_category,
            0.0
        FROM contracts_unified u1
        WHERE is_diit = 1
        GROUP BY vendor_name
    """)
    conn.commit()

    total = conn.execute("SELECT SUM(total_amount) FROM vendor_summary").fetchone()[0] or 0
    if total > 0:
        conn.execute("UPDATE vendor_summary SET pct_of_total = ROUND(total_amount * 100.0 / ?, 2)", (total,))
        conn.commit()

def compute_hhi(conn: sqlite3.Connection) -> float:
    """HHI = sum of squared market shares (0-100 scale)."""
    rows = conn.execute("SELECT pct_of_total FROM vendor_summary").fetchall()
    return sum(r[0] ** 2 for r in rows if r[0] is not None)

'''
Main
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Loading CheckBookNYC Data Feeds CSV export into SQLite and run DIIT contract analysis."
    )
    parser.add_argument ("--registered", help="Path to registered status data feeds CSV export.")
    parser.add_argument ("--pending", help="Path to pending status data feeds CSV export.")
    args = parser.parse_args()

    if not args.registered and not args.pending:
        parser.error("Provide at least one of --registered or --pending CSV file path.")

    conn = get_connection()
    create_schema(conn)

    #Load CSV exports
    registered_rows = load_registered_csv(args.registered) if args.registered else []
    pending_rows    = load_pending_csv(args.pending) if args.pending else []

    if not registered_rows and not pending_rows:
        print("\nNo rows loaded from either CSV. Check the file path(s) and that the "
              "export actually has data rows (not just headers).")
        conn.close()
        raise SystemExit(1)

    #Load into SQLite
    insert_registered(conn, registered_rows)
    insert_pending(conn, pending_rows)
    print(f"\nLoaded {len(registered_rows)} registered rows and {len(pending_rows)} pending rows into {DB_PATH}")

    #Flag DIIT contracts
    flag_diit_sql(conn)

    #Union registered and pending into one normalized table
    build_unified_table(conn)

    diit_count = conn.execute("SELECT COUNT(*) FROM contracts_unified WHERE is_diit = 1").fetchone()[0]
    print(f"Flagged {diit_count} unified rows as likely DIIT/tech contracts.")

    #Vendor summary and execute HHI
    build_vendor_summary_sql(conn)
    hhi = compute_hhi(conn)

    print(f"\nHHI (DIIT-flagged vendors, all roles): {hhi:.1f}")
    if hhi < 1500:
        interp = "Unconcentrated"
    elif hhi < 2500:
        interp = "Moderately concentrated"
    else:
        interp = "Highly concentrated"
    print(f"Interpretation per DOJ/FTC guideline bands: {interp}")

    print("\n--- Top 10 vendors by total DIIT contract value ---")
    top10 = conn.execute("""
        SELECT vendor_name, num_contracts, total_amount, mwbe_category, pct_of_total
        FROM vendor_summary ORDER BY total_amount DESC LIMIT 10
    """).fetchall()

    for row in top10:
        print(f"  {row[0]:<40} contracts={row[1]:<4} ${row[2]:,.2f}  {row[3]:<15} {row[4]}%")

    print("\n--- M/WBE category breakdown (DIIT-flagged contracts) ---")
    mwbe_counts = conn.execute("""
        SELECT mwbe_category, COUNT(*) FROM contracts_unified
        WHERE is_diit = 1 GROUP BY mwbe_category ORDER BY COUNT(*) DESC
    """).fetchall()
    for cat, cnt in mwbe_counts:
        print(f"  {cat or '(blank)':<20} {cnt}")

    conn.close()
    print(f"\nDone. Full database saved at: {DB_PATH}")
    print("Open it with: sqlite3 diit_contracts.db ")