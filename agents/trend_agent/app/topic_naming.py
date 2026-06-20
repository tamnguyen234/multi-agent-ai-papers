from typing import List

KEYWORD_MAPPINGS = [
    {
        "name": "Retrieval-Augmented Generation",
        "description": "Papers about RAG, retrieval, embedding, and knowledge-grounded generation.",
        "trigger_words": ["retrieval", "rag", "embedding", "vector", "faiss"]
    },
    {
        "name": "Multi-Agent Systems",
        "description": "Papers focusing on multi-agent cooperation, autonomous agents, workflows, and tool execution.",
        "trigger_words": ["agent", "multi-agent", "autonomous agent", "tool use", "planning", "workflow", "coordination"]
    },
    {
        "name": "Large Language Models",
        "description": "Papers related to large language models, transformers, prompting, and generative AI.",
        "trigger_words": ["llm", "language model", "transformer", "prompt", "generative ai", "gpt", "llama", "deepseek"]
    },
    {
        "name": "Computer Vision",
        "description": "Papers involving image processing, computer vision, visual generation, multimodal learning, and video modeling.",
        "trigger_words": ["computer vision", "image", "vision", "detection", "segmentation", "diffusion", "video", "multimodal", "yolo", "cnn"]
    },
    {
        "name": "Speech / Audio",
        "description": "Papers discussing speech recognition, audio processing, voice cloning, and text-to-speech generation.",
        "trigger_words": ["speech", "audio", "tts", "text-to-speech", "asr", "voice", "speaker", "whisper"]
    },
    {
        "name": "AI Safety",
        "description": "Papers investigating AI safety, model alignment, hallucination detection, bias mitigation, and trustworthiness.",
        "trigger_words": ["safety", "alignment", "hallucination", "bias", "robustness", "trustworthy", "jailbreak", "security"]
    },
    {
        "name": "Robotics",
        "description": "Papers analyzing robotics, control systems, and autonomous physical interactions.",
        "trigger_words": ["robot", "robotics", "manipulation", "control", "locomotion"]
    },
    {
        "name": "Reinforcement Learning",
        "description": "Papers analyzing reinforcement learning, rewards, policies, and environment interactions.",
        "trigger_words": ["reinforcement learning", "rl", "reward", "policy", "q-learning", "ppo"]
    },
    {
        "name": "AI Systems",
        "description": "Papers optimizing AI systems, latency reduction, GPU hardware usage, and distributed serving infrastructures.",
        "trigger_words": ["serving", "inference", "optimization", "latency", "distributed", "deployment", "hardware", "gpu", "efficiency"]
    }
]

def map_keywords_to_topic(keywords: List[str]) -> tuple:
    """
    Given a list of keywords from BERTopic, map them to a human-readable topic name
    and description. Returns (name, description).
    """
    if not keywords:
        return "Other", "Fallback topic for papers that do not match any topic."
        
    keywords_lower = [k.lower() for k in keywords]
    
    # Calculate score for each mapped topic based on trigger keyword overlaps
    best_match = None
    max_score = 0
    
    for mapping in KEYWORD_MAPPINGS:
        score = 0
        for trigger in mapping["trigger_words"]:
            for kw in keywords_lower:
                if trigger in kw or kw in trigger:
                    score += 1
        if score > max_score:
            max_score = score
            best_match = mapping
            
    if best_match and max_score > 0:
        return best_match["name"], best_match["description"]
        
    # If no pre-defined match, build a name dynamically from top keywords
    top_kws = [k for k in keywords if len(k) > 2][:3]
    if not top_kws:
        top_kws = keywords[:3]
    name = f"Topic: {', '.join(top_kws).title()}"
    description = f"Research papers primarily discussing {', '.join(keywords[:5])}."
    return name, description
