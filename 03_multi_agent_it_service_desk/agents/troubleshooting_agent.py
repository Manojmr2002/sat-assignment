import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.llm_provider import llm

class TroubleshootingAgent:
    """
    Troubleshooting Agent (Step 2 in Workflow):
    Handles technical analysis and generates step-by-step diagnostic checks.
    """
    
    def process(self, request_text: str, manager_analysis: dict) -> dict:
        category = manager_analysis.get("category", "General")
        summary = manager_analysis.get("summary", request_text)
        
        prompt = f"""
You are the Technical Troubleshooting Specialist Agent.
Problem Category: {category}
Issue Summary: {summary}
Original Request: "{request_text}"

Generate systematic technical troubleshooting steps to diagnose and isolate the root cause.
Include:
1. Primary Root Cause Hypothesis
2. Immediate verification steps
3. Clear step-by-step instructions (bullet points)
4. Recommended follow-up agent action ('Knowledge Agent' for SOP check)
"""
        system_prompt = "You are a senior Systems & Network Engineering AI agent. Provide clear, precise technical diagnostic instructions."
        response = llm.generate(prompt=prompt, system_prompt=system_prompt, temperature=0.3)
        
        return {
            "agent": "Troubleshooting Agent",
            "hypothesis": f"Potential misconfiguration or credential/network anomaly in {category}.",
            "diagnostic_steps": response.strip(),
            "next_step": "Knowledge Agent (Verify with Organization SOPs)"
        }
