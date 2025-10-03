import os
import csv

STORAGE_FILE = os.getenv("STORAGE_FILE", "saved_entries.csv")

def append_entries(entries):
    """CSV に追記保存"""
    file_exists = os.path.exists(STORAGE_FILE)
    with open(STORAGE_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "grade", "credits", "field"])
        if not file_exists:
            writer.writeheader()
        for e in entries:
            writer.writerow({
                "name": e.get("name", ""),
                "grade": e.get("grade", ""),
                "credits": e.get("credits", ""),
                "field": e.get("field", "")
            })

def load_entries():
    """CSV から全てのエントリを読み込む"""
    if not os.path.exists(STORAGE_FILE):
        return []
    with open(STORAGE_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]
