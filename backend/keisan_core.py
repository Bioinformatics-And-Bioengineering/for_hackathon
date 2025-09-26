# gpa_core.py
from typing import List, Dict, Any

# A~F ¨ 4.0~0.0
GRADE_TO_POINT: Dict[str, float] = {
    "A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0,
}

def compute_gpa(entries_with_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    entries_with_meta: [{"name","grade","credits","field"}...]
    GPA = ƒ°(point*credits) / ƒ°(credits) ‚ğ¬”‘æ2ˆÊ‚Å•Ô‚·
    """
    if not entries_with_meta:
        return {"gpa": 0.00, "total_credits_counted": 0.0, "details": []}

    numer = denom = 0.0
    details: List[Dict[str, Any]] = []

    for i, e in enumerate(entries_with_meta):
        name = str(e.get("name", "")).strip()
        grade_raw = str(e.get("grade", "")).strip().upper()
        credits = e.get("credits", 0)

        if not name:
            raise ValueError(f"entries[{i}].name is empty")
        if grade_raw not in GRADE_TO_POINT:
            raise ValueError(f"entries[{i}].grade '{grade_raw}' not supported (A/B/C/D/F)")

        try:
            cr = float(credits)
        except Exception:
            raise ValueError(f"entries[{i}].credits is not a number")
        if cr <= 0:
            raise ValueError(f"entries[{i}].credits must be > 0")

        point = GRADE_TO_POINT[grade_raw]
        numer += point * cr
        denom += cr

        details.append({
            "name": name, "grade": grade_raw, "point": point,
            "credits": cr, "field": e.get("field", "TBD"),
        })

    gpa = round(numer / denom, 2) if denom else 0.00
    return {"gpa": gpa, "total_credits_counted": denom, "details": details}
