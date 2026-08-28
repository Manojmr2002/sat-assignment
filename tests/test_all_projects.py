import os
import sys
import unittest
import json

# Add root directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from shared.document_parser import DocumentParser
from shared.vector_db import LocalVectorDB
from shared.llm_provider import llm

# Project 1
sys.path.append(os.path.join(BASE_DIR, '01_quiz_generator'))
from engine import QuizEngine
import app as quiz_app_module

# Project 2
sys.path.append(os.path.join(BASE_DIR, '02_rag_chatbot'))
from rag_engine import RAGEngine
import app as rag_app_module

# Project 3
sys.path.append(os.path.join(BASE_DIR, '03_multi_agent_it_service_desk'))
from agents.manager_agent import ManagerAgent
from agents.troubleshooting_agent import TroubleshootingAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.database_agent import DatabaseAgent
from agents.response_agent import ResponseAgent
from database import init_db, get_db
import app as it_desk_app_module

# Project 4
sys.path.append(os.path.join(BASE_DIR, '04_ai_study_assistant'))
from crew_engine import CrewStudyEngine
from vector_store import StudyVectorStore
import app as study_app_module

class TestAssignmentSuite(unittest.TestCase):

    def setUp(self):
        self.sample_text = (
            "Deep learning is a subset of machine learning based on artificial neural networks with representation learning. "
            "Convolutional Neural Networks (CNNs) are particularly effective for computer vision tasks such as image classification "
            "and object detection. Transformers have revolutionized natural language processing through the self-attention mechanism. "
            "Retrieval-Augmented Generation (RAG) combines semantic vector search with large language models to ground responses in verified documents."
        )

    def test_01_document_parser_and_vector_db(self):
        print("\n[TEST] Testing DocumentParser and LocalVectorDB...")
        pages = [{"page_number": 1, "content": self.sample_text, "source": "sample_ai.txt"}]
        chunks = DocumentParser.chunk_documents(pages, chunk_size=20, chunk_overlap=5)
        self.assertTrue(len(chunks) > 0)

        vdb = LocalVectorDB(name="test_vdb")
        added = vdb.add_documents(chunks)
        self.assertEqual(added, len(chunks))

        results = vdb.similarity_search("What are Convolutional Neural Networks used for?", k=2)
        self.assertTrue(len(results) > 0)
        self.assertTrue("CNN" in results[0]["text"] or "neural" in results[0]["text"].lower())
        print("  -> Passed DocumentParser & VectorDB test")

    def test_02_quiz_generator(self):
        print("\n[TEST] Testing 01_quiz_generator...")
        questions = QuizEngine.generate_quiz(
            context_text=self.sample_text,
            num_questions=3,
            difficulty="Medium",
            topic="Deep Learning"
        )
        self.assertTrue(len(questions) >= 1)
        q1 = questions[0]
        self.assertIn("question", q1)
        self.assertIn("options", q1)
        self.assertIn("correct_answer", q1)
        self.assertIn(q1["correct_answer"], ["A", "B", "C", "D"])

        # Test PDF Export
        test_pdf_path = os.path.join(BASE_DIR, "uploads", "test_quiz.pdf")
        QuizEngine.export_pdf("Sample AI Assessment", questions, test_pdf_path, include_answers=True)
        self.assertTrue(os.path.exists(test_pdf_path))
        print("  -> Passed Quiz Generator & PDF export test")

    def test_03_rag_chatbot(self):
        print("\n[TEST] Testing 02_rag_chatbot...")
        rag = RAGEngine(name="test_rag")
        chunks = [{"id": 0, "text": self.sample_text, "source": "ai_notes.txt", "page_number": 1}]
        rag.vector_db.add_documents(chunks)

        # Test Hybrid Query
        res_hybrid = rag.answer_query("Explain how RAG works.", mode="hybrid")
        self.assertIn("answer", res_hybrid)
        self.assertTrue(len(res_hybrid["sources"]) > 0)

        # Test Doc Only Query
        res_doc = rag.answer_query("Transformers self-attention", mode="doc_only")
        self.assertIn("answer", res_doc)
        print("  -> Passed RAG Chatbot retrieval & synthesis test")

    def test_04_multi_agent_it_desk(self):
        print("\n[TEST] Testing 03_multi_agent_it_service_desk 5-Agent Pipeline...")
        init_db()

        # Step 1: Manager Agent
        mgr = ManagerAgent()
        m_res = mgr.process("VPN is not connecting with error 806 timeout", "alex.chen@company.com")
        self.assertEqual(m_res["category"], "Network / VPN")

        # Step 2: Troubleshooting Agent
        trouble = TroubleshootingAgent()
        t_res = trouble.process("VPN is not connecting", m_res)
        self.assertIn("diagnostic_steps", t_res)

        # Step 3: Knowledge Agent
        kb = KnowledgeAgent()
        k_res = kb.process("VPN is not connecting", m_res)
        self.assertIn("standard_procedure", k_res)

        # Step 4: Database Agent
        db = DatabaseAgent()
        d_res = db.process("alex.chen@company.com", "Alex Chen")
        self.assertEqual(d_res["employee"]["name"], "Alex Chen")
        self.assertIsNotNone(d_res["device"])

        # Step 5: Response Agent
        resp_agent = ResponseAgent()
        r_res = resp_agent.process(
            request_text="VPN is not connecting with error 806 timeout",
            ticket_number="INC-TEST-001",
            manager_data=m_res,
            troubleshooting_data=t_res,
            knowledge_data=k_res,
            database_data=d_res
        )
        self.assertIn("final_response", r_res)
        self.assertIn("ticket_status", r_res)
        print(f"  -> Decision: {r_res['decision']}, Status: {r_res['ticket_status']}")
        print("  -> Passed Multi-Agent IT Service Desk workflow test")

    def test_05_ai_study_assistant_crew(self):
        print("\n[TEST] Testing 04_ai_study_assistant CrewAI Engine...")
        study_engine = CrewStudyEngine()
        chunks = [{"id": 0, "text": self.sample_text, "source": "lecture_1.txt", "page_number": 1}]
        study_engine.vector_store.local_db.add_documents(chunks)

        result = study_engine.run_crew(query="What is Retrieval-Augmented Generation?")
        self.assertIn("final_answer", result)
        self.assertEqual(len(result["trace"]), 3)
        self.assertTrue(len(result["flashcards"]) > 0)
        print(f"  -> Generated {len(result['flashcards'])} interactive flashcards")
        print("  -> Passed AI Study Assistant CrewAI test")

if __name__ == '__main__':
    unittest.main()
