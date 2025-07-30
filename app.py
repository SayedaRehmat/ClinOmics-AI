 # app.py

import streamlit as st
import requests
import pandas as pd
from fpdf import FPDF
import tempfile
import os

BASE_API = "http://localhost:10000"

st.set_page_config(page_title="ClinOmics AI Pro", layout="centered")
st.title("🧬 ClinOmics AI Pro")

st.markdown("### AI-powered mutation analysis, drug matching, and trial insights")

gene = st.text_input("Enter Gene Symbol (e.g., TP53, BRCA1)").strip().upper()

def safe_text(text):
    return str(text).encode('latin1', 'ignore').decode('latin1')

if gene:
    # 1. Fetch Expression
    expr = requests.get(f"{BASE_API}/expression/{gene}").json()
    # 2. Fetch Mutation
    muts = requests.get(f"{BASE_API}/mutation/{gene}").json()
    # 3. Fetch Drugs
    drugs = requests.get(f"{BASE_API}/drugs/{gene}").json()
    # 4. Fetch Trials
    trials = requests.get(f"{BASE_API}/trials/{gene}").json()

    # --- Show Expression
    if "expression" in expr and isinstance(expr["expression"], list):
        st.subheader("📊 Gene Expression")
        df_expr = pd.DataFrame(expr["expression"])
        st.dataframe(df_expr)
    else:
        st.error(expr.get("error", "No expression data."))

    # --- Show Mutations
    if "mutations" in muts:
        st.subheader("🧬 Mutations")
        df_muts = pd.DataFrame(muts["mutations"])
        st.dataframe(df_muts)
    else:
        st.error(muts.get("error", "No mutation data."))

    # --- Show Drug Matches
    if "drugs" in drugs:
        st.subheader("💊 Drug Matches")
        df_drugs = pd.DataFrame(drugs["drugs"])
        st.dataframe(df_drugs)
    else:
        st.error(drugs.get("error", "No drug data."))

    # --- Show Clinical Trials
    if "trials" in trials:
        st.subheader("🏥 Clinical Trials")
        df_trials = pd.DataFrame(trials["trials"])
        st.dataframe(df_trials)
    else:
        st.error(trials.get("error", "No clinical trial data."))

    # --- PDF Report
    if st.button("📥 Download Report as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"ClinOmics Report: {gene}", ln=True, align="C")

        def add_section(title, df):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt=safe_text(title), ln=True)
            pdf.set_font("Arial", '', 10)
            for idx, row in df.iterrows():
                row_data = ', '.join(f"{col}: {safe_text(str(val))}" for col, val in row.items())
                pdf.multi_cell(0, 8, txt=row_data)
            pdf.ln(5)

        if "expression" in expr and isinstance(expr["expression"], list):
            add_section("Expression Data", pd.DataFrame(expr["expression"]))
        if "mutations" in muts:
            add_section("Mutations", pd.DataFrame(muts["mutations"]))
        if "drugs" in drugs:
            add_section("Drug Matches", pd.DataFrame(drugs["drugs"]))
        if "trials" in trials:
            add_section("Clinical Trials", pd.DataFrame(trials["trials"]))

        # Save + download
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                st.download_button("⬇️ Download PDF", data=f, file_name=f"{gene}_ClinOmics_Report.pdf", mime="application/pdf")
            os.unlink(tmpfile.name)
