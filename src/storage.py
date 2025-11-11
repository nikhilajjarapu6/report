import pandas as pd
import os
import json

def save_to_csv(data: dict | list[dict],file_name: str,output_dir=r"D:\Nikhil\python\report_analysis\data\processed",overwrite: bool = True):

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, file_name)

    # Convert single dict to list for consistency
    if isinstance(data, dict):
        df = pd.DataFrame([data])  #single dict
    else:
        df = pd.DataFrame(data)    #multiple dict
     # 🔒 Encode complex types (lists/dicts) into JSON strings
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x
        )

    if overwrite or not os.path.exists(file_path):
        # Replace existing file
        df.to_csv(file_path, index=False)
        print(f"🆕 File overwritten → {file_path}")
    else:
        # Append to existing
        df.to_csv(file_path, mode='a', header=False, index=False)
        print(f"➕ Data appended → {file_path}")


def save_to_json(
    data: dict | list[dict],
    file_name: str,
    output_dir=r"D:\Nikhil\python\report_analysis\data\processed",
    overwrite: bool = True
):
    os.makedirs(output_dir, exist_ok=True)
    file = os.path.join(output_dir, file_name)

    # Normalize data to DataFrame
    df = pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)

    # Save new file or overwrite
    if overwrite or not os.path.exists(file):
        df.to_json(file, orient="records", indent=4, force_ascii=False)
        print(f"✅ JSON overwritten: {file}")
    else:
        old = pd.read_json(file, orient="records")
        new_df = pd.concat([old, df], ignore_index=True)
        new_df.to_json(file, orient="records", indent=4, force_ascii=False)
        print(f"➕ Data appended → {file}")
