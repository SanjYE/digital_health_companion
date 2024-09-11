import csv
import json
from collections import defaultdict

disease_data = defaultdict(list)


csv_file_path = "drugs_for_common_treatments.csv"
json_file_path = "data.json"


with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
 
    for row in reader:
        disease = row["medical_condition"]
        drug = row["drug_name"]
        success_rate = row["rating"]
        
       
        if success_rate.strip():  
            disease_data[disease].append({
                "drug_name": drug,
                "success_rate": success_rate
            })

disease_data = {disease: drugs for disease, drugs in disease_data.items() if drugs}


with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
    json.dump(disease_data, jsonfile, indent=4)

print(f"Filtered data successfully saved to {json_file_path}")
