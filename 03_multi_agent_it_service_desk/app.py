import os
import sys
import uuid
import json
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from shared.llm_provider import llm
from database import init_db, get_db

# Import 5 Agents
from agents.manager_agent import ManagerAgent
from agents.troubleshooting_agent import TroubleshootingAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.database_agent import DatabaseAgent
from agents.response_agent import ResponseAgent

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Ensure database is initialized
init_db()

# Initialize Agents
manager_agent = ManagerAgent()
troubleshooting_agent = TroubleshootingAgent()
knowledge_agent = KnowledgeAgent()
database_agent = DatabaseAgent()
response_agent = ResponseAgent()

@app.route('/')
def index():
    ollama_info = llm.check_connection()
    # Get recent tickets
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 5")
    recent_tickets = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT email, name, department FROM employees")
    employees = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return render_template('index.html', ollama_info=ollama_info, recent_tickets=recent_tickets, employees=employees)

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    data = request.json or {}
    request_text = data.get('request_text', '').strip()
    employee_email = data.get('employee_email', 'alex.chen@company.com').strip()
    employee_name = data.get('employee_name', 'Alex Chen').strip()

    if not request_text:
        return jsonify({"success": False, "error": "Request description cannot be empty"}), 400

    ticket_number = f"INC-{random.randint(10000, 99999)}"
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Initial Insert in SQLite
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tickets (ticket_number, employee_name, employee_email, request_text, status, created_at)
        VALUES (?, ?, ?, ?, 'PROCESSING', ?)
    """, (ticket_number, employee_name, employee_email, request_text, now_str))
    conn.commit()
    conn.close()

    trace = []

    # Step 1: Manager Agent
    manager_res = manager_agent.process(request_text, employee_email)
    trace.append({
        "step": 1,
        "agent": "Manager Agent",
        "action": "Understand Request & Classify Problem",
        "data": manager_res
    })

    # Step 2: Troubleshooting Agent
    trouble_res = troubleshooting_agent.process(request_text, manager_res)
    trace.append({
        "step": 2,
        "agent": "Troubleshooting Agent",
        "action": "Formulate Technical Diagnostic Steps",
        "data": trouble_res
    })

    # Step 3: Knowledge Agent
    kb_res = knowledge_agent.process(request_text, manager_res)
    trace.append({
        "step": 3,
        "agent": "Knowledge Agent",
        "action": "Search Organization Knowledge Base & SOPs",
        "data": kb_res
    })

    # Step 4: Database Agent
    db_res = database_agent.process(employee_email, employee_name)
    trace.append({
        "step": 4,
        "agent": "Database Agent",
        "action": "Query SQLite for Employee, Device & Past Ticket Data",
        "data": db_res
    })

    # Step 5: Response Agent & Decision
    resp_res = response_agent.process(
        request_text=request_text,
        ticket_number=ticket_number,
        manager_data=manager_res,
        troubleshooting_data=trouble_res,
        knowledge_data=kb_res,
        database_data=db_res
    )
    trace.append({
        "step": 5,
        "agent": "Response Agent",
        "action": "Synthesize Findings & Evaluate Problem Solved (YES/NO)",
        "data": resp_res
    })

    # Update ticket with full trace in SQLite
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tickets 
        SET category = ?, urgency = ?, agent_trace = ?
        WHERE ticket_number = ?
    """, (
        manager_res.get("category", "General"),
        manager_res.get("urgency", "Medium"),
        json.dumps(trace),
        ticket_number
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "ticket_number": ticket_number,
        "category": manager_res.get("category"),
        "urgency": manager_res.get("urgency"),
        "problem_solved": resp_res.get("problem_solved"),
        "decision": resp_res.get("decision"),
        "ticket_status": resp_res.get("ticket_status"),
        "final_response": resp_res.get("final_response"),
        "trace": trace
    })

@app.route('/admin')
def admin():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY id DESC")
    tickets = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM employees")
    employees = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM devices")
    devices = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM knowledge_base")
    kb_articles = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template(
        'admin.html',
        tickets=tickets,
        employees=employees,
        devices=devices,
        kb_articles=kb_articles
    )

@app.route('/api/database')
def api_database():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees")
    employees = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM devices")
    devices = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM knowledge_base")
    kb = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM tickets ORDER BY id DESC")
    tickets = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({
        "employees": employees,
        "devices": devices,
        "knowledge_base": kb,
        "tickets": tickets
    })

if __name__ == '__main__':
    print(f"[*] Starting Multi-Agent IT Service Desk on http://localhost:{config.PORT_IT_DESK}")
    app.run(host='0.0.0.0', port=config.PORT_IT_DESK, debug=True)
