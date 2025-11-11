from src.extractors import extract_text, extract_text_in_order,extract_tables
from src.parsers import extract_patient_parse, demographics_parse
from src.storage import save_to_csv,save_to_json
import src.parsers as par
import json


def main():
    pdf_path = r"D:\Nikhil\python\report_analysis\data\raw\KIMS _ EHR (19).pdf"

    # Extract all sections
    all_text, patient_demographics, discharge_text, medication_text,test_data,follow_up= extract_text_in_order(pdf_path)



    patient = extract_patient_parse(patient_demographics)
    diagnosis = demographics_parse(patient_demographics)
    discharge = par.discharge_condition_parse(discharge_text)
    medication=par.medication_parse(medication_text)
    # full_test_data=par.test_reports_parse(test_data)
    # print(patient,diagnosis,discharge,medication)
    # print(json.dumps(patient,indent=2))
    print(json.dumps(diagnosis,indent=2))
    # print(json.dumps(discharge,indent=2))
    # print(json.dumps(medication,indent=2))

    patient_json=json.dumps(patient,indent=2)
    diagnosis_json=json.dumps(diagnosis,indent=2)
    discharge_json=json.dumps(discharge,indent=2)
    medication_json=json.dumps(medication,indent=2)
    # print(patient_json,diagnosis_json,discharge_json,medication_json)
 
    

    # Save outputs
    # save_to_csv(diagnosis, "diagnosis.csv")
    # save_to_csv(patient, "patient.csv")
    # save_to_csv(discharge, "discharge.csv")

    # save_to_json(diagnosis, "diagnosis.json")
    # save_to_json(patient, "patient.json")
    # save_to_json(discharge, "discharge.json")
    # save_to_json(medication,"medication.json")
    # save_to_json(test_data,"test_data.json")

if __name__ == "__main__":
    main()

