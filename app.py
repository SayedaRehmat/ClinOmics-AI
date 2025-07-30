 # app.py
import streamlit as st
import requests
import json
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="ClinOmics AI Pro", layout="wide")
st.title("ClinOmics AI Pro")
st.markdown("AI-powered gene mutation analysis, drug discovery, and clinical trial insights.")

def fetch_expression(gene):
    try:
        res = requests.get(f"https://autobiox-api.onrender.com/expression/{gene}", timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def fetch_mutation(gene):
    try:
        res = requests.get(f"https://autobiox-api.onrender.com/mutation/{gene}", timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def fetch_trials_v2(gene):
    try:
        res = requests.get("https://clinicaltrials.gov/api/v2/studies", params={
          "query.cond": "cancer",
          "query.term": gene,
          "fields": "NCTId,BriefTitle,Condition,LocationCountry",
          "pageSize": 5,
          "format": "json"
        }, timeout=10)
        res.raise_for_status()
        data = res.json()
        return [
            {"Trial ID": s["protocolSection"]["identificationModule"]["nctId"],
             "Title": s["protocolSection"]["identificationModule"].get("officialTitle", "")}
            for s in data.get("studies", [])
        ]
    except Exception as e:
        return [{"error": f"ClinicalTrials v2 API failed: {e}"}]

def fetch_drug_graphql(gene):
    query = '''
    {
      matchedTerms(genes:["%s"]) {
        geneName
        interactions {
          drugName
          interactionTypes
          sources { source }
        }
      }
    }''' % gene
    try:
        r = requests.post("https://dgidb.org/api/graphql", json={"query": query}, timeout=10)
        r.raise_for_status()
        result = r.json()
        interactions = result.get("data", {}).get("matchedTerms", [])[0].get("interactions", [])
        return interactions if interactions else [{"note": "No drug matches found."}]
    except Exception as e:
        return [{"error": f"DGIdb GraphQL failed: {e}"}]

def generate_pdf(gene, expression, mutation, drugs, trials):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"Gene Report: {gene}", ln=True, align="C")

    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "\nGene Expression", ln=True)
    pdf.set_font("Arial", size=10)
    for k, v in expression.items():
        pdf.cell(200, 8, f"{k}: {v}", ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "\nMutations", ln=True)
    pdf.set_font("Arial", size=10)
    for row in mutation:
        line = ', '.join(f"{k}: {v}" for k, v in row.items())
        pdf.multi_cell(200, 8, line)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "\nDrug Matches", ln=True)
    pdf.set_font("Arial", size=10)
    for drug in drugs:
        line = ', '.join(f"{k}: {v}" for k, v in drug.items())
        pdf.multi_cell(200, 8, line)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "\nClinical Trials", ln=True)
    pdf.set_font("Arial", size=10)
    for trial in trials:
        line = ', '.join(f"{k}: {v}" for k, v in trial.items())
        pdf.multi_cell(200, 8, line)

    filename = f"{gene}_report.pdf"
    pdf.output(filename)
    return filename

# UI
with st.form("search_form"):
    gene_input = st.text_input("Enter Gene Symbol (e.g. TP53):")
    submitted = st.form_submit_button("Search")

if submitted and gene_input:
    gene = gene_input.strip().upper()
    st.info(f"Searching for gene: {gene}")

    expr = fetch_expression(gene)
    mut = fetch_mutation(gene)
    drug = fetch_drug_graphql(gene)
    trials = fetch_trials_v2(gene)

    st.subheader("Gene Expression")
    if "error" in expr:
        st.warning(expr["error"])
    else:
        st.json(expr["expression"])

    st.subheader("Mutations")
    if mut and isinstance(mut, list):
        st.write(pd.DataFrame(mut))
    else:
        st.warning("No mutation data found.")

    st.subheader("Drug Matches")
    st.write(drug)

    st.subheader("Clinical Trials")
    st.write(pd.DataFrame(trials))

    if st.button("Download PDF Report"):
        pdf_path = generate_pdf(gene, expr["expression"], mut, drug, trials)
        with open(pdf_path, "rb") as f:
            st.download_button("Download Report", f, file_name=pdf_path)
