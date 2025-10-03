#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV（科目名/単位数/大区分/小区分）を第3正規形相当へ分割：
- Categories（大区分）
- SubCategories（小区分 + 大区分ID）
- Subjects（科目 + 単位数 + 小区分ID）

出力：
- categories.csv, subcategories.csv, subjects.csv（UTF-8 BOM付き）
- normalized.db（SQLite, 外部キー有効）
- schema.sql（CREATE TABLE）
- inserts.sql（全件INSERT）

使い方例：
python normalize_db.py \
  --input /path/to/Bioinformatics-And-Bioengineering.csv \
  --outdir ./out
"""

import argparse
import os
import sqlite3
from typing import Tuple

import pandas as pd

try:
    import chardet  # 文字コード推定（任意）
    HAS_CHARDET = True
except Exception:
    HAS_CHARDET = False


REQUIRED_COLS = ["科目名", "単位数", "大区分", "小区分"]


def detect_encoding(path: str, fallback: str = "utf-8") -> str:
    if not HAS_CHARDET:
        return fallback
    with open(path, "rb") as f:
        raw = f.read(200_000)
    res = chardet.detect(raw)
    enc = (res.get("encoding") or fallback).upper()
    # Windows系CSVを想定してCP932優先
    return "CP932" if enc in {"SHIFT_JIS", "SJIS", "CP932", "MS932"} else enc


def load_source_csv(path: str) -> pd.DataFrame:
    enc = detect_encoding(path, fallback="utf-8")
    df = pd.read_csv(path, encoding=enc)
    # 列名/文字列の前後空白除去
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise KeyError(f"必要カラムが不足しています: {missing}（CSVの列名を確認してください）")
    for col in ["科目名", "大区分", "小区分"]:
        df[col] = df[col].astype(str).str.strip()
    df["単位数"] = pd.to_numeric(df["単位数"], errors="coerce")
    return df


def normalize(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Categories（大区分）
    categories = (
        df[["大区分"]]
        .drop_duplicates()
        .sort_values("大区分")
        .reset_index(drop=True)
        .reset_index(names="大区分ID")
    )
    categories["大区分ID"] += 1  # 1始まり

    # SubCategories（小区分 + 大区分ID）
    subcats = (
        df[["大区分", "小区分"]]
        .drop_duplicates()
        .merge(categories, on="大区分", how="left")
        .sort_values(["大区分ID", "小区分"])
        .reset_index(drop=True)
        .reset_index(names="小区分ID")
    )
    subcats["小区分ID"] += 1
    subcats = subcats[["小区分ID", "小区分", "大区分ID"]]

    # Subjects（科目 + 単位数 + 小区分ID）
    subjects = (
        df[["科目名", "単位数", "大区分", "小区分"]]
        .merge(categories, on="大区分", how="left")
        .merge(subcats, on=["小区分", "大区分ID"], how="left")
        .reset_index(drop=True)
    )
    subjects = subjects[["科目名", "単位数", "小区分ID"]].reset_index(names="科目ID")
    subjects["科目ID"] += 1

    return categories, subcats, subjects


SCHEMA_SQL = """\
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS Subjects;
DROP TABLE IF EXISTS SubCategories;
DROP TABLE IF EXISTS Categories;

CREATE TABLE Categories (
  category_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE SubCategories (
  subcategory_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category_id INTEGER NOT NULL,
  UNIQUE(name, category_id),
  FOREIGN KEY(category_id)
    REFERENCES Categories(category_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE Subjects (
  subject_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  credits REAL NOT NULL,
  subcategory_id INTEGER NOT NULL,
  FOREIGN KEY(subcategory_id)
    REFERENCES SubCategories(subcategory_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);
"""


def to_insert_values(df: pd.DataFrame, table: str, cols: list[str]) -> str:
    def esc(v):
        if isinstance(v, str):
            return "'" + v.replace("'", "''") + "'"
        if pd.isna(v):
            return "NULL"
        return str(v)

    values = []
    for row in df[cols].itertuples(index=False, name=None):
        values.append("(" + ", ".join(esc(v) for v in row) + ")")
    return f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n  " + ",\n  ".join(values) + ";\n"


def save_csvs(categories: pd.DataFrame, subcats: pd.DataFrame, subjects: pd.DataFrame, outdir: str) -> None:
    os.makedirs(outdir, exist_ok=True)
    categories.to_csv(os.path.join(outdir, "categories.csv"), index=False, encoding="utf-8-sig")
    subcats.to_csv(os.path.join(outdir, "subcategories.csv"), index=False, encoding="utf-8-sig")
    subjects.to_csv(os.path.join(outdir, "subjects.csv"), index=False, encoding="utf-8-sig")


def build_sqlite(categories: pd.DataFrame, subcats: pd.DataFrame, subjects: pd.DataFrame, outdir: str) -> None:
    db_path = os.path.join(outdir, "normalized.db")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript(SCHEMA_SQL)

    categories_sql = categories.rename(columns={"大区分ID": "category_id", "大区分": "name"})
    subcats_sql = subcats.rename(columns={"小区分ID": "subcategory_id", "小区分": "name", "大区分ID": "category_id"})
    subjects_sql = subjects.rename(columns={"科目ID": "subject_id", "科目名": "name", "単位数": "credits", "小区分ID": "subcategory_id"})

    cur.executemany(
        "INSERT INTO Categories(category_id, name) VALUES(?, ?)",
        categories_sql[["category_id", "name"]].itertuples(index=False, name=None),
    )
    cur.executemany(
        "INSERT INTO SubCategories(subcategory_id, name, category_id) VALUES(?, ?, ?)",
        subcats_sql[["subcategory_id", "name", "category_id"]].itertuples(index=False, name=None),
    )
    cur.executemany(
        "INSERT INTO Subjects(subject_id, name, credits, subcategory_id) VALUES(?, ?, ?, ?)",
        subjects_sql[["subject_id", "name", "credits", "subcategory_id"]].itertuples(index=False, name=None),
    )

    con.commit()
    con.close()


def write_sql_scripts(categories: pd.DataFrame, subcats: pd.DataFrame, subjects: pd.DataFrame, outdir: str) -> None:
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "schema.sql"), "w", encoding="utf-8") as f:
        f.write(SCHEMA_SQL)

    categories_sql = categories.rename(columns={"大区分ID": "category_id", "大区分": "name"})
    subcats_sql = subcats.rename(columns={"小区分ID": "subcategory_id", "小区分": "name", "大区分ID": "category_id"})
    subjects_sql = subjects.rename(columns={"科目ID": "subject_id", "科目名": "name", "単位数": "credits", "小区分ID": "subcategory_id"})

    with open(os.path.join(outdir, "inserts.sql"), "w", encoding="utf-8") as f:
        f.write(to_insert_values(categories_sql, "Categories", ["category_id", "name"]))
        f.write("\n")
        f.write(to_insert_values(subcats_sql, "SubCategories", ["subcategory_id", "name", "category_id"]))
        f.write("\n")
        f.write(to_insert_values(subjects_sql, "Subjects", ["subject_id", "name", "credits", "subcategory_id"]))


def main():
    ap = argparse.ArgumentParser(description="Normalize course CSV to 3NF tables (Categories/SubCategories/Subjects).")
    ap.add_argument("--input", required=True, help="入力CSV（科目名, 単位数, 大区分, 小区分 列を含む）")
    ap.add_argument("--outdir", default="./out", help="出力ディレクトリ（既定: ./out）")
    ap.add_argument("--no-sqlite", action="store_true", help="SQLite出力をスキップする")
    ap.add_argument("--no-sql", action="store_true", help="schema.sql / inserts.sql の出力をスキップする")
    args = ap.parse_args()

    df = load_source_csv(args.input)
    categories, subcats, subjects = normalize(df)

    save_csvs(categories, subcats, subjects, args.outdir)

    if not args.no_sqlite:
        build_sqlite(categories, subcats, subjects, args.outdir)

    if not args.no_sql:
        write_sql_scripts(categories, subcats, subjects, args.outdir)

    print(f"Done. Output -> {os.path.abspath(args.outdir)}")


if __name__ == "__main__":
    main()