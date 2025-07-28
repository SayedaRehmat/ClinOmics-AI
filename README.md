# ClinOmics AI
ClinOmics AI is an AI-powered clinical genomics tool that fetches mutation pathogenicity, drug interactions, and clinical trials to generate professional PDF reports.

## Features
- **ClinVar Pathogenicity:** Analyze gene mutations.
- **Drug Interactions (DGIdb):** Find drugs targeting specific genes.
- **Clinical Trials:** Fetch current trial data from ClinicalTrials.gov.
- **PDF Reports:** Generate professional downloadable reports.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/ClinOmics-AI.git
   cd ClinOmics-AI
   ```
2. Create a virtual environment (Python 3.11 recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On Mac/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deployment on Streamlit Cloud
1. Push this project to GitHub.
2. Go to [Streamlit Cloud](https://share.streamlit.io/).
3. Click **New App** and link your repository.
4. Select `app.py` as the entry point.
5. Deploy and share your public URL!

## Requirements
See `requirements.txt`.

## Author
**ClinOmics AI** — Bioinformatics SaaS MVP by Syeda Rehmat.
