import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.llm_provider import llm
from database import get_db

class ResponseAgent:
    """
    Response Agent (Step 5 in Workflow):
    Synthesizes findings from Manager, Troubleshooting, Knowledge, and Database agents.
    Evaluates: Problem Solved? (YES -> Close Ticket / NO -> Human Escalation).
    Prepares final response and records ticket resolution in SQLite.
    """
    
    def process(
        self,
        request_text: str,
        ticket_number: str,
        manager_data: dict,
        troubleshooting_data: dict,
        knowledge_data: dict,
        database_data: dict
    ) -> dict:
        category = manager_data.get("category", "")
        urgency = manager_data.get("urgency", "Medium")
        emp = database_data.get("employee", {})
        device = database_data.get("device", {})
        sop = knowledge_data.get("standard_procedure", "")
        solution_type = knowledge_data.get("solution_type", "Self-Service")

        # Determine if problem is solved via automated procedure or requires human escalation
        is_hardware = "Hardware" in category or "BSOD" in request_text or "Requires Escalation" in solution_type
        is_critical_security = urgency == "Critical" and "Security" in category
        
        if is_hardware or is_critical_security:
            problem_solved = False
            ticket_status = "ESCALATED_HUMAN"
            assigned_tier = "Tier-2 Field Operations / Senior SecOps"
        else:
            problem_solved = True
            ticket_status = "RESOLVED"
            assigned_tier = "AI Automated Self-Service Desk"

        # Generate response
        prompt = f"""
You are the IT Response Agent. Prepare an empathetic, professional, clear IT Helpdesk ticket response for the employee.

EMPLOYEE: {emp.get('name')} ({emp.get('email')}), Department: {emp.get('department')}
DEVICE: {device.get('hostname')} ({device.get('os_version')})
ISSUE CATEGORY: {category} ({urgency} Priority)
ISSUE DESCRIPTION: "{request_text}"

KNOWLEDGE BASE SOP:
{sop}

DECISION:
- Problem Solved by AI SOP: {problem_solved}
- Ticket Outcome: {ticket_status}
- Escalation: {assigned_tier if not problem_solved else 'None - Automated Self-Service Resolution'}

Draft a response email formatted with:
1. Friendly greeting addressing {emp.get('name')}
2. Clear confirmation of device and ticket #{ticket_number}
3. Exact actionable steps (or escalation confirmation if physical inspection/Tier-2 required)
4. Ticket status notice: [{ticket_status}]
"""
        system_prompt = "You are a courteous, clear IT Support Specialist AI agent."
        final_message = llm.generate(prompt=prompt, system_prompt=system_prompt, temperature=0.4)

        # Save / update in SQLite database
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tickets 
                SET status = ?, assigned_agent = ?, is_escalated = ?, resolution_notes = ?, closed_at = ?
                WHERE ticket_number = ?
            """, (
                ticket_status,
                assigned_tier,
                1 if not problem_solved else 0,
                final_message[:500],
                now_str if problem_solved else None,
                ticket_number
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating ticket status in database: {e}")

        return {
            "agent": "Response Agent",
            "problem_solved": problem_solved,
            "decision": "Close Ticket" if problem_solved else "Escalate to Human IT Specialist",
            "ticket_status": ticket_status,
            "assigned_tier": assigned_tier,
            "final_response": final_message.strip(),
            "timestamp": now_str
        }
