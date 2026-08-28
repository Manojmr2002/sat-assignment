import os
import sys
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from database import get_db

class KnowledgeAgent:
    """
    Knowledge Agent (Step 3 in Workflow):
    Searches the organization's knowledge base and standard operating procedures (SOPs).
    """
    
    def process(self, request_text: str, manager_analysis: dict) -> dict:
        category = manager_analysis.get("category", "")
        conn = get_db()
        cursor = conn.cursor()
        
        # Search by category and keywords
        cursor.execute("SELECT * FROM knowledge_base")
        all_articles = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Find best matching article
        best_match = None
        highest_score = -1
        keywords = set(request_text.lower().split() + category.lower().split())

        for article in all_articles:
            score = 0
            art_text = f"{article['category']} {article['title']} {article['symptoms']}".lower()
            for kw in keywords:
                if len(kw) > 3 and kw in art_text:
                    score += 1
            if article['category'].lower() in category.lower():
                score += 3
            if score > highest_score:
                highest_score = score
                best_match = article

        if best_match and highest_score > 0:
            return {
                "agent": "Knowledge Agent",
                "matched_article_id": best_match["id"],
                "article_title": best_match["title"],
                "category": best_match["category"],
                "solution_type": best_match["solution_type"],
                "standard_procedure": best_match["troubleshooting_steps"],
                "status": "SOP Found"
            }
        else:
            return {
                "agent": "Knowledge Agent",
                "matched_article_id": None,
                "article_title": "General Incident Protocol",
                "category": category,
                "solution_type": "Standard Diagnostic",
                "standard_procedure": "1. Review system application event logs.\n2. Confirm endpoint compliance.\n3. Escalate if unresolvable.",
                "status": "No specific KB found; using General IT Standard Protocol"
            }
