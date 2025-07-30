from fastapi import FastAPI
import pandas as pd

app = FastAPI(title="ClinOmics API")

expr_df = pd.read_csv("data/expression.csv")
mut_df = pd.read_csv("data/mutations.csv")
drug_df = pd.read_csv("data/dgidb_drugs.csv")

@app.get("/")
def home():
    return {"message": "Welcome to ClinOmics API"}

@app.get("/expression/{gene}")
def expression(gene: str):
    gene = gene.upper()
    row = expr_df[expr_df["Gene"].str.upper() == gene]
    if row.empty:
        return {"error": "No expression data found"}
    return row.iloc[0][1:].to_dict()

@app.get("/mutation/{gene}")
def mutation(gene: str):
    gene = gene.upper()
    df = mut_df[mut_df["Gene"].str.upper() == gene]
    if df.empty:
        return [{"error": "No mutation data found"}]
    return df.to_dict(orient="records")

@app.get("/drugs/{gene}")
def drugs(gene: str):
    gene = gene.upper()
    df = drug_df[drug_df["Gene"].str.upper() == gene]
    if df.empty:
        return [{"error": "No drug data found"}]
    return df[["Drug", "Interaction"]].to_dict(orient="records")
