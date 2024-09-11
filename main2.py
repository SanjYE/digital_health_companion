import json
import openai
import os
from openai import OpenAI
from difflib import get_close_matches

client = OpenAI(
    api_key="**",  
)

disease_synonyms_cache = {}

with open('data.json', 'r') as file:
    disease_drug_data = json.load(file)

def chat_with_gpt(messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
      
        top_drugs = sorted_drugs[:10]
        recommendations = [f"{drug['drug_name']}" for drug in top_drugs]
        return closest_disease, "\n".join(recommendations)
    return None, "No specific drug recommendations found for this condition."

def symptom_checker():
    messages = [
        {"role": "system", "content": "You are a medical chatbot. Ask about symptoms and determine potential diseases. Be empathetic and professional. When you determine a disease, clearly state it as 'Potential disease: [disease name]' at the end of your message. Make sure you only mention the disease's general name. for example if it is Common Cold(viral respiratory infection) just state Common Cold. DO NOT state specifics."},
        {"role": "assistant", "content": "Hello! I'm here to help you identify potential health issues based on your symptoms. What symptoms are you experiencing?"}
    ]
    
    print("Chatbot: " + messages[-1]["content"])

    potential_disease = None

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Chatbot: Thank you for using the symptom checker. Remember, this is not a substitute for professional medical advice. Please consult a doctor for accurate diagnosis and treatment.")
            break

        messages.append({"role": "user", "content": user_input})
        response = chat_with_gpt(messages)
        messages.append({"role": "assistant", "content": response})
        print("Chatbot:", response)

     
        if "Potential disease:" in response:
            potential_disease = response.split("Potential disease:")[-1].strip()
            closest_disease, drug_recommendations = get_top_drug_recommendations(potential_disease)
            
            if closest_disease:
                print(f"\nChatbot: Based on the potential diagnosis of {potential_disease}, which seems similar to {closest_disease} in our database, here are the best drugs commonly used for treatment, with the highest success rates")
            else:
                print(f"\nChatbot: Based on the potential diagnosis of {potential_disease}, here's what I found:")
            
            print(drug_recommendations)
            print("\nChatbot: Please note that this information is for educational purposes only. Always consult with a healthcare professional before starting or changing any medication.")
            break

if __name__ == "__main__":
    symptom_checker()
