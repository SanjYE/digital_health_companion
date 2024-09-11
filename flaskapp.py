from flask import Flask, request, jsonify, render_template, session
import json
import openai
from openai import OpenAI
from difflib import get_close_matches

app = Flask(__name__)
app.secret_key = 'your_secret_key'


client = OpenAI(
    api_key="**",
)

with open('data.json', 'r') as file:
    disease_drug_data = json.load(file)

disease_synonyms_cache = {}

def chat_with_gpt(messages):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    response_message = response.choices[0].message.content
    return response_message

def get_disease_synonyms(disease_name):
    if disease_name in disease_synonyms_cache:
        return disease_synonyms_cache[disease_name]

    prompt = f"Provide a list of common synonyms or alternative names for the disease '{disease_name}' in medical context."

    messages = [
        {"role": "system", "content": "You are a medical expert."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.7,
        )
        synonym_list = response.choices[0].message.content.split(", ")
        synonym_list = [syn.strip().lower() for syn in synonym_list]
        
        disease_synonyms_cache[disease_name.lower()] = synonym_list
        return synonym_list
    except Exception as e:
        print(f"Error fetching synonyms for {disease_name}: {str(e)}")
        return []

def find_closest_disease(disease):
    diseases = list(disease_drug_data.keys())
    disease_lower = disease.lower()

  
    synonyms = get_disease_synonyms(disease)
    synonyms.append(disease_lower)

    for main_disease in diseases:
        if main_disease.lower() in synonyms:
            return main_disease

    closest_matches = get_close_matches(disease_lower, [d.lower() for d in diseases], n=1, cutoff=0.6)
    if closest_matches:
        return next(d for d in diseases if d.lower() == closest_matches[0])

    return None

def get_top_drug_recommendations(disease, top_n=10):
    closest_disease = find_closest_disease(disease)

    if closest_disease:
        drugs = disease_drug_data[closest_disease]
        sorted_drugs = sorted(drugs, key=lambda x: float(x['success_rate']), reverse=True)
        top_drugs = sorted_drugs[:top_n]
        recommendations = [f"{drug['drug_name']}" for drug in top_drugs]
        return closest_disease, "\n".join(recommendations)
    return None, "No specific drug recommendations found for this condition."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def get_symptoms():
    symptom_input = request.form['symptoms']
    
   
    if 'messages' not in session:
        session['messages'] = [
            {"role": "system", "content": "You are a medical chatbot. Ask about symptoms and determine potential diseases."},
            {"role": "assistant", "content": "Hello! What symptoms are you experiencing?"}
        ]

  
    session['messages'].append({"role": "user", "content": symptom_input})

    response = chat_with_gpt(session['messages'])
    session['messages'].append({"role": "assistant", "content": response})

    if "Potential disease:" in response:
        potential_disease = response.split("Potential disease:")[-1].strip()
        closest_disease, drug_recommendations = get_top_drug_recommendations(potential_disease)

 
        if closest_disease:
            response += f"\nBased on the potential diagnosis of {potential_disease}, similar to {closest_disease}, here are some drug recommendations:\n{drug_recommendations}"
        else:
            response += f"\nBased on the potential diagnosis of {potential_disease}, no specific drug recommendations were found."

    
    return jsonify({
        'response': response
    })

if __name__ == '__main__':
    app.run(debug=True)
