 import streamlit as st
import requests
import pandas as pd
from fpdf import FPDF
import tempfile
import os

BASE_API = "https://YOUR-RENDER-API-URL.onrender.com"

st.set_page_config(page_title="ClinOmics AI", layout="centered")
st.title("🔬 ClinOmics AI Pro")

gene = st.text_input("Enter Gene Symbol (e.g. TP53)").strip().upper()

def safe_text(txt):
    return str(txt).encode('latin1', 'ignore').decode('latin1')

if gene:
    expr, muts, drugs = {}, [], []
    try:
        expr = requests.get(f"{BASE_API}/expression/{gene}").json()
        muts = requests.get(f"{BASE_API}/mutation/{gene}").json()
        drugs = requests.get(f"{BASE_API}/drugs/{gene}").json()
    except Exception as e:
        st.error(f"API Error: {e}")

    if "error" not in expr:
        st.subheader("📊 Expression Data")
        df_expr = pd.DataFrame(expr.items(), columns=["Sample", "Expression"])
        st.dataframe(df_expr)
    else:
        st.warning(expr.get("error"))

    if muts and "error" not in muts[0]:
        st.subheader("🧬 Mutations")
        st.table(pd.DataFrame(muts))
    else:
        st.warning(muts[0].get("error"))

    if drugs and "error" not in drugs[0]:
        st.subheader("💊 Drug Matches")
        st.table(pd.DataFrame(drugs))
    else:
        st.warning(drugs[0].get("error"))

    if st.button("📄 Download PDF Report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt=safe_text(f"ClinOmics AI Report: {gene}"), ln=True, align='C')
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Expression Data", ln=True)
        pdf.set_font("Arial", '', 12)
        for k, v in expr.items():
            pdf.cell(0, 10, txt=safe_text(f"{k}: {v}"), ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Mutation Info", ln=True)
        pdf.set_font("Arial", '', 12)
        for row in muts:
            for k, v in row.items():
                pdf.cell(0, 10, txt=safe_text(f"{k}: {v}"), ln=True)
            pdf.ln(3)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Drug Matches", ln=True)
        pdf.set_font("Arial", '', 12)
        for row in drugs:
            for k, v in row.items():
                pdf.cell(0, 10, txt=safe_text(f"{k}: {v}"), ln=True)
            pdf.ln(3)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("⬇️ Download PDF", f, f"{gene}_report.pdf", mime="application/pdf")
            os.unlink(tmp.name)
