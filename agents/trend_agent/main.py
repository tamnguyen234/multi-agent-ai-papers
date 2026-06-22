from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Any
import uvicorn
from trend_model.services import pipeline_service
import math

app = FastAPI(title="Trend Agent")

class PaperInput(BaseModel):
    id: int | str
    title: str
    abstract: str
    published: str

class AnalyzeRequest(BaseModel):
    papers: List[PaperInput]

@app.post("/analyze")
def analyze_trends(request: AnalyzeRequest):
    # Apply LLM FIX
    original_post = pipeline_service.requests.post
    def patched_post(url, json=None, **kwargs):
        if url == "http://localhost:11434/api/generate" and json:
            json["model"] = "llama3.2:1b"
            json["options"] = {"num_predict": 10, "stop": ["\n", ".", ","]}
        return original_post(url, json=json, **kwargs)
    pipeline_service.requests.post = patched_post
    
    # Generate embeddings
    texts_to_process = [f"{p.title}. {p.abstract}" for p in request.papers]
    vectors = pipeline_service.generate_embeddings(texts_to_process)
    
    class PaperModel:
        def __init__(self, p_dict):
            self.id = p_dict['id']
            self.title = p_dict['title']
            self.abstract = p_dict['abstract']
            self.published = p_dict['published']
            self.paper_vector = None
            self.umap_x = None
            self.umap_y = None

    papers_data = [PaperModel(p.dict()) for p in request.papers]
    
    for i, p in enumerate(papers_data):
        p.paper_vector = vectors[i].tolist()
        
    graph = pipeline_service.process_topic_clustering(None, papers_data)
    
    papers_res = [{"id": mp.id, "umap_x": mp.umap_x, "umap_y": mp.umap_y} for mp in papers_data]
    return {"graph": graph, "papers": papers_res}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
