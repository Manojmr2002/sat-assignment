import os
import sys
import uuid
from flask import Flask, render_template, request, jsonify

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from shared.llm_provider import llm
from crew_engine import CrewStudyEngine

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = os.path.join(config.UPLOAD_FOLDER, 'study_docs')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Global Crew Engine
study_engine = CrewStudyEngine()

@app.route('/')
def index():
    ollama_info = llm.check_connection()
    vector_status = study_engine.vector_store.get_status()
    materials = study_engine.vector_store.indexed_materials
    return render_template(
        'index.html',
        ollama_info=ollama_info,
        vector_status=vector_status,
        materials=materials
    )

@app.route('/upload', methods=['POST'])
def upload_study_material():
    if 'document' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
        
    file = request.files['document']
    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename"}), 400
        
    try:
        filename = f"{uuid.uuid4().hex[:6]}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        info = study_engine.vector_store.ingest_document(filepath)
        return jsonify({
            "success": True,
            "material": info,
            "total_chunks": study_engine.vector_store.local_db.count()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json or {}
    query = data.get('query', '').strip()
    model = data.get('model', None)

    if not query:
        return jsonify({"success": False, "error": "Question cannot be empty"}), 400

    try:
        result = study_engine.run_crew(query=query, model=model)
        return jsonify({
            "success": True,
            "query": result["query"],
            "final_answer": result["final_answer"],
            "trace": result["trace"],
            "sources": result["sources"],
            "flashcards": result["flashcards"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear():
    study_engine.vector_store.clear()
    return jsonify({"success": True, "message": "Study materials cleared."})

@app.route('/api/status')
def status():
    return jsonify({
        "ollama": llm.check_connection(),
        "vector_store": study_engine.vector_store.get_status()
    })

if __name__ == '__main__':
    print(f"[*] Starting AI Study Assistant on http://localhost:{config.PORT_STUDY}")
    app.run(host='0.0.0.0', port=config.PORT_STUDY, debug=True)
