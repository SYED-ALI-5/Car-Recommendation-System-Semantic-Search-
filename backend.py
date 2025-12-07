# app.py
import os
import re
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, abort
from flask_cors import CORS

# LangChain & Qdrant imports (keep your existing pipeline imports)
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Range
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Qdrant as LCQdrant
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate

load_dotenv()

# Config from .env
QDRANT_URL = os.getenv("QDRANT_CLOUD_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
CLEANED_CSV = os.getenv("CLEANED_CSV")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
TUNNEL_SECRET = os.getenv("TUNNEL_SECRET")
PORT = int(os.getenv("PORT", 5000))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")  # You can set to your Render URL

# Basic checks
if not QDRANT_URL or not QDRANT_API_KEY:
    print("Warning: Qdrant URL or API key not set. If using local Qdrant skip these.")
# Load CSV
if not os.path.exists(CLEANED_CSV):
    print(f"[WARN] CSV not found at {CLEANED_CSV}. Endpoints returning no sources.")
df = pd.read_csv(CLEANED_CSV, low_memory=False) if os.path.exists(CLEANED_CSV) else pd.DataFrame()

# Flask
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}})

# Qdrant client
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60.0)

# Embeddings & LLM (Ollama local)
embeddings = OllamaEmbeddings(model="nomic-embed-text")
llm = Ollama(model=OLLAMA_MODEL, temperature=0.2)

# Vectorstore
vectorstore = LCQdrant(client=qdrant_client, collection_name="Cars_Data", embeddings=embeddings)

# Prompt template
enhanced_prompt = PromptTemplate(
    template="""You are a car expert assistant. Use the following car information to answer the user's question accurately and comprehensively.

Context Information:
{summaries}

Instructions:
- Provide specific details about each relevant vehicle
- Be precise with numbers and facts
- If multiple cars match, list them clearly
- Don't give duplicate answers
- Don't give me irrelevant answers

Question: {question}

Detailed Answer:""",
    input_variables=["summaries", "question"]
)

def funcChain(retriever):
    return RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        chain_type_kwargs={"prompt": enhanced_prompt}
    )

# Filter builder (same as your existing function)
def build_filter(query: str):
    query = (query or "").lower()
    conditions = []
    # YEAR
    year_range = re.search(r"(?:between|from)\s+(20[0-9]{2})\s+(?:and|to)\s+(20[0-9]{2})", query)
    if year_range:
        conditions.append(FieldCondition(key="metadata.year", range=Range(gte=int(year_range.group(1)), lte=int(year_range.group(2)))))
    else:
        year_match = re.search(r"\b(20[0-9]{2})\b", query)
        if year_match:
            conditions.append(FieldCondition(key="metadata.year", match={"value": int(year_match.group(1))}))
    # PRICE
    price_range = re.search(r"(?:between|from)\s+([\d,]+)\s+(?:and|to)\s+([\d,]+)", query)
    if price_range:
        conditions.append(FieldCondition(key="metadata.latest_price", range=Range(gte=float(price_range.group(1).replace(',','')), lte=float(price_range.group(2).replace(',','')))))
    else:
        price_match = re.search(r"(?:under|below|less than)\s+([\d,]+)", query)
        if price_match:
            conditions.append(FieldCondition(key="metadata.latest_price", range=Range(lt=float(price_match.group(1).replace(',','')))))
    # MILEAGE
    mileage_range = re.search(r"(?:between|from)\s+([\d,]+)\s+(?:and|to)\s+([\d,]+)\s*(?:km|kilometers?)?", query)
    if mileage_range:
        conditions.append(FieldCondition(key="metadata.mileage_numeric", range=Range(gte=float(mileage_range.group(1).replace(',','')), lte=float(mileage_range.group(2).replace(',','')))))
    else:
        mileage_match = re.search(r"(?:under|below|less than)\s+([\d,]+)\s*(?:km|kilometers?)?", query)
        if mileage_match:
            conditions.append(FieldCondition(key="metadata.mileage_numeric", range=Range(lt=float(mileage_match.group(1).replace(',','')))))
    # FUEL EFFICIENCY (city/hwy/combined)
    fe_city_range = re.search(r"city\s+(?:between|from)\s+([\d\.]+)\s+(?:and|to)\s+([\d\.]+)", query)
    if fe_city_range:
        conditions.append(FieldCondition(key="metadata.fuel_efficiency_city", range=Range(gte=float(fe_city_range.group(1)), lte=float(fe_city_range.group(2)))))
    else:
        fe_city = re.search(r"city\s*(?:under|below|less than)\s*([\d\.]+)", query)
        if fe_city:
            conditions.append(FieldCondition(key="metadata.fuel_efficiency_city", range=Range(lt=float(fe_city.group(1)))))
    fe_hwy_range = re.search(r"(?:highway|hwy)\s+(?:between|from)\s+([\d\.]+)\s+(?:and|to)\s+([\d\.]+)", query)
    if fe_hwy_range:
        conditions.append(FieldCondition(key="metadata.fuel_efficiency_highway", range=Range(gte=float(fe_hwy_range.group(1)), lte=float(fe_hwy_range.group(2)))))
    else:
        fe_hwy = re.search(r"(?:highway|hwy)\s*(?:under|below|less than)\s*([\d\.]+)", query)
        if fe_hwy:
            conditions.append(FieldCondition(key="metadata.fuel_efficiency_highway", range=Range(lt=float(fe_hwy.group(1)))))
    fe_combined_range = re.search(r"(?:combined)\s+(?:between|from)\s+([\d\.]+)\s+(?:and|to)\s+([\d\.]+)", query)
    if fe_combined_range:
        conditions.append(FieldCondition(key="metadata.fuel_efficiency_combined", range=Range(gte=float(fe_combined_range.group(1)), lte=float(fe_combined_range.group(2)))))
    else:
        fe_combined = re.search(r"(?:combined)\s*(?:under|below|less than)\s*([\d\.]+)", query)
        if fe_combined:
            conditions.append(FieldCondition(key="metadata.fuel_efficiency_combined", range=Range(lt=float(fe_combined.group(1)))))
    return Filter(must=conditions) if conditions else None

RETURN_COLUMNS = ["id","title","year","make","model","mileage(km)","location/city","latest_price","description","body_type","fuel_type","fuel_efficiency_city","fuel_efficiency_highway"]

# Simple auth decorator to check tunnel secret
def check_auth():
    header = request.headers.get("X-API-KEY")
    if not header or header != TUNNEL_SECRET:
        abort(401, description="Unauthorized")

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query_endpoint():
    # Authenticate first
    check_auth()

    user_query = request.form.get("user_input", "").strip()
    if not user_query:
        return jsonify({"error":"No query provided"}), 400

    try:
        filter_kwargs = build_filter(user_query)
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k":6, "filter": filter_kwargs})
        chain = funcChain(retriever)

        result = chain({"question": user_query}, return_only_outputs=True)
        answer = result.get("answer") or result.get("result") or ""
        source_documents = result.get("source_documents", [])

        source_ids = [doc.metadata.get("source") for doc in source_documents if doc.metadata.get("source")]
        sources_list = []
        if source_ids and not df.empty:
            matched_rows = df[df["id"].astype(str).isin(set(source_ids))].drop_duplicates(subset="id", keep="first")
            for _, row in matched_rows[RETURN_COLUMNS].iterrows():
                item = {col: (row[col] if col in row.index else "") for col in RETURN_COLUMNS}
                sources_list.append(item)

        return jsonify({"answer": answer, "sources": sources_list})

    except Exception as e:
        print("Error in /query:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT)