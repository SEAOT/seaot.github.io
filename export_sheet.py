#!/usr/bin/env python3
"""Export the website-content workbook (xlsx download of the Google Sheet) to sheet_data.json.

Usage:  python3 export_sheet.py check.xlsx
Sheets: People, Publications, Projects, SEAL Lab capabilities, News (header row 1, help row 2,
        data from row 3; blank 'Full name/Title/Project name/Capability/Date' rows are skipped)
        Team info (Field/Value pairs), Pages (planned pages).
"""
import sys, json, datetime, openpyxl

src = sys.argv[1] if len(sys.argv) > 1 else "check.xlsx"
wb = openpyxl.load_workbook(src, data_only=True)

def cell(v):
    if v is None: return ""
    if isinstance(v, (datetime.datetime, datetime.date)): return str(v)
    if isinstance(v, float) and v.is_integer(): return int(v)
    return str(v).strip() if isinstance(v, str) else v

def rows(name, key):
    ws = wb[name]
    hdr = [cell(c) for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
    out = []
    for r in ws.iter_rows(min_row=3, values_only=True):
        d = {h: cell(v) for h, v in zip(hdr, r) if h}
        if str(d.get(key, "")).strip(): out.append(d)
    return out

team = {}
for r in wb["Team info"].iter_rows(min_row=2, values_only=True):
    if r[0]: team[cell(r[0])] = cell(r[1])

D = {"people": rows("People", "Full name *"),
     "pubs": rows("Publications", "Title *"),
     "projects": rows("Projects", "Project name *"),
     "caps": rows("SEAL Lab capabilities", "Capability / specification *"),
     "news": rows("News", "Date *"),
     "team": team}
if "Pages" in wb.sheetnames:
    ws = wb["Pages"]; hdr = [cell(c) for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
    D["pages"] = [{h: cell(v) for h, v in zip(hdr, r) if h} for r in ws.iter_rows(min_row=2, values_only=True) if r[0]]
json.dump(D, open("sheet_data.json", "w"), ensure_ascii=False, indent=1)
print({k: (len(v) if isinstance(v, list) else "dict") for k, v in D.items()})
