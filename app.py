import streamlit as st
import requests
import pandas as pd
from fpdf import FPDF
import tempfile
import os

# ------------------- CONFIG -------------------
st.set_page_config(page_title="ClinOmics AI Pro", layout="centered")
st.title("🧬 ClinOmics AI Pro: Gene, Drug & Clinical Trial Insights")
st.markdown("**AI-powered mutation analysis, drug discovery, and clinical trial insights with trusted, open data sources.**")

# ------------------- UTILITIES -------------------
def safe_text(text):
    return str(text).encode('latin1', 'ignore').decode('latin1')

# ------------------- API FUNCTIONS -------------------

# ✅ 1. CLINVAR
def fetch_clinvar_data(gene: str):
    try:
        url = "https://clinicaltrials.gov/api/v2"
        params = {"terms": gene, "maxList": 10}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        variants = data[3] if len(data) > 3 else []
        if not variants:
            return [{"error": "No ClinVar data found."}]
        return [{"VariantID": v[0], "Description": v[1]} for v in variants]
    except Exception as e:
        return [{"error": f"ClinVar API failed: {e}"}]

# ✅ 2. DGIdb (Drug–Gene Interactions)
def fetch_drug_data(gene: str):
    try:
        url = f"https://dgidb.org/api/v2/interactions.json?genes={gene}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        interactions = data.get("matchedTerms", [])[0].get("interactions", [])
        if not interactions:
            return [{"error": "No drug interactions found in DGIdb."}]
        
        return [
            {
                "Drug": d.get("drugName", "N/A"),
                "Interaction Type": d.get("interactionTypes", ["N/A"])[0],
                "Source": d.get("source", "N/A")
            }
            for d in interactions
        ]
    except Exception as e:
        return [{"error": f"DGIdb API failed: {e}"}]

# ✅ 3. ClinicalTrials.gov API (New version)
def fetch_trials(gene: str):
    try:
        search_url = "https://clinicaltrials.gov/api/query/study_fields"
        params = {
            "expr": gene,
            "fields": "NCTId,BriefTitle,Condition,LocationCountry",
            "min_rnk": 1,
            "max_rnk": 10,
            "fmt": "json"
        }
        r = requests.get(search_url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        trials = data.get("StudyFieldsResponse", {}).get("StudyFields", [])
        if not trials:
            return [{"error": "No clinical trials found."}]
        return [
            {
                "Trial ID": t.get("NCTId", ["N/A"])[0],
                "Title": t.get("BriefTitle", ["N/A"])[0],
                "Condition": ", ".join(t.get("Condition", ["N/A"])),
                "Country": ", ".join(t.get("LocationCountry", ["N/A"]))
            }
            for t in trials
        ]
    except Exception as e:
        return [{"error": f"ClinicalTrials.gov API failed: {e}"}]

# ------------------- GENE INPUT -------------------
gene = st.text_input("🔍 Enter Gene Symbol (e.g., TP53, BRCA1)").strip().upper()
muts, drugs, trials = [], [], []

if gene:
    st.info(f"Fetching data for **{gene}**...")
    muts = fetch_clinvar_data(gene)
    drugs = fetch_drug_data(gene)
    trials = fetch_trials(gene)

# ------------------- DISPLAY RESULTS -------------------
if gene:
    if muts and "error" not in muts[0]:
        st.subheader("🧬 Mutation Info (ClinVar)")
        st.table(pd.DataFrame(muts))
    else:
        st.warning(muts[0].get("error", "No mutation data found."))

    if drugs and "error" not in drugs[0]:
        st.subheader("💊 Drug Matches (DGIdb)")
        st.table(pd.DataFrame(drugs))
    else:
        st.warning(drugs[0].get("error", "No drug matches found."))

    if trials and "error" not in trials[0]:
        st.subheader("🏥 Clinical Trials (ClinicalTrials.gov)")
        st.table(pd.DataFrame(trials))
    else:
        st.warning(trials[0].get("error", "No clinical trials found."))

# ------------------- PDF REPORT -------------------
def create_pdf_report(gene, muts, drugs, trials):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=safe_text(f"ClinOmics Report: {gene}"), ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Mutation Info (ClinVar)", ln=True)
    pdf.set_font("Arial", '', 11)
    for mut in muts:
        for k, v in mut.items():
            pdf.cell(0, 8, txt=safe_text(f"{k}: {v}"), ln=True)
        pdf.ln(2)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Drug Matches (DGIdb)", ln=True)
    pdf.set_font("Arial", '', 11)
    for drug in drugs:
        for k, v in drug.items():
            pdf.cell(0, 8, txt=safe_text(f"{k}: {v}"), ln=True)
        pdf.ln(2)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Clinical Trials", ln=True)
    pdf.set_font("Arial", '', 11)
    for trial in trials:
        for k, v in trial.items():
            pdf.cell(0, 8, txt=safe_text(f"{k}: {v}"), ln=True)
        pdf.ln(2)

    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Generated by ClinOmics AI Pro", ln=True, align='C')
    return pdf

if gene and muts and "error" not in muts[0]:
    if st.button("📅 Download PDF Report"):
        pdf = create_pdf_report(gene, muts, drugs, trials)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=f,
                    file_name=f"{gene}_ClinOmics_Report.pdf",
                    mime="application/pdf"
                )
            os.unlink(tmpfile.name)

# ------------------- FOOTER -------------------
st.markdown("""
<hr style='border: 1px solid #ddd;'>
<div style="text-align: center; color: gray;">
    Created by <b>Sayeda Rehmat</b> — Founder, <i>ClinOmics AI Pro</i>
</div>
""", unsafe_allow_html=True)
