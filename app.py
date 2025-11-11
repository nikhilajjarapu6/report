from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from src.extractors import extract_text_in_order
from src.parsers import extract_patient_parse, demographics_parse,discharge_condition_parse,medication_parse


app = FastAPI(title="Patient Report API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = r"D:\Nikhil\python\report_analysis\index.html"
PDF_PATH = r"D:\Nikhil\python\report_analysis\data\raw\KIMS _ EHR (19).pdf"



patient_json = None
diagnosis_json = None
discharge_json = None
medication_json = None



def load_pdf_and_extract():
    """Extract text and structured JSONs from the given PDF."""
    global patient_json, diagnosis_json, discharge_json, medication_json

    # Extract sections
    all_text, patient_demographics, discharge_text, medication_text, test_data, follow_up = extract_text_in_order(PDF_PATH)

    # Parse individual sections
    patient = extract_patient_parse(patient_demographics)
    diagnosis = demographics_parse(patient_demographics)
    discharge = discharge_condition_parse(discharge_text)
    medication =medication_parse(medication_text)

    # Convert to JSON (or keep as dicts if you prefer)
    patient_json = json.loads(json.dumps(patient, indent=2))
    diagnosis_json = json.loads(json.dumps(diagnosis, indent=2))
    discharge_json = json.loads(json.dumps(discharge, indent=2))
    medication_json = json.loads(json.dumps(medication, indent=2))

# ------------------- FastAPI Events -------------------

@app.on_event("startup")
def startup_event():
    """Load the PDF and parse data when the app starts."""
    print("Extracting PDF data...")
    load_pdf_and_extract()
    print("✅ Extraction complete. Data ready for API use.")



@app.get("/report_home", response_class=HTMLResponse)
def open_html():
    with open(FRONTEND_PATH, encoding="utf-8") as file:
        return file.read()



@app.get("/")
def home():
    return {"message": "Patient Report API is running 🚀"}


@app.get("/patients")
def get_patient_details():
    if patient_json:
        return JSONResponse(content=patient_json, status_code=200)
    return JSONResponse(content={"error": "Patient data not available"}, status_code=404)

@app.get("/diagnosis")
def get_diagnosis():
    if diagnosis_json:
        return JSONResponse(content=diagnosis_json, status_code=200)
    return JSONResponse(content={"error": "Diagnosis data not available"}, status_code=404)

@app.get("/discharge")
def get_discharge_condition():
    if discharge_json:
        return JSONResponse(content=discharge_json, status_code=200)
    return JSONResponse(content={"error": "Discharge data not available"}, status_code=404)

@app.get("/medication")
def get_medication():
    if medication_json:
        return JSONResponse(content=medication_json, status_code=200)
    return JSONResponse(content={"error": "Medication data not available"}, status_code=404)

