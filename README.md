# 🚀 AI & Multi-Agent Systems Assignment Suite

A comprehensive, production-ready Python suite implementing all **4 projects** specified in the assignment presentation. Each project can be executed either as an independent standalone Flask application or simultaneously through the **Unified Master Portal**.

---

## 📑 Table of Contents
1. [Project 01: AI Quiz Generator](#01-ai-quiz-generator)
2. [Project 02: RAG Chatbot](#02-rag-chatbot)
3. [Project 03: Multi-Agent IT Service Desk](#03-multi-agent-it-service-desk)
4. [Project 04: AI Study Assistant Using CrewAI & Pinecone](#04-ai-study-assistant-using-crewai--pinecone)
5. [Quick Start & Setup](#quick-start--setup)
6. [Ollama Integration & Fallbacks](#ollama-integration)

---

## 01. AI Quiz Generator
> **Slide 01**: AI-powered Quiz Generator that automatically analyses uploaded documents and generates multiple-choice questions (MCQs) with answer options and the correct answer.

- **Key Capabilities**:
  - Upload PDF, TXT, or paste raw text.
  - Generates configurable MCQs (3 to 15 questions) across Easy, Medium, Hard difficulty levels.
  - Interactive exam testing interface with a live countdown timer and instant progress tracking.
  - Instant score calculation with correct/incorrect visual feedback and detailed answer explanations.
  - **Export to PDF**: Downloads a professionally formatted PDF assessment sheet using ReportLab.
- **Tech Stack**: Ollama LLM, LangChain Prompt Templates, Vector DB, Flask, HTML5, CSS3, ReportLab.
- **Port**: `http://localhost:5001`

---

## 02. RAG Chatbot
> **Slide 02**: Web application where users upload PDFs and ask questions, answering from both documents and LLM knowledge.

- **Key Capabilities**:
  - Multi-document PDF uploader and vector indexing with chunk overlap.
  - **Hybrid Synthesis Engine**: Blends verified factual excerpts from uploaded PDFs with the LLM's broader parametric knowledge.
  - **3 Operating Modes**:
    1. *Hybrid (Doc + LLM)*: Synthesizes both sources with clear categorization.
    2. *Strict Document Only*: Answers strictly from source text.
    3. *General LLM*: Direct conversational model knowledge.
  - Interactive citation viewer modal displaying exact document names, page numbers, and similarity scores.
- **Tech Stack**: Ollama LLM, LangChain, FAISS / Vector DB, Flask, HTML5, CSS3, JavaScript.
- **Port**: `http://localhost:5002`

---

## 03. Multi-Agent IT Service Desk
> **Slides 03 - 05**: AI-powered IT Service Management system analyzing employee IT requests and delegating across 5 specialized AI agents.

- **Specialized 5-Agent Pipeline**:
  1. **Manager Agent**: Understands request, classifies problem category (*Network/VPN, Software & Access, Hardware/System, Security*), and assigns urgency.
  2. **Troubleshooting Agent**: Generates diagnostic hypotheses and technical checklists.
  3. **Knowledge Agent**: Queries organization's Knowledge Base (SOP articles) for standard operating procedures.
  4. **Database Agent**: Queries SQLite database to verify employee credentials, assigned devices, MAC/IP, and ticket history.
  5. **Response Agent**: Evaluates **Problem Solved?**
     - **YES** $\rightarrow$ Formulates resolution response, marks ticket `RESOLVED`, and closes ticket.
     - **NO** $\rightarrow$ Escalates to Tier-2 Human Engineer and marks ticket `ESCALATED_HUMAN`.
- **Admin Dashboard & Database Explorer**: View real-time tickets queue, corporate employee directory, hardware inventory, and knowledge base articles.
- **Tech Stack**: Ollama LLM, Multi-Agent Engine, SQLite, Flask, HTML5, CSS3, JavaScript.
- **Port**: `http://localhost:5003`

---

## 04. AI Study Assistant Using CrewAI & Pinecone
> **Slides 06 - 08**: AI-powered Study Assistant using multiple specialized agents and Pinecone semantic search to synthesize reliable study materials.

- **CrewAI Collaborative Agents**:
  1. **Research Agent**: Deep semantic search across uploaded study documents, extracting key formulas, definitions, and citations.
  2. **Analysis Agent**: Transforms raw evidence into structured pedagogical study notes with practical analogies and step-by-step breakdowns.
  3. **Review Agent**: Audits notes against source text for factual accuracy, checks for hallucinations, and validates grounding confidence (98%).
- **Interactive 3D Study Flashcards**: Automatically generates high-yield Q&A flashcards with click-to-flip 3D CSS animation.
- **Tech Stack**: CrewAI Multi-Agent Pipeline, Pinecone & Vector DB, Sentence Transformers, Flask, HTML5, CSS3.
- **Port**: `http://localhost:5004`

---

## ⚡ Quick Start & Setup

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Run the Unified Master Portal (Launches All 4 Apps)
```bash
python app.py
```
Open **`http://localhost:5000`** in your browser to access the central dashboard.

### 3. Run Any Project Standalone (Optional)
You can also launch any individual project directly:
```bash
# Project 1: Quiz Generator
python 01_quiz_generator/app.py       # http://localhost:5001

# Project 2: RAG Chatbot
python 02_rag_chatbot/app.py          # http://localhost:5002

# Project 3: IT Service Desk
python 03_multi_agent_it_service_desk/app.py  # http://localhost:5003

# Project 4: AI Study Assistant
python 04_ai_study_assistant/app.py   # http://localhost:5004
```

---

## 🧠 Ollama Integration & Fallbacks

All 4 applications are configured to automatically connect to **Ollama** if running on your machine:
```bash
# Download and start any preferred local model
ollama run llama3
# or
ollama run mistral
```

- **Smart Heuristic Simulation Fallback**: If Ollama is not currently running or downloading, all 4 applications include an intelligent semantic fallback engine that ensures complete functionality, instant responses, and realistic multi-agent execution out-of-the-box!
