from typing import List
from app.schemas import PaperItem, TopicResponseItem

TOPIC_GROUPS = [
    {
        "name": "Large Language Models",
        "description": "Papers related to large language models, transformers, prompting, and generative AI.",
        "keywords": ["llm", "large language model", "language model", "transformer", "prompt", "prompting", "generative ai", "gpt", "llama", "instruction tuning"]
    },
    {
        "name": "Retrieval-Augmented Generation",
        "description": "Papers exploring retrieval-augmented generation, vector databases, document Q&A, and search mechanisms.",
        "keywords": ["rag", "retrieval augmented generation", "retrieval", "vector database", "embedding", "faiss", "knowledge base", "document qa", "citation"]
    },
    {
        "name": "Multi-Agent Systems",
        "description": "Papers focusing on multi-agent cooperation, autonomous agents, workflows, and tool execution.",
        "keywords": ["agent", "multi-agent", "autonomous agent", "tool use", "planning", "orchestration", "workflow", "coordination"]
    },
    {
        "name": "Computer Vision",
        "description": "Papers involving image processing, computer vision, visual generation, multimodal learning, and video modeling.",
        "keywords": ["computer vision", "image", "vision", "object detection", "segmentation", "diffusion", "video", "multimodal", "clip"]
    },
    {
        "name": "Speech / Audio",
        "description": "Papers discussing speech recognition, audio processing, voice cloning, and text-to-speech generation.",
        "keywords": ["speech", "audio", "tts", "text-to-speech", "asr", "voice", "speaker", "waveform"]
    },
    {
        "name": "Reinforcement Learning",
        "description": "Papers analyzing reinforcement learning, rewards, policies, and environment interactions.",
        "keywords": ["reinforcement learning", "rl", "reward", "policy", "agent environment", "q-learning", "decision making"]
    },
    {
        "name": "AI Safety",
        "description": "Papers investigating AI safety, model alignment, hallucination detection, bias mitigation, and trustworthiness.",
        "keywords": ["safety", "alignment", "hallucination", "bias", "robustness", "evaluation", "red teaming", "trustworthy"]
    },
    {
        "name": "AI Systems",
        "description": "Papers optimizing AI systems, latency reduction, GPU hardware usage, and distributed serving infrastructures.",
        "keywords": ["serving", "inference", "optimization", "latency", "distributed", "deployment", "hardware", "gpu", "efficiency"]
    }
]

def analyze_rule_based(papers: List[PaperItem]) -> List[TopicResponseItem]:
    """
    Categorize papers using rule-based keyword matching.
    Provides fallback and classification for outliers.
    """
    topic_data = {t["name"]: {"paper_ids": [], "confidences": []} for t in TOPIC_GROUPS}
    topic_data["Other"] = {"paper_ids": [], "confidences": []}
    
    for paper in papers:
        title = paper.title or ""
        abstract = paper.abstract or ""
        summary = paper.summary or ""
        text = f"{title} {abstract} {summary}".lower()
        
        matched_any = False
        
        for topic in TOPIC_GROUPS:
            matched_kws = [kw for kw in topic["keywords"] if kw in text]
            if matched_kws:
                matched_any = True
                # Match confidence calculation as in Task 11 but capped and normalized
                confidence = round(min(1.0, len(matched_kws) / len(topic["keywords"]) + 0.3), 2)
                topic_data[topic["name"]]["paper_ids"].append(paper.id)
                topic_data[topic["name"]]["confidences"].append(confidence)
                
        if not matched_any:
            topic_data["Other"]["paper_ids"].append(paper.id)
            topic_data["Other"]["confidences"].append(0.5)  # Default lower confidence score for outlier/Other
            
    topics_response = []
    
    topic_meta = {t["name"]: t for t in TOPIC_GROUPS}
    topic_meta["Other"] = {
        "name": "Other",
        "description": "Fallback topic for papers that do not match any topic.",
        "keywords": []
    }
    
    for topic_name, data in topic_data.items():
        paper_ids = data["paper_ids"]
        if not paper_ids:
            continue
            
        confidences = data["confidences"]
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        meta = topic_meta[topic_name]
        
        paper_scores = {str(pid): conf for pid, conf in zip(paper_ids, confidences)}
        
        topics_response.append(TopicResponseItem(
            name=meta["name"],
            description=meta["description"],
            keywords=meta["keywords"],
            paper_ids=paper_ids,
            paper_scores=paper_scores,
            confidence_score=avg_confidence
        ))
        
    topics_response = sorted(topics_response, key=lambda x: len(x.paper_ids), reverse=True)
    return topics_response
