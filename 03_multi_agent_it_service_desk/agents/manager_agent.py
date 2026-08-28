import json
import re
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.llm_provider import llm

class ManagerAgent:
    """
    Manager Agent (Step 1 in Workflow):
    Understands the employee IT request, classifies problem category and urgency, 
    and delegates tasks to downstream specialized agents.
    """
    
    def process(self, request_text: str, employee_email: str = "") -> dict:
        prompt = f"""
You are the Lead IT Manager Agent. Analyze the following employee IT request:

REQUEST: "{request_text}"
EMPLOYEE EMAIL: "{employee_email}"

Perform the following:
1. Classify the problem category (One of: 'Network / VPN', 'Software & Access', 'Hardware / System', 'Security / Identity', 'General').
2. Determine urgency level (One of: 'Low', 'Medium', 'High', 'Critical').
3. Provide a concise technical summary.
4. Set the initial delegation target (e.g., 'Troubleshooting Agent').

Output ONLY a valid JSON object matching:
{{
  "category": "Category Name",
  "urgency": "Urgency Level",
  "summary": "Brief problem summary",
  "delegated_to": "Troubleshooting Agent",
  "reasoning": "Reasoning for classification"
}}
"""
        system_prompt = "You are an expert IT Incident Manager Agent. Respond ONLY in valid JSON format."
        raw_output = llm.generate(prompt=prompt, system_prompt=system_prompt, temperature=0.2)
        
        # Parse JSON
        result = self._parse_json(raw_output, request_text)
        return result

    def _parse_json(self, text: str, fallback_query: str) -> dict:
        try:
            cleaned = re.sub(r'```json\s*', '', text)
            cleaned = re.sub(r'```\s*$', '', cleaned).strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            if start != -1 and end != 0:
                data = json.loads(cleaned[start:end])
                return data
        except Exception:
            pass
            
        # Heuristic fallback based on keywords
        query_l = fallback_query.lower()
        if "vpn" in query_l or "network" in query_l or "wifi" in query_l or "internet" in query_l:
            cat = "Network / VPN"
            urgency = "High"
        elif "password" in query_l or "mfa" in query_l or "token" in query_l or "login" in query_l:
            cat = "Security / Identity"
            urgency = "High"
        elif "hardware" in query_l or "screen" in query_l or "crash" in query_l or "bsod" in query_l or "laptop" in query_l:
            cat = "Hardware / System"
            urgency = "Critical"
        else:
            cat = "Software & Access"
            urgency = "Medium"
            
        return {
            "category": cat,
            "urgency": urgency,
            "summary": f"Employee reported: {fallback_query}",
            "delegated_to": "Troubleshooting Agent",
            "reasoning": f"Identified {cat} keywords and assessed urgency as {urgency}."
        }
