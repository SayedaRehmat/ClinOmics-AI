from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import requests
import csv
import io

app = FastAPI(title="ClinOmics AI Pro - FastAPI Backend")

# ------------------- API ENDPOINTS -------------------
CLINVAR_API = "https://clinicaltables.nlm.nih.gov/api/variants/v3/search"
DGIDB_API = "https://dgidb.org/api/v2/interactions.json"
TRIALS_API = "https://clinicaltrials.gov/api/query/study_fields"

# ------------------- HELPERS -------------------
def fetch_clinvar_data(gene: str):
    try:
        params = {"terms": gene, "maxList": 10}
        r = requests.get(CLINVAR_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        variants = data[3] if len(data) > 3 else []
        return [{"VariantID": v[0], "Description": v[1]} for v in variants] if variants else []
    except Exception as e:
        return [{"error": f"ClinVar API failed: {e}"}]

def fetch_drug_data(gene: str):
    try:
        headers = {"Accept": "application/json"}
        params = {"genes": gene}
        r = requests.get(DGIDB_API, headers=headers, params=params, timeout=10)
        if not r.content or r.status_code != 200:
            raise ValueError("Empty response or bad status code.")

        data = r.json()
        matched = data.get("matchedTerms", [])
        if not matched or not matched[0].get("interactions"):
            raise ValueError("No DGIdb interactions.")

        interactions = matched[0]["interactions"]
        return [{"Drug": i["drugName"], "Interaction Type": ", ".join(i.get("interactionTypes", []))} for i in interactions[:5]]
    except Exception:
        return fetch_drug_data_fallback(gene)

def fetch_drug_data_fallback(gene: str):
    try:
        with open("drug_fallback.csv") as f:
            reader = csv.DictReader(f)
            return [
                {"Drug": row["Drug"], "Interaction Type": row["Interaction Type"]}
                for row in reader if row["Gene"].upper() == gene.upper()
            ] or [{"error": f"No fallback drug data for {gene}"}]
    except Exception as e:
        return [{"error": f"Fallback CSV failed: {e}"}]

def fetch_trials(gene: str):
    try:
        params = {
            "expr": gene,
            "fields": "NCTId,BriefTitle,OverallStatus,LocationCountry",
            "min_rnk": 1,
            "max_rnk": 5,
            "fmt": "json"
        }
        r = requests.get(TRIALS_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        studies = data.get("StudyFieldsResponse", {}).get("StudyFields", [])
        return [
            {
                "Trial ID": s.get("NCTId", ["N/A"])[0],
                "Title": s.get("BriefTitle", ["N/A"])[0],
                "Status": s.get("OverallStatus", ["N/A"])[0],
                "Country": ", ".join(s.get("LocationCountry", ["N/A"]))
            }
            for s in studies
        ]
    except Exception as e:
        return [{"error": f"ClinicalTrials API failed: {e}"}]

# ------------------- ROUTES -------------------
@app.post("/analyze-gene")
async def analyze_gene(payload: dict):
    gene = payload.get("gene", "").strip().upper()
    if not gene:
        return JSONResponse(content={"error": "Gene name required."}, status_code=400)

    mutations = fetch_clinvar_data(gene)
    drugs = fetch_drug_data(gene)
    trials = fetch_trials(gene)

    return {
        "gene": gene,
        "mutations": mutations,
        "drugs": drugs,
        "trials": trials
    }

@app.post("/batch-analyze")
async def batch_analyze(file: UploadFile = File(...)):
    content = await file.read()
    genes = []
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(content.decode("utf-8")))
            genes = df.iloc[:, 0].dropna().astype(str).str.upper().tolist()
        else:
            genes = [line.strip().upper() for line in content.decode("utf-8").splitlines() if line.strip()]
    except Exception as e:
        return JSONResponse(content={"error": f"File read failed: {e}"}, status_code=400)

    results = {}
    for gene in genes:
        results[gene] = {
            "mutations": fetch_clinvar_data(gene),
            "drugs": fetch_drug_data(gene),
            "trials": fetch_trials(gene)
        }
    return results
