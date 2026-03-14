#!/usr/bin/env python3
"""Fetch title and publication date for DOIs via Crossref API."""

import re
import csv
import time
import urllib.request
import urllib.error
import json

DOIS_RAW = "10.1001/jama.2025.781710.1001/jamanetworkopen.2025.1229610.1002/2688-8319.7004510.1007/s10461-025-04694-y10.1007/s10461-025-04726-710.1007/s10461-025-04761-410.1007/s10461-025-04790-z10.1007/s10461-025-04799-410.1007/s10739-025-09809-810.1007/s10912-025-09941-w10.1007/s10912-025-09954-510.1007/s10943-025-02299-210.1007/s11017-025-09710-910.1007/s11136-025-04009-710.1007/s11166-025-09453-x10.1007/s12021-025-09726-510.1007/s12115-025-01108-610.1007/s42113-025-00250-y10.1016/j.apr.2025.10255310.1016/j.bglo.2025.10001610.1016/j.cdnut.2025.10692310.1016/j.cegh.2025.10202110.1016/j.celrep.2025.11595610.1016/j.emospa.2025.10108610.1016/j.hlpt.2025.10102810.1016/j.jdeveco.2025.10356010.1016/j.jeud.2025.10012110.1016/j.jrurstud.2025.10363210.1016/j.jrurstud.2025.10375010.1016/j.jvacx.2025.10067610.1016/j.lanmic.2025.10114010.1016/j.oneear.2025.10134810.1016/j.paid.2025.11326010.1016/j.phyplu.2025.10079310.1016/j.praneu.2025.04.00210.1016/j.sajb.2025.03.01310.1016/j.sigpro.2025.11011610.1016/j.ssmhs.2025.10007910.1016/j.ssmhs.2025.10008110.1016/j.ssmhs.2025.10008610.1016/j.ssmhs.2025.10009010.1016/j.ssmmh.2025.10044910.1016/j.ssmmh.2025.10046010.1016/j.ssmmh.2025.10046610.1016/j.ssmmh.2025.10047010.1016/j.ssmmh.2025.10048710.1016/s0140-6736(25)00691-910.1016/s2213-2600(25)00199-710.1017/mdh.2025.310.1017/s002193202500018510.1017/s002193202500024010.1021/acs.analchem.5c0143910.1021/acs.biochem.5c0027410.1021/acs.jproteome.5c0016710.1021/acsabm.5c0026610.1021/acsinfecdis.4c0075110.1037/hop000027610.1037/pag000090410.1037/pas000139010.1037/pha000077410.1037/tra000194410.1037/xlm000146210.1037/xlm000149210.1038/s41422-025-01127-210.1038/s41562-025-02188-410.1038/s41564-025-02010-x10.1038/s41588-025-02219-w10.1055/a-2602-328810.1056/nejmoa240811410.1056/nejmoa241336110.1056/nejmoa250575210.1057/s41292-025-00351-810.1080/05704928.2025.251904810.1080/13811118.2025.248915910.1080/15476286.2025.252588610.1080/26410397.2025.252103110.1084/jem.2025088310.1089/aut.2024.030710.1089/dna.2025.006410.1093/ajeadv/uuaf00310.1093/biosci/biaf09110.1093/brain/awaf16010.1093/eurpub/ckaf05810.1093/eurpub/ckaf07810.1093/eurpub/ckaf10210.1093/gbe/evaf08910.1093/gbe/evaf11610.1093/heapol/czaf03810.1093/heapro/daaf06110.1093/neuonc/noaf10310.1093/nutrit/nuaf00210.1093/rheumatology/keaf142.02010.1093/schbul/sbaf08310.1093/schbul/sbaf10010.1093/shm/hkae09410.1093/shm/hkaf02810.1093/shm/hkaf04010.1097/aud.000000000000167310.1097/inf.000000000000484210.1097/inf.000000000000485510.1097/inf.000000000000490710.1109/mcse.2025.357388710.1111/jade.1258010.1111/jcpp.1417310.1111/jcpp.1417510.1136/bmj.r79110.1136/bmjopen-2024-09687910.1136/medhum-2025-01328210.1136/thorax-2024-22173810.1146/annurev-micro-121423-11595910.1146/annurev-neuro-112723-02334110.1161/circresaha.125.32549210.1164/ajrccm.2025.211.abstracts.a141510.1164/ajrccm.2025.211.abstracts.a328810.1164/ajrccm.2025.211.abstracts.a495910.1164/ajrccm.2025.211.abstracts.a769410.1164/ajrccm.2025.211.abstracts.a772610.1164/ajrccm.2025.211.abstracts.a778510.1167/iovs.66.6.4010.1167/iovs.66.6.6410.1176/appi.neuropsych.2024021510.1177/0020764025133672610.1177/0036850425133863110.1177/0269881125134092510.1177/0300985825134301710.1177/0748730425132850110.1177/0748730425133662410.1177/0952695125132811410.1177/0952695125133137810.1177/1360780424128768310.1177/1362361325134101210.1177/1387287725133777610.1177/1470594x25133959410.1177/1744806925134240910.1177/1877718x25132985710.1177/1932296825133292510.1177/2754633025134855410.1192/bjp.2025.4910.1192/bjp.2025.6910.1212/wnl.000000000021036910.1213/ane.000000000000749410.1242/dev.20480010.1242/dev.20493910.1242/dev.20494810.12688/aasopenres.13241.210.12688/openreseurope.19356.210.12688/wellcomeopenres.18637.210.12688/wellcomeopenres.21122.210.12688/wellcomeopenres.23002.210.12688/wellcomeopenres.23905.110.12688/wellcomeopenres.24031.110.12688/wellcomeopenres.24094.110.12688/wellcomeopenres.24139.110.12688/wellcomeopenres.24264.110.12688/wellcomeopenres.24272.110.12944/crnfsj.13.1.410.1302/0301-620x.107b1.bjj-2024-089410.1302/0301-620x.107b2.bjj-2024-0660.r110.1302/0301-620x.107b4.bjj-2024-1164.r110.1302/0301-620x.107b5.bjj-2024-1346.r210.1332/20437897y2025d00000006910.1353/bhm.2025.a96372610.1353/lm.2025.a97554210.1353/lm.2025.a97555210.1353/sex.0001910.1353/tcc.2025.a95042710.1371/journal.pbio.300307010.1371/journal.pbio.300315710.1371/journal.pcbi.101273110.1371/journal.pclm.000046910.1371/journal.pclm.000060110.1371/journal.pcsy.000002810.1371/journal.pgph.000403910.1371/journal.pgph.000409410.1371/journal.pntd.001283310.1371/journal.pntd.001300110.1371/journal.ppat.101307110.1371/journal.pwat.000033710.1503/cmaj.24099610.1525/collabra.13645610.1681/asn.000000077310.16993/sjdr.124010.18653/v1/2025.sdp-1.410.20935/acadmolbiogen779810.21105/joss.0756310.21105/joss.0760110.21105/joss.0760410.2139/ssrn.476513610.2218/ijdc.v19i1.98310.23889/ijpds.v10i1.239110.23889/ijpds.v10i1.246810.30827/dynamis.v45i1.3309010.3201/eid3102.24025110.3201/eid3102.24177710.3201/eid3103.24121110.3201/eid3103.24149310.3201/eid3104.24147110.3201/eid3105.24169010.3201/eid3105.24175710.3201/eid3106.24179610.3310/nihropenres.13512.110.3310/nihropenres.13568.210.3310/nihropenres.13842.110.3389/fpubh.2025.151721310.3390/a1802008610.3390/agriculture1505045010.3390/jal501000510.3390/make702002810.3390/populations102001210.3390/urbansci902003710.3390/w1710144910.3758/s13415-025-01268-210.3758/s13423-024-02633-x10.3758/s13428-025-02630-510.4088/jcp.24m1562210.4337/cilj.2025.01.0110.47941/ijhmnp.258110.5152/iao.2025.24169310.5195/pom.2025.22210.7189/jogh.15.0401410.7189/jogh.15.0402210.7189/jogh.15.0407110.7189/jogh.15.04187"


def parse_dois(raw: str) -> list[str]:
    # Handles both plain DOIs (10.XXXX/...) and full URLs (http://dx.doi.org/10.XXXX/...)
    return re.findall(r'10\.\d{4,}/\S+?(?=10\.\d{4,}/|https?://|$)', raw.strip())


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


def fetch_crossref(doi: str) -> tuple[str, str]:
    """Return (title, date) from Crossref API. Date as YYYY-MM-DD or YYYY-MM or YYYY."""
    url = f"https://api.crossref.org/works/{doi}?mailto=user@example.com"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "doi-fetcher/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())["message"]

        # Title
        titles = data.get("title", [])
        title = titles[0] if titles else ""

        # Date: prefer published, then published-print, then published-online, then created
        for key in ("published", "published-print", "published-online", "created"):
            parts = data.get(key, {}).get("date-parts", [[]])[0]
            if parts and parts[0]:
                date = "-".join(str(p).zfill(2) for p in parts)
                return title, date

        return title, ""
    except Exception as e:
        return "", f"ERROR: {e}"


def main():
    dois = parse_dois(DOIS_RAW)
    print(f"Parsed {len(dois)} DOIs — fetching from Crossref...\n")

    rows = []
    for i, doi in enumerate(dois, 1):
        print(f"  [{i}/{len(dois)}] {doi}", end=" ", flush=True)
        title, date = fetch_crossref(doi)
        rows.append({"DOI": doi, "Title": title, "Date": date})
        print(f"→ {date[:10] if date else '—'}")
        time.sleep(0.1)  # polite rate limit

    # Write CSV
    out = "doi_dates.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["DOI", "Title", "Date"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows → {out}")


if __name__ == "__main__":
    main()
