import re
from src.extractors import remove_header_text
from groq import Groq
import json
import textwrap

def extract_patient_parse(text: str):
    """Extract structured patient details from text."""
    # print("=" * 40, "Patient Details", "=" * 40)
    patient_details = {}

    patterns = {
        "Patient Name": r'Patient Name\s*:\s*(.+?)(?=\s*IP#|$)',
        "Age/Gender": r'Age/Gender\s*:\s*(.+)',
        "IP No": r'IP No\.\s*:\s*(.+)',
        "UMR No": r'UMR No\.\s*:\s*(.+)',
        "Admission Date": r'Admn Date\s*:\s*(.+)',
        "Discharge Date": r'Discharge Date\s*:\s*(.+)',
        "Doctor Name": r'Doctor Name\s*:\s*(.+)',
        "Ward/Room/Bed": r'Ward/Room/Bed\s*:\s*(.+)',
        "Mobile No": r'Mobile No\.\s*:\s*(.+)',
        "Address": r'Address\s*:\s*(.+)',
        "Prime Consultant": r'Doctor Name\s*:\s*(.+)',
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        patient_details[field] = match.group(1).strip() if match else None

    care_team_pattern = r'^\s*(Dr\.?\s+[A-Z][a-zA-Z\s]*(?:\([A-Za-z]+\))?)\s*'
    care_team = re.findall(care_team_pattern, text, re.MULTILINE | re.IGNORECASE)
    care_team = care_team[-2:]
    patient_details["Care Team"] = [re.sub(r'[\n\s\xa0]+', ' ', d).strip() for d in care_team]

    # for k, v in patient_details.items():
    #     if k == "Care Team":
    #         print(f"{k}:")
    #         for doc in v:
    #             print(" -", doc)
    #     else:
    #         print(f"{k}: {v}")

    return patient_details


def demographics_parse(text: str):
    """Extract diagnosis and treatment sections with clean formatting."""
    diagnosis = {}
    patterns = {
        "Diagnosis": r"DIAGNOSIS\s*(.+?)\s*(?=TREATMENT)",
        "Treatment": r"TREATMENT\s*(.+?)(?=\n\s*Patient Name:|\n\d{2}-\d{2}-\d{4}|$)",
        "Chief Complaints": r"CHIEF COMPLAINTS\S*(.+?)(?=\n\s*PRESENT HISTORY)",
        "Present History": r"PRESENT HISTORY\S*(.+?)(?=\n\s*PAST HISTORY)",
        "Past History": r"PAST HISTORY\S*(.+?)(?=\n\s*ON EXAMINATION)"
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        value = match.group(1).strip() if match else None

        if value:
            clean_value = "\n".join(
                line.strip() for line in value.strip().splitlines() if line.strip()
            )
        else:
            clean_value = None

        diagnosis[field] = clean_value

    # print("=" * 40, "Diagnosis & Treatment", "=" * 40)
    # for field, value in diagnosis.items():
    #     print(f"{field}:\n{value}\n")

    return diagnosis
def discharge_condition_parse(text: str):
    discharge = {}

    pattern = (
        r"CONDITION\s*(?:AT\s+THE\s+TIME\s+OF\s+)?DISCHARGE[:\s-]*"
        r"([\s\S]+?)(?=\bDISCHARGE\s+ADVICE\b|$)"
    )

    match = re.search(pattern, text, re.IGNORECASE)
    discharge["condition"] = match.group(1).strip() if match else None

    return discharge


def discharge_condition_parse(text: str):
    discharge = {}

    # First extract the discharge condition block
    pattern = r"CONDITION AT THE TIME OF DISCHARGE\s*(.+?)\s*(?=DISCHARGE ADVICE|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return {"condition": None}

    block = match.group(1)
    block = re.sub(r"\xa0", " ", block)  # clean non-breaking spaces

    # --- Split into sections ---
    lines = [l.strip() for l in block.splitlines() if l.strip()]

    # 1️⃣ General condition summary
    summary_lines = []
    for l in lines:
        if re.match(r"^(Patient|No pallor|On \d{1,2}/\d{1,2}/\d{4})", l, re.IGNORECASE):
            summary_lines.append(l)
        else:
            break
    discharge["condition_summary"] = " ".join(summary_lines)

    # 2️⃣ Devices / tubes present
    device_lines = [l for l in lines if "insitu" in l.lower()]
    discharge["devices"] = device_lines if device_lines else None

    # 3️⃣ Vitals
    vitals_match = re.search(
        r"HR[:\s]*[\d/]+.*?(BP[:\s]*[^\n]*)", block, re.IGNORECASE
    )
    discharge["vitals"] = vitals_match.group(0).strip() if vitals_match else None

 
    systems = {}
    for sys in ["CVS", "RS", "P/A", "CNS"]:
        m = re.search(rf"{sys}[:\s]*(.*?)(?:;|$)", block)
        if m:
            systems[sys] = m.group(1).strip()
    discharge["systems"] = systems if systems else None

    # 5️⃣ Lab results (with date)
    labs = []
    lab_pattern = re.compile(
        r"On\s+(\d{1,2}/\d{1,2}/\d{4})\s*(.+?)(?=On\s+\d{1,2}/\d{1,2}/\d{4}|$)",
        re.DOTALL | re.IGNORECASE
    )
    for date, details in lab_pattern.findall(block):
        labs.append({"date": date, "details": re.sub(r"\s+", " ", details).strip()})
    discharge["lab_results"] = labs if labs else None

    return discharge
def medication_parse(text:str):
    clean_text = remove_header_text(text)
    medication = {}

    section_pattern = (
        r"(?:(?<=\n)|(?<=^))\s*"
        r"(IMMUNOSUPPRESSANTS\s*:|"
        r"RESPIRATORY\s+DRUGS\s*:|"
        r"CARDIAC\s+DRUGS\s*:|"
        r"ANTI\s+INFECTIVE\s+PROPHYLAXIS\s*:|"
        r"GI\s+DRUGS\s*:|"
        r"SUPPLEMENTS\s*:|"
        r"OTHERS\s*:)"
    )

    parts = re.split(section_pattern, clean_text, flags=re.IGNORECASE)

    current_category = None
    for part in parts:
        part = part.strip()
        if not part:
            continue

        if re.match(r"^[A-Z][A-Z\s]*:$", part):
            current_category = part.strip(":").upper()
            medication[current_category] = []
        elif current_category:
            for line in part.split("\n"):
                line = line.strip()
                if re.match(r"^(TAB|CAP|SYP|INJ|NEB|DROP|OINT|CREAM|SUPP)\b", line, re.IGNORECASE):
                    medication[current_category].append(line)
    return medication
