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

# ------------------- API ENDPOINTS -------------------
CLINVAR_API = "https://clinicaltables.nlm.nih.gov/api/variants/v3/search"
DGIDB_API = "https://dgidb.org/api/v2/interactions.json"
TRIALS_API = "https://clinicaltrials.gov/api/v2"

# ------------------- UTILITIES -------------------
def safe_text(text):
    return str(text).encode('latin1', 'ignore').decode('latin1')

# ------------------- DATA FETCH FUNCTIONS -------------------
def fetch_clinvar_data(gene: str):
    try:
        params = {"terms": gene, "maxList": 10}
        r = requests.get(CLINVAR_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        variants = data[3] if len(data) > 3 else []
        if not variants:
            return [{"error": "No ClinVar data found."}]
        return [{"VariantID": v[0], "Description": v[1]} for v in variants]
    except Exception as e:
        return [{"error": f"ClinVar API failed: {e}"}]

def fetch_drug_data(gene: str):
    try:
        params = {"genes": gene}
        r = requests.get(DGIDB_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        interactions = data.get("matchedTerms", [])[0].get("interactions", [])
        if not interactions:
            return [{"error": "No drug interactions found in DGIdb."}]
        return [
            {"Drug": i["drugName"], "Interaction Type": i["interactionTypes"][0]}
            for i in interactions[:5]
        ]
    except Exception as e:
        return [{"error": f"DGIdb API failed: {e}"}]

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
        if not studies:
            return [{"error": "No clinical trials found."}]
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

# ------------------- INPUT SECTION -------------------
gene = st.text_input("🔍 Enter Gene Symbol (e.g., TP53, BRCA1)").strip().upper()
uploaded_file = st.file_uploader("📁 Or upload a file with gene names (.txt, .csv)", type=["txt", "csv"])

gene_list = []
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        gene_list = df.iloc[:, 0].dropna().astype(str).str.upper().tolist()
    else:
        gene_list = [line.strip().upper() for line in content.splitlines() if line.strip()]
elif gene:
    gene_list = [gene]

# ------------------- DISPLAY RESULTS -------------------
all_results = {}

for gene in gene_list:
    st.info(f"Fetching data for **{gene}**...")
    muts = fetch_clinvar_data(gene)
    drugs = fetch_drug_data(gene)
    trials = fetch_trials(gene)
    all_results[gene] = {"muts": muts, "drugs": drugs, "trials": trials}

    if muts and "error" not in muts[0]:
        st.subheader(f"🧬 Mutation Info: {gene}")
        st.table(pd.DataFrame(muts))
    else:
        st.warning(muts[0].get("error", "No mutation data found."))

    if drugs and "error" not in drugs[0]:
        st.subheader(f"💊 Drug Matches: {gene}")
        st.table(pd.DataFrame(drugs))
    else:
        st.warning(drugs[0].get("error", "No drug matches found."))

    if trials and "error" not in trials[0]:
        st.subheader(f"🏥 Clinical Trials: {gene}")
        st.table(pd.DataFrame(trials))
    else:
        st.warning(trials[0].get("error", "No clinical trials found."))

# ------------------- PDF EXPORT -------------------
def create_pdf_report(results):
    pdf = FPDF()
    for gene, data in results.items():
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt=safe_text(f"ClinOmics Report: {gene}"), ln=True, align='C')
        pdf.ln(10)

        for section, label in zip(["muts", "drugs", "trials"],
                                  ["Mutation Info", "Drug Matches", "Clinical Trials"]):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt=label, ln=True)
            pdf.set_font("Arial", '', 11)
            for item in data[section]:
                for k, v in item.items():
                    pdf.cell(0, 8, txt=safe_text(f"{k}: {v}"), ln=True)
                pdf.ln(2)
        pdf.ln(10)
    return pdf

if gene_list:
    if st.button("📥 Download PDF Report"):
        pdf = create_pdf_report(all_results)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=f,
                    file_name=f"ClinOmics_Report.pdf",
                    mime="application/pdf"
                )
            os.unlink(tmpfile.name)

# ------------------- FOOTER -------------------
st.markdown("""
<hr style='border: 1px solid #ddd;'>
<div style="text-align: center; color: gray;">
    Created by <b>Syeda Rehmat</b> — Founder, <i>ClinOmics AI Pro</i><br>
    Powered by ClinVar, DGIdb, ClinicalTrials.gov
</div>
""", unsafe_allow_html=True)
