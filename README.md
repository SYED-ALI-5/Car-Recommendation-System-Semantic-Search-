### Car Semantic Search — NLP + Vector Database Project

This project is a natural-language car finder that uses:

Qdrant Vector Database (cloud-hosted)

Ollama (local LLM) — runs on the user's own machine

Semantic search + filtering

A clean front-end web interface

Render is used only to host the static webpage.
The query processing happens locally through a small RunPod-style server that each user runs on their own machine.


### Features

Search cars using normal human language
e.g. “hybrid SUVs 2018–2021 under 40 lac”

Semantic retrieval powered by vector embeddings

Automatic filtering (year, price, mileage, fuel averages, etc.)

Clean UI built in plain HTML/CSS/JS

Super fast when Ollama runs locally

Zero paid APIs — fully free solution


### Technology Stack

Python + Flask backend

LangChain for RAG pipeline

Ollama (phi3-mini) for LLM

Qdrant Cloud for vector search

HTML + CSS + JS for the front-end

Regex-based filter extraction


### Using the Website

Open your Render-hosted webpage

Your browser connects to:

    Render for the UI

    Your own laptop for LLM processing

Ask anything like:

“SUV 2020 under 30 lakh”

“sedan low mileage 2018 to 2021”

“hybrid under 5L mileage under 40k km”


### Credits

Built by Syed Ahmad Ali

Semester NLP Project

Instructor: Dr. Rao Adeel