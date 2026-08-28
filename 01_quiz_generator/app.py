import os
import sys
import uuid
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from shared.llm_provider import llm
from engine import QuizEngine

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = os.path.join(config.UPLOAD_FOLDER, 'quiz_docs')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory storage for active quizzes
QUIZ_STORE = {}

@app.route('/')
def index():
    ollama_info = llm.check_connection()
    return render_template('index.html', ollama_info=ollama_info)

@app.route('/generate', methods=['POST'])
def generate_quiz():
    try:
        num_questions = int(request.form.get('num_questions', 5))
        difficulty = request.form.get('difficulty', 'Medium')
        topic = request.form.get('topic', 'General')
        model = request.form.get('model', None)
        
        extracted_text = ""
        doc_name = "Direct Text Input"
        
        # Handle file upload
        if 'document' in request.files and request.files['document'].filename:
            file = request.files['document']
            filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            extracted_text = QuizEngine.extract_text(filepath)
            doc_name = file.filename
        elif request.form.get('raw_text'):
            extracted_text = request.form.get('raw_text').strip()
            
        if not extracted_text:
            return jsonify({"success": False, "error": "Please provide a document or paste text."}), 400
            
        # Generate MCQs
        questions = QuizEngine.generate_quiz(
            context_text=extracted_text,
            num_questions=num_questions,
            difficulty=difficulty,
            topic=topic,
            model=model
        )
        
        quiz_id = uuid.uuid4().hex[:12]
        QUIZ_STORE[quiz_id] = {
            "id": quiz_id,
            "title": f"Quiz on {doc_name}",
            "doc_name": doc_name,
            "difficulty": difficulty,
            "topic": topic,
            "questions": questions,
            "raw_context": extracted_text[:1000]
        }
        
        return jsonify({
            "success": True,
            "quiz_id": quiz_id,
            "redirect_url": url_for('view_quiz', quiz_id=quiz_id)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/quiz/<quiz_id>')
def view_quiz(quiz_id):
    quiz = QUIZ_STORE.get(quiz_id)
    if not quiz:
        return redirect(url_for('index'))
    return render_template('quiz.html', quiz=quiz)

@app.route('/evaluate/<quiz_id>', methods=['POST'])
def evaluate_quiz(quiz_id):
    quiz = QUIZ_STORE.get(quiz_id)
    if not quiz:
        return jsonify({"success": False, "error": "Quiz not found"}), 404
        
    user_answers = request.json.get('answers', {})
    total = len(quiz['questions'])
    correct_count = 0
    detailed_results = []
    
    for q in quiz['questions']:
        qid = str(q['id'])
        user_choice = user_answers.get(qid, "").upper().strip()
        correct_choice = q['correct_answer'].upper().strip()
        is_correct = (user_choice == correct_choice)
        if is_correct:
            correct_count += 1
            
        detailed_results.append({
            "id": q['id'],
            "question": q['question'],
            "options": q['options'],
            "user_choice": user_choice,
            "correct_answer": correct_choice,
            "is_correct": is_correct,
            "explanation": q.get('explanation', '')
        })
        
    score_percentage = round((correct_count / total * 100), 1) if total > 0 else 0
    
    return jsonify({
        "success": True,
        "score": correct_count,
        "total": total,
        "percentage": score_percentage,
        "results": detailed_results
    })

@app.route('/export/pdf/<quiz_id>')
def export_pdf(quiz_id):
    quiz = QUIZ_STORE.get(quiz_id)
    if not quiz:
        return "Quiz not found", 404
        
    pdf_filename = f"quiz_{quiz_id}.pdf"
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    include_answers = request.args.get('answers', 'true').lower() == 'true'
    
    QuizEngine.export_pdf(
        quiz_title=quiz['title'],
        questions=quiz['questions'],
        output_path=pdf_path,
        include_answers=include_answers
    )
    
    return send_file(pdf_path, as_attachment=True, download_name=f"{quiz['title']}.pdf")

@app.route('/export/json/<quiz_id>')
def export_json(quiz_id):
    quiz = QUIZ_STORE.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    return jsonify(quiz)

@app.route('/api/status')
def status():
    return jsonify(llm.check_connection())

if __name__ == '__main__':
    print(f"[*] Starting Quiz Generator on http://localhost:{config.PORT_QUIZ}")
    app.run(host='0.0.0.0', port=config.PORT_QUIZ, debug=True)
