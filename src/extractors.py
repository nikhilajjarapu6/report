import re
import fitz  
from collections import defaultdict
import pandas as pd
import pdfplumber
import tabula
from utils.cleaners import clean_page_text, remove_header_text


def extract_text(path: str):
    """Extract text that contains 'PATIENT DETAILS' from the PDF."""
    try:
        doc = fitz.open(path)
    except Exception as e:
        print(f"[ERROR] Unable to open PDF: {path}. Reason: {e}")
        return ""

    text = ""
    try:
        for page in doc:
            try:
                page_text = page.get_text("text")
                if re.search(r'PATIENT DETAILS', page_text, re.IGNORECASE):
                    text += page_text
            except Exception as pe:
                print(f"[WARNING] Failed to read page {page.number}: {pe}")
    finally:
        doc.close()

    return text


def extract_text_in_order(pdf_path: str):
    """Extract all text while preserving logical reading order."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[ERROR] Failed to open PDF: {pdf_path}. Reason: {e}")
        return "", "", "", "", "", ""

    all_text = ""
    patient_demographics = ""
    discharge_text = ""
    medication = ""
    test_data = ""
    follow_up = ""

    inside_discharge = False
    inside_tests = False

    try:
        for page in doc:
            try:
                blocks = page.get_text("blocks")
                blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
                extracted_text = "\n".join(b[4].strip() for b in blocks if b[4].strip())

                page_text = clean_page_text(extracted_text)
                normalized = re.sub(r"\s+", " ", page_text)

                # === Categorize text sections ===
                if re.search(r'PATIENT DETAILS', page_text, re.IGNORECASE) or \
                   re.search(r'PRESENT HISTORY', page_text, re.IGNORECASE):
                    patient_demographics += page_text 

                elif re.search(r"CONDITION AT THE TIME OF DISCHARGE", page_text, re.IGNORECASE):
                    discharge_text += page_text + "\n\n"

                if re.search(r"I\s*P\s*[\s\-]*Investigations", page_text, re.IGNORECASE) or \
                   re.search(r"IP Investigations", page_text, re.IGNORECASE):
                    inside_tests = True

                if inside_tests:
                    test_data += page_text + "\n"
                    if re.search(r"ACKNOWLEDGEMENT|SIGNATURE", page_text, re.IGNORECASE):
                        inside_tests = False

                if re.search(r"DISCHARGE ADVICE", page_text, re.IGNORECASE):
                    inside_discharge = True

                if inside_discharge:
                    medication += page_text
                    if re.search(
                        r"(SURGICAL\s+GASTRO\s+REVIEW|OTHER\s+INSTRUCTIONS|INVESTIGATIONS\s+DONE|FOLLOW\s+UP)",
                        normalized,
                        re.IGNORECASE
                    ):
                        inside_discharge = False
                        continue
                else:
                    all_text += page_text + "\n"

            except Exception as pe:
                print(f"[WARNING] Failed to process page {page.number}: {pe}")

    finally:
        doc.close()

    return (
        all_text.strip(),
        patient_demographics.strip(),
        discharge_text.strip(),
        medication.strip(),
        test_data.strip(),
        follow_up.strip(),
    )


TEST_NAMES = [
    "COMPLETE BLOOD COUNT",
    "COMPLETE URINE EXAMINATION",
    "CREATININE",
    "ELECTROLYTES",
    "BLOOD UREA",
    "LIVER FUNCTION TEST WITH PROTEINS",
    "PRO CALCITONIN",
    "ARTERIAL BLOOD GASES \\(ABG\\)",
    "SERUM ALBUMIN",
    "FLUID CULTURE & SENSITIVITY",
    "TACROLIMUS -",
    "X-RAY",
    "BRONCHIAL WASH-FUNGAL STAIN",
    "BRONCHIAL WASH-GRAMS STAIN",
    "GENE-XPERT"
]

TEST_HEADER = re.compile(
    r"(?P<test>" + "|".join(TEST_NAMES) + r")",
    re.IGNORECASE
)

DATE_TIME = re.compile(
    r"(?P<date>\d{1,2}-\d{1,2}-\d{4})\s+(?P<time>\d{1,2}:\d{2})\s*(?:AM|PM)?",
    re.IGNORECASE
)

escaped_tests = [re.escape(name) for name in TEST_NAMES]

HEADER_PATTERN = re.compile(
    rf"(?P<test>{'|'.join(escaped_tests)})\s*[-:]\s*(?P<date>\d{{1,2}}-\d{{1,2}}-\d{{4}})(?:\s+(?P<time>\d{{1,2}}:\d{{2}}))?",
    re.IGNORECASE
)


def extract_all_tests(all_text: str):
    """Extract all test sections with name, date/time, and parameters."""
    sections = []
    try:
        matches = list(TEST_HEADER.finditer(all_text))
        for i, match in enumerate(matches):
            test_name = match.group("test").strip().upper()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(all_text)
            chunk = all_text[start:end].strip()

            date, time = None, None
            if dt := DATE_TIME.search(chunk):
                date = dt.group("date")
                time = dt.group("time")

            params = extract_parameters(chunk)
            sections.append({
                "test_name": test_name,
                "date": date,
                "time": time,
                "parameters": params
            })
    except Exception as e:
        print(f"[ERROR] Failed to extract test sections: {e}")

    return sections


def extract_parameters(chunk: str):
    """Extract parameters for one test section."""
    params = {}
    try:
        lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]
        current_param = None
        param_counter = defaultdict(int)

        multi_param_pattern = re.compile(
            r"([A-Z0-9\+\-]+)\s+([\d.]+\s*[a-zA-Z/%]*)\s+([\d.]+\s*-\s*[\d.]+\s*[a-zA-Z/%]*)"
        )

        for line in lines:
            if re.fullmatch(r"(Parameter|Result|Normal Range)", line, re.I):
                continue

            if re.match(r"^[A-Z]", line) and not re.search(r"\d", line):
                current_param = line.upper()
                param_counter[current_param] += 1
                if param_counter[current_param] > 1:
                    current_param = f"{current_param}_{param_counter[current_param]}"
                params[current_param] = {}

            else:
                multi_matches = multi_param_pattern.findall(line)
                if multi_matches:
                    for name, value, ref_range in multi_matches:
                        params[name.upper()] = {
                            "value": value.strip(),
                            "reference_range": ref_range.strip(),
                        }
                elif current_param:
                    if "value" not in params[current_param]:
                        params[current_param]["value"] = line.strip()
                    else:
                        params[current_param]["value"] += " " + line.strip()

    except Exception as e:
        print(f"[WARNING] Parameter extraction failed: {e}")

    return params


def extract_tables(pdf):
    """Extract tables using tabula and pdfplumber."""
    try:
        tables = tabula.read_pdf(pdf, pages='1-10', multiple_tables=True)
        with pdfplumber.open(pdf) as file:
            print(file.lines)
        return tables
    except Exception as e:
        print(f"[ERROR] Table extraction failed: {e}")
        return []
