import re
from src.extractors import remove_header_text
from utils.cleaners import remove_garbage


def extract_patient_parse(text: str):
    """Extract structured patient details from text."""
    patient_details = {}

    try:
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
        patient_details["Care Team"] = [
            re.sub(r'[\n\s\xa0]+', ' ', d).strip() for d in care_team
        ]

    except Exception as e:
        print(f"[ERROR] extract_patient_parse failed: {e}")

    return patient_details


def demographics_parse(text: str):
    """Extract diagnosis and treatment sections with clean formatting."""
    diagnosis = {}
    try:
        patterns = {
            "Diagnosis": r"DIAGNOSIS\s*(.+?)\s*(?=TREATMENT)",
            "Treatment": r"TREATMENT\s*(.+?)(?=\n\s*Patient Name:|\n\d{2}-\d{2}-\d{4}|$)",
            "Chief Complaints": r"CHIEF COMPLAINTS\S*(.+?)(?=\n\s*PRESENT HISTORY)",
            "Present History": r"PRESENT HISTORY\S*(.+?)(?=\n\s*PAST HISTORY)",
            "Past History": r"PAST HISTORY\S*(.+?)(?=\n\s*ON EXAMINATION)",
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

    except Exception as e:
        print(f"[ERROR] demographics_parse failed: {e}")

    return diagnosis


def discharge_condition_parse(text: str):
    """Extract discharge condition details."""
    discharge = {}
    try:
        pattern = r"CONDITION AT THE TIME OF DISCHARGE\s*(.+?)\s*(?=DISCHARGE ADVICE|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            return {"condition": None}

        block = match.group(1)
        block = re.sub(r"\xa0", " ", block)

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

        # 4️⃣ Systems
        systems = {}
        for sys in ["CVS", "RS", "P/A", "CNS"]:
            m = re.search(rf"{sys}[:\s]*(.*?)(?:;|$)", block)
            if m:
                systems[sys] = m.group(1).strip()
        discharge["systems"] = systems if systems else None

        # 5️⃣ Lab results
        labs = []
        lab_pattern = re.compile(
            r"On\s+(\d{1,2}/\d{1,2}/\d{4})\s*(.+?)(?=On\s+\d{1,2}/\d{1,2}/\d{4}|$)",
            re.DOTALL | re.IGNORECASE,
        )
        for date, details in lab_pattern.findall(block):
            labs.append({"date": date, "details": re.sub(r"\s+", " ", details).strip()})
        discharge["lab_results"] = labs if labs else None

    except Exception as e:
        print(f"[ERROR] discharge_condition_parse failed: {e}")

    return discharge


def medication_parse(text: str):
    """Extract medication details from discharge advice section."""
    print("from medication parserrr................")
    medication = {}
    try:
        clean_text = remove_header_text(text)

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
                    if re.match(
                        r"^(TAB|CAP|SYP|INJ|NEB|DROP|OINT|CREAM|SUPP)\b",
                        line,
                        re.IGNORECASE,
                    ):
                        medication[current_category].append(line)

    except Exception as e:
        print(f"[ERROR] medication_parse failed: {e}")

    return medication

def test_reports_parse(txt: str):
    txt = remove_garbage(txt)

    # Flexible regex for test headers (multi-line, includes special chars)
    pattern = r"([A-Za-z0-9\s\(\)\/\-\&\+\,\.\[\]]+\s*-\s*\d{2}-\d{2}-\d{4}\s*\d{2}:\d{2})"

    parts = re.split(pattern, txt, flags=re.IGNORECASE | re.DOTALL)

    tests = {}
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = remove_garbage(parts[i + 1]) if i + 1 < len(parts) else ""

        # Extract parameter rows
        rows = parse_parameter_rows(body)
        tests[header] = rows

    return tests


def parse_parameter_rows(body: str):
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    data = []
    current = {}
    
    skip_words = {"parameter", "result", "normal range", "note", "null", "method", "patient name"}
    
    i = 0
    while i < len(lines):
        line = lines[i]
        low = line.lower()

        # Skip known header or empty lines
        if any(w in low for w in skip_words):
            i += 1
            continue

        # Detect parameter (usually uppercase, contains spaces or parentheses)
        if re.match(r"^[A-Z][A-Z0-9\s\(\)\-\/\+%\.]+$", line):
            param = line
            result = ""
            normal = ""

            # Try to take next one or two lines as result/range
            if i + 1 < len(lines) and not re.match(r"^[A-Z][A-Z0-9\s\(\)\-\/\+%\.]+$", lines[i + 1]):
                result = lines[i + 1]
                i += 1

            if i + 1 < len(lines) and re.search(r"\d", lines[i + 1]):  # something numeric
                normal = lines[i + 1]
                i += 1

            data.append({
                "Parameter": param,
                "Result": result.strip(),
                "Normal Range": normal.strip()
            })

        i += 1

    return data
