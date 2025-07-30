 # backend/api.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="ClinOmics AI - Real API")

# Allow frontend (Streamlit) to access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "ClinOmics AI API"}

@app.get("/expression/{gene}")
def get_expression(gene: str):
    try:
        url = f"https://rest.ensembl.org/expression/id/{gene}?content-type=application/json"
        r = requests.get(url, headers={"Content-Type": "application/json"})
        return r.json()
    except Exception as e:
        return {"error": f"Expression API failed: {str(e)}"}

@app.get("/mutation/{gene}")
def get_mutation(gene: str):
    try:
        url = f"https://myvariant.info/v1/query?q={gene}&fields=all"
        r = requests.get(url)
        return r.json()
    except Exception as e:
        return {"error": f"Mutation API failed: {str(e)}"}

@app.get("/drugs/{gene}")
def get_drugs(gene: str):
    try:
        url = f"https://dgidb.org/api/v2/interactions.json?genes={gene}"
        r = requests.get(url)
        data = r.json()
        return data.get("matchedTerms", [{}])[0].get("interactions", [])
    except Exception as e:
        return {"error": f"DGIdb API failed: {str(e)}"}

@app.get("/trials/{gene}")
def get_trials(gene: str):
    try:
        url = f"https://clinicaltrials.gov/api/query/study_fields?expr={gene}&fields=NCTId,BriefTitle,Condition,LocationCountry&min_rnk=1&max_rnk=10&fmt=json"
        r = requests.get(url)
        return r.json().get("StudyFieldsResponse", {}).get("StudyFields", [])
    except Exception as e:
        return {"error": f"ClinicalTrials API failed: {str(e)}"}
