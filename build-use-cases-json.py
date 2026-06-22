#!/usr/bin/env python3
"""Regenerate use-cases.json from use-cases.csv (the single source of truth).

Run after editing use-cases.csv (e.g. re-scoring):  python3 build-use-cases-json.py
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "use-cases.csv")
JSON_PATH = os.path.join(HERE, "use-cases.json")

INT_FIELDS = {"real_use_score"}


def main() -> None:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in INT_FIELDS:
            r[k] = int(r[k])

    doc = {
        "meta": {
            "name": "Flipper Zero rig — use-case data model",
            "generated": "2026-06-19",
            "source": "use-cases.csv",
            "count": len(rows),
            "rig": {
                "device": "Flipper Zero FZ.1",
                "firmware_target": "Momentum",
                "accessories": [
                    "external 433 MHz CC1101 SMA board",
                    "ESP32-WROOM Marauder w/ onboard microSD",
                ],
            },
            "real_use_score_rubric": {
                "9-10": "high, recurring real value",
                "7-8": "solidly useful, periodic",
                "5-6": "situational / occasional",
                "3-4": "niche / demo / novelty",
                "1-2": "rarely practical / prank / impossible-by-design",
            },
            "enums": {
                "category": ["IR", "SubGHz", "RFID-LF", "NFC-HF", "iButton",
                             "HID", "BLE", "WiFi", "GPIO", "Software", "Defensive"],
                "target": ["Hardware", "Software", "Hybrid"],
                "firmware": ["OFW", "CFW", "n/a"],
                "difficulty": ["Easy", "Medium", "Hard"],
                "legality": ["Low", "Medium", "High"],
                "status": ["Ready", "NeedAccessory", "ByDesign-No"],
                "prereq_consumable": ["None", "T5577 blank", "NTAG21x blank",
                                      "NTAG215 blank", "Magic card", "RW1990 blank"],
                "time_to_value": ["Instant", "Quick", "Setup", "Project", "n/a"],
            },
            "field_order": list(rows[0].keys()) if rows else [],
        },
        "use_cases": rows,
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {JSON_PATH}: {len(rows)} use-cases")


if __name__ == "__main__":
    main()
