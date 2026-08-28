import os
import sys
import uuid
from flask import Flask, render_template, request, jsonify

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from shared.llm_provider import llm
from rag_engine import RAGEngine

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = os.path.join(config.UPLOAD_FOLDER, 'rag_docs')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global RAG instance
rag_engine = RAGEngine(name="rag_chatbot")

@app.route('/')
def index():
    ollama_info = llm.check_connection()
    return render_template('index.html', ollama_info=ollama_info, indexed_files=rag_engine.indexed_files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'document' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
        
    file = request.files['document']
    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename"}), 400
        
    try:
        filename = f"{uuid.uuid4().hex[:6]}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        info = rag_engine.ingest_pdf(filepath)
        return jsonify({
            "success": True,
            "file": info,
            "total_chunks": rag_engine.vector_db.count()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    query = data.get('message', '').strip()
    mode = data.get('mode', 'hybrid')
    model = data.get('model', None)
    
    if not query:
        return jsonify({"success": False, "error": "Message cannot be empty"}), 400
        
    try:
        result = rag_engine.answer_query(query=query, mode=mode, model=model)
        return jsonify({
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"],
            "mode": result["mode"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear():
    rag_engine.clear()
    return jsonify({"success": True, "message": "Knowledge base reset."})

@app.route('/api/status')
def status():
    return jsonify(llm.check_connection())

if __name__ == '__main__':
    print(f"[*] Starting RAG Chatbot on http://localhost:{config.PORT_RAG}")
    app.run(host='0.0.0.0', port=config.PORT_RAG, debug=True)
