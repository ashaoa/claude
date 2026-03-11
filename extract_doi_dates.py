#!/usr/bin/env python3
"""Extract dates embedded in DOI strings using regex patterns."""

import re
import csv

DOIS_RAW = "http://dx.doi.org/10.1002/cpz1.70063http://dx.doi.org/10.1002/eahr.500227http://dx.doi.org/10.1002/pdi.2520http://dx.doi.org/10.1007/978-1-0716-4168-2_18http://dx.doi.org/10.1007/978-1-0716-4168-2_22http://dx.doi.org/10.1007/978-1-0716-4176-7_14http://dx.doi.org/10.1007/s10461-024-04553-2http://dx.doi.org/10.1007/s11019-024-10237-4http://dx.doi.org/10.1007/s13164-024-00760-xhttp://dx.doi.org/10.1007/s40592-024-00214-1http://dx.doi.org/10.1007/s40592-024-00223-0http://dx.doi.org/10.1007/s40592-024-00224-zhttp://dx.doi.org/10.1016/bs.pbr.2024.12.001http://dx.doi.org/10.1016/j.arrct.2024.100411http://dx.doi.org/10.1016/j.cobeha.2024.101458http://dx.doi.org/10.1016/j.cub.2024.11.004http://dx.doi.org/10.1016/j.esg.2024.100229http://dx.doi.org/10.1016/j.hrcr.2024.11.002http://dx.doi.org/10.1016/j.ijidoh.2024.100049http://dx.doi.org/10.1016/j.ijms.2024.117386http://dx.doi.org/10.1016/j.jddst.2024.106494http://dx.doi.org/10.1016/j.landusepol.2024.107410http://dx.doi.org/10.1016/j.nsa.2024.105407http://dx.doi.org/10.1016/s0140-6736(24)01980-9http://dx.doi.org/10.1016/s0140-6736(24)01997-4http://dx.doi.org/10.1016/s0140-6736(24)02011-7http://dx.doi.org/10.1021/acs.jctc.4c00579http://dx.doi.org/10.1021/acs.jpclett.4c02731http://dx.doi.org/10.1021/acsami.4c04117http://dx.doi.org/10.1021/acschembio.4c00548http://dx.doi.org/10.1021/acsinfecdis.4c00659http://dx.doi.org/10.1021/acssynbio.4c00453http://dx.doi.org/10.1021/jacs.4c11229http://dx.doi.org/10.1037/sah0000594http://dx.doi.org/10.1037/xap0000522http://dx.doi.org/10.1037/xge0001665http://dx.doi.org/10.1037/xge0001706http://dx.doi.org/10.1038/s41593-024-01722-3http://dx.doi.org/10.1039/d4qo02126fhttp://dx.doi.org/10.1039/d4sm01059khttp://dx.doi.org/10.1056/aip2401088http://dx.doi.org/10.1056/nejmoa2400007http://dx.doi.org/10.1057/s41292-024-00344-zhttp://dx.doi.org/10.1080/03057070.2024.2508570http://dx.doi.org/10.1080/03670244.2024.2426104http://dx.doi.org/10.1080/15265161.2024.2416117http://dx.doi.org/10.1080/15265161.2024.2416133http://dx.doi.org/10.1083/jcb.202410147http://dx.doi.org/10.1083/jcb.202412011http://dx.doi.org/10.1089/ast.2024.0016http://dx.doi.org/10.1089/ham.2024.0077http://dx.doi.org/10.1089/zeb.2024.0170http://dx.doi.org/10.1093/ecco-jcc/jjae188http://dx.doi.org/10.1093/ehjci/jeae297http://dx.doi.org/10.1093/eurpub/ckae195http://dx.doi.org/10.1093/heapro/daae168http://dx.doi.org/10.1093/heapro/daae182http://dx.doi.org/10.1093/heapro/daae183http://dx.doi.org/10.1093/jhmas/jrae041http://dx.doi.org/10.1093/jhmas/jrae042http://dx.doi.org/10.1093/jhmas/jrae044http://dx.doi.org/10.1097/01.aoa.0001080156.34953.cehttp://dx.doi.org/10.1097/rct.0000000000001688http://dx.doi.org/10.1109/tpami.2024.3522305http://dx.doi.org/10.1109/trpms.2024.3496779http://dx.doi.org/10.1111/camh.12753http://dx.doi.org/10.1111/jcpp.14064http://dx.doi.org/10.1111/jcpp.14070http://dx.doi.org/10.1111/jcpp.14071http://dx.doi.org/10.1111/jcpp.14078http://dx.doi.org/10.1111/jcpp.14080http://dx.doi.org/10.1111/jcpp.14095http://dx.doi.org/10.1111/jcpp.14096http://dx.doi.org/10.1111/jcpp.14098http://dx.doi.org/10.1111/nyas.15258http://dx.doi.org/10.1111/tmi.14071http://dx.doi.org/10.1136/bmj-2024-080380http://dx.doi.org/10.1136/medhum-2024-013057http://dx.doi.org/10.1163/2208522x-bja10065http://dx.doi.org/10.1177/00380261241280463http://dx.doi.org/10.1177/02537176241294146http://dx.doi.org/10.1177/10497323241302653http://dx.doi.org/10.1177/10556656241298217http://dx.doi.org/10.1177/1357034x241298153http://dx.doi.org/10.1177/13634593241303610http://dx.doi.org/10.1177/14782715241301486http://dx.doi.org/10.1177/17470161241298726http://dx.doi.org/10.1177/17474930241306987http://dx.doi.org/10.1177/17579759241293453http://dx.doi.org/10.1182/blood-2024-200400http://dx.doi.org/10.1182/blood-2024-201577http://dx.doi.org/10.1182/blood-2024-204693http://dx.doi.org/10.1182/blood-2024-205848http://dx.doi.org/10.1182/blood-2024-206754http://dx.doi.org/10.1182/blood-2024-208843http://dx.doi.org/10.12688/aasopenres.13092.2http://dx.doi.org/10.12688/wellcomeopenres.20547.3http://dx.doi.org/10.12688/wellcomeopenres.21141.1http://dx.doi.org/10.12688/wellcomeopenres.23133.1http://dx.doi.org/10.12688/wellcomeopenres.23291.1http://dx.doi.org/10.12688/wellcomeopenres.23320.1http://dx.doi.org/10.12688/wellcomeopenres.23364.1http://dx.doi.org/10.12688/wellcomeopenres.23429.1http://dx.doi.org/10.1371/journal.pbio.3002886http://dx.doi.org/10.1371/journal.pbio.3002908http://dx.doi.org/10.1371/journal.pgph.0003762http://dx.doi.org/10.1371/journal.pgph.0003940http://dx.doi.org/10.15407/bioorganica2024.02.037http://dx.doi.org/10.21037/jmai-24-94http://dx.doi.org/10.23889/ijpds.v9i2.2402http://dx.doi.org/10.3201/eid3012.231733http://dx.doi.org/10.3310/nihropenres.13523.2http://dx.doi.org/10.3310/nihropenres.13555.1http://dx.doi.org/10.3310/nihropenres.13787.1http://dx.doi.org/10.3389/fitd.2024.1346828http://dx.doi.org/10.3389/fmala.2024.1481816http://dx.doi.org/10.3389/fsufs.2024.1390047http://dx.doi.org/10.3389/fsufs.2024.1451656http://dx.doi.org/10.3390/su16229689http://dx.doi.org/10.5152/thoracrespract.2024.24075http://dx.doi.org/10.51628/001c.127770http://dx.doi.org/10.5334/cstp.739http://dx.doi.org/10.5588/ijtld.24.0255http://dx.doi.org/10.59556/japi.72.0766http://dx.doi.org/10.61373/gp024i.0076http://dx.doi.org/10.7189/jogh.14.03046http://dx.doi.org/10.7189/jogh.14.04191http://dx.doi.org/10.7189/jogh.14.04228http://dx.doi.org/10.7189/jogh.14.04235http://dx.doi.org/10.7189/jogh.14.05035http://dx.doi.org/10.7554/elife.100478http://dx.doi.org/10.7554/elife.100569.3http://dx.doi.org/10.7554/elife.100840http://dx.doi.org/10.7554/elife.100856.3http://dx.doi.org/10.7554/elife.102222.3http://dx.doi.org/10.7554/elife.102592.3http://dx.doi.org/10.7554/elife.103047http://dx.doi.org/10.7554/elife.103403http://dx.doi.org/10.7554/elife.103492http://dx.doi.org/10.7554/elife.88584.3http://dx.doi.org/10.7554/elife.88768.3http://dx.doi.org/10.7554/elife.89361.3http://dx.doi.org/10.7554/elife.89950.4http://dx.doi.org/10.7554/elife.91642.4http://dx.doi.org/10.7554/elife.92854.4http://dx.doi.org/10.7554/elife.93002.3http://dx.doi.org/10.7554/elife.93764.3http://dx.doi.org/10.7554/elife.95106.3http://dx.doi.org/10.7554/elife.97188.3http://dx.doi.org/10.7554/elife.98349.3http://dx.doi.org/10.7554/elife.99000.3http://dx.doi.org/10.7554/elife.99303.3http://dx.doi.org/10.7554/elife.99785http://dx.doi.org/10.7759/cureus.73408"


def parse_dois(raw: str) -> list[str]:
    return re.findall(r'10\.\S+?(?=http|$)', raw.strip())


# ── Date patterns, applied in priority order ─────────────────────────────────
# Each entry: (label, regex, converter)
# converter(match) → "YYYY-MM-DD" style string

PATTERNS = [
    # YYYY.MM.DD  e.g. 2024.11.004  (day part may be article suffix, kept for transparency)
    (
        "YYYY.MM",
        re.compile(r'(?<![0-9])((?:199[0-9]|20[012][0-9]))\.(0[1-9]|1[0-2])(?=\.|$|\D)'),
        lambda m: f"{m.group(1)}-{m.group(2)}",
    ),
    # (YY) — Lancet-style  e.g. (24) → 2024
    (
        "(YY)",
        re.compile(r'\(([0-9]{2})\)'),
        lambda m: f"20{m.group(1)}",
    ),
    # -YYYY- or .YYYY- or /YYYY. with clear word boundaries
    (
        "YYYY",
        re.compile(r'(?<![0-9])((?:199[0-9]|20[012][0-9]))(?![0-9])'),
        lambda m: m.group(1),
    ),
    # YY in suffix after letter  e.g.  jrae041 → no; but "24-94" → 2024
    # SAGE-style  e.g. 241280463 → year 2024, month 12
    (
        "YYMM…",
        re.compile(r'(?<![0-9])(2[0-9])(0[1-9]|1[0-2])\d{5,}'),
        lambda m: f"20{m.group(1)}-{m.group(2)}",
    ),
    # ACS suffix: 4c → year 2024, 5c → 2025 (digit = last digit of 202X)
    (
        "Nc (ACS)",
        re.compile(r'\.([0-9])c[0-9]{5}$'),
        lambda m: f"202{m.group(1)}",
    ),
    # last-resort 2-digit year after dash only: -24- means 2024
    # Requires digits 20-30 to avoid matching volume/issue numbers like .14.
    (
        "YY",
        re.compile(r'-([2-9][0-9])-'),
        lambda m: f"20{m.group(1)}" if int(m.group(1)) <= 30 else f"19{m.group(1)}",
    ),
]


def extract_dates_from_doi(doi: str) -> list[tuple[str, str]]:
    """Return list of (label, date_string) found in the DOI suffix (after the prefix)."""
    # Work only on the part after the registrant prefix  e.g. everything after "10.NNNN/"
    suffix = re.sub(r'^10\.\d{4,}/', '', doi)
    found: list[tuple[str, str]] = []
    seen_spans: list[tuple[int, int]] = []

    for label, pattern, converter in PATTERNS:
        for m in pattern.finditer(suffix):
            # Skip if this span overlaps an already-captured match
            if any(m.start() < e and m.end() > s for s, e in seen_spans):
                continue
            date_str = converter(m)
            # Sanity-check: year must be plausible
            year = int(date_str[:4])
            if not (1990 <= year <= 2030):
                continue
            found.append((label, date_str))
            seen_spans.append((m.start(), m.end()))

    return found


def main():
    dois = parse_dois(DOIS_RAW)
    print(f"Parsed {len(dois)} DOIs\n")

    rows = []
    for doi in dois:
        hits = extract_dates_from_doi(doi)
        if hits:
            for label, date in hits:
                rows.append({"DOI": doi, "Pattern": label, "Date": date})
        else:
            rows.append({"DOI": doi, "Pattern": "—", "Date": ""})

    # Write CSV
    out = "doi_dates.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["DOI", "Pattern", "Date"])
        writer.writeheader()
        writer.writerows(rows)

    # Print table
    print(f"{'DOI':<55} {'Pattern':<12} {'Date'}")
    print("-" * 85)
    prev_doi = None
    for r in rows:
        doi_col = r["DOI"] if r["DOI"] != prev_doi else ""
        print(f"{doi_col:<55} {r['Pattern']:<12} {r['Date']}")
        prev_doi = r["DOI"]

    print(f"\nSaved {len(rows)} rows → {out}")


if __name__ == "__main__":
    main()
