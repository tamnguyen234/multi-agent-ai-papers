from typing import List
from app.schemas import PaperItem

def get_mock_papers(today_str: str) -> List[PaperItem]:
    """
    Generate mock paper entries for fallback mode (backward compatible with Task 7).
    """
    mock_data = [
        {
            "rank_position": 1,
            "arxiv_id": "mock-001",
            "title": "Scaling Laws for Large Multi-Agent Systems",
            "abstract": "We investigate how scaling LLM size and agent population affects overall system performance in collaborative tasks. Our results demonstrate sub-linear performance gains with population size.",
            "summary": "This study explores scaling law dynamics in multi-agent LLM systems, showing sub-linear performance gains.",
            "authors": ["Tâm Nguyễn", "John Doe"],
            "published": today_str,
            "pdf_url": "https://arxiv.org/pdf/2401.00001",
            "pdf_path": None,
            "score": 98.5,
            "upvotes": 98
        },
        {
            "rank_position": 2,
            "arxiv_id": "mock-002",
            "title": "Self-Reflection Mechanisms in Autonomous Agents",
            "abstract": "Self-reflection enables autonomous agents to correct their errors dynamically during execution. We propose a lightweight reflection loop that increases success rate by 20% on reasoning benchmarks.",
            "summary": "We propose a lightweight reflection loop for autonomous agents that increases success rate by 20%.",
            "authors": ["Jane Smith", "Tâm Nguyễn"],
            "published": today_str,
            "pdf_url": "https://arxiv.org/pdf/2401.00002",
            "pdf_path": None,
            "score": 95.2,
            "upvotes": 95
        },
        {
            "rank_position": 3,
            "arxiv_id": "mock-003",
            "title": "Improving Text-to-Speech Prosody for Academic Digests",
            "abstract": "Generating podcast-style audio digests from papers requires expressiveness and proper prosody for complex technical words. We train a multi-speaker TTS model on academic presentations.",
            "summary": "This work trains a multi-speaker TTS model on academic lectures to improve prosody for paper digests.",
            "authors": ["Alice Cooper", "Bob Vance"],
            "published": today_str,
            "pdf_url": "https://arxiv.org/pdf/2401.00003",
            "pdf_path": None,
            "score": 91.8,
            "upvotes": 91
        },
        {
            "rank_position": 4,
            "arxiv_id": "mock-004",
            "title": "Retrieval-Augmented Generation with Hierarchical Document Graph",
            "abstract": "We present GraphRAG-H, a RAG system that structures academic PDFs into hierarchical graphs representing chapters, sections, and paragraphs, showing better retrieval accuracy than flat chunking.",
            "summary": "We introduce GraphRAG-H, a system structuring documents into hierarchical graphs for more accurate retrieval.",
            "authors": ["David Beckham", "Tâm Nguyễn"],
            "published": today_str,
            "pdf_url": "https://arxiv.org/pdf/2401.00004",
            "pdf_path": None,
            "score": 89.1,
            "upvotes": 89
        },
        {
            "rank_position": 5,
            "arxiv_id": "mock-005",
            "title": "Emergent Cooperation in Competitive Multi-Agent Environments",
            "abstract": "We analyze reinforcement learning agents in mixed cooperative-competitive settings. We show that temporary alliances emerge naturally when agents face high resource scarcity.",
            "summary": "This study analyzes emergent cooperation and temporary alliances among RL agents in competitive settings.",
            "authors": ["Eve Adams", "Frank Miller"],
            "published": today_str,
            "pdf_url": "https://arxiv.org/pdf/2401.00005",
            "pdf_path": None,
            "score": 86.4,
            "upvotes": 86
        }
    ]
    return [PaperItem(**p) for p in mock_data]
