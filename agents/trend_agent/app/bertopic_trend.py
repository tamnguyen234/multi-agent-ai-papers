import logging
import numpy as np
from typing import List
from app.config import settings
from app.embeddings import EmbeddingEngine
from app.schemas import PaperItem, TopicResponseItem
from app.topic_naming import map_keywords_to_topic
from app.rule_based_trend import analyze_rule_based

logger = logging.getLogger(__name__)

def analyze_bertopic(papers: List[PaperItem]) -> List[TopicResponseItem]:
    """
    Cluster and categorize a list of papers using BERTopic with UMAP and HDBSCAN.
    """
    valid_papers = []
    documents = []
    
    for p in papers:
        title = p.title or ""
        abstract = p.abstract or ""
        summary = p.summary or ""
        doc_text = f"Title: {title}\nAbstract: {abstract}\nSummary: {summary}".strip()
        if len(doc_text) > 10:
            valid_papers.append(p)
            documents.append(doc_text)
            
    n_papers = len(valid_papers)
    # Check dataset size restriction
    if n_papers < 3:
        raise ValueError(f"Too few valid papers for BERTopic analysis (found {n_papers}, need at least 3).")
        
    logger.info(f"Running BERTopic analysis on {n_papers} documents...")
    
    # 1. Embed documents
    embeddings_model = EmbeddingEngine.get_instance().load_model()
    embeddings = embeddings_model.encode(documents, show_progress_bar=False)
    
    # 2. Setup UMAP with dynamic constraints
    n_neighbors = min(n_papers - 1, settings.TREND_UMAP_N_NEIGHBORS)
    if n_neighbors < 2:
        n_neighbors = 2
        
    n_components = min(n_papers - 2, settings.TREND_UMAP_N_COMPONENTS)
    if n_components < 2:
        n_components = 2
    if n_components >= n_papers:
        n_components = n_papers - 1 if n_papers > 2 else 2
        
    from umap import UMAP
    umap_model = UMAP(
        n_neighbors=n_neighbors,
        n_components=n_components,
        min_dist=0.0,
        metric='cosine',
        random_state=42
    )
    
    # 3. Setup HDBSCAN with dynamic constraints
    hdbscan_min_cluster_size = min(n_papers, settings.TREND_HDBSCAN_MIN_CLUSTER_SIZE)
    if hdbscan_min_cluster_size < 2:
        hdbscan_min_cluster_size = 2
        
    from hdbscan import HDBSCAN
    hdbscan_model = HDBSCAN(
        min_cluster_size=hdbscan_min_cluster_size,
        metric='euclidean',
        cluster_selection_method='eom',
        prediction_data=True
    )
    
    # 4. Fit BERTopic
    from bertopic import BERTopic
    from bertopic.vectorizers import ClassTfidfTransformer
    from sklearn.feature_extraction.text import CountVectorizer
    
    vectorizer_model = CountVectorizer(stop_words="english", min_df=1)
    ctfidf_model = ClassTfidfTransformer()
    
    topic_model = BERTopic(
        embedding_model=embeddings_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        ctfidf_model=ctfidf_model,
        top_n_words=settings.TREND_TOP_N_WORDS
    )
    
    topics, probs = topic_model.fit_transform(documents, embeddings)
    topic_info = topic_model.get_topics()
    
    # Check if BERTopic produced a valid result
    if not topic_info:
        raise ValueError("BERTopic model fit did not generate any topics.")
        
    # Group papers and scores by topic number
    grouped_papers = {}
    grouped_probs = {}
    
    for idx, topic_num in enumerate(topics):
        paper = valid_papers[idx]
        
        # Get probability/score for this assignment
        prob = 0.7  # Default confidence score
        if probs is not None:
            if isinstance(probs, (list, np.ndarray)):
                val = probs[idx]
                # If there are multiple topics probabilities returned, get the max
                if isinstance(val, (list, np.ndarray)):
                    prob = float(np.max(val))
                else:
                    prob = float(val)
            else:
                prob = float(probs)
                
        # Guard against zero or NaN probability
        if prob <= 0.0 or np.isnan(prob):
            prob = 0.7
            
        prob = round(prob, 2)
        
        if topic_num not in grouped_papers:
            grouped_papers[topic_num] = []
            grouped_probs[topic_num] = []
        grouped_papers[topic_num].append(paper)
        grouped_probs[topic_num].append(prob)
        
    topics_response = []
    
    # Build list of topics (skipping outlier topic -1)
    for topic_num, paper_list in grouped_papers.items():
        if topic_num == -1:
            continue
            
        raw_kws = [word for word, _ in topic_info.get(topic_num, [])]
        name, description = map_keywords_to_topic(raw_kws)
        
        paper_ids = [p.id for p in paper_list]
        paper_scores = {str(p.id): grouped_probs[topic_num][i] for i, p in enumerate(paper_list)}
        avg_confidence = round(sum(grouped_probs[topic_num]) / len(paper_list), 2)
        
        topics_response.append(TopicResponseItem(
            name=name,
            description=description,
            keywords=raw_kws,
            paper_ids=paper_ids,
            paper_scores=paper_scores,
            confidence_score=avg_confidence
        ))
        
    # 5. Handle outlier papers (topic -1) using rule-based classification
    outliers = grouped_papers.get(-1, [])
    if outliers:
        logger.info(f"Re-assigning {len(outliers)} outlier papers via rule-based keyword matching...")
        outlier_topics = analyze_rule_based(outliers)
        
        for o_topic in outlier_topics:
            # Check if this topic name already exists in topics_response
            existing_topic = next((t for t in topics_response if t.name == o_topic.name), None)
            if existing_topic:
                # Merge papers into existing topic
                existing_topic.paper_ids.extend(o_topic.paper_ids)
                if existing_topic.paper_scores is None:
                    existing_topic.paper_scores = {}
                for pid in o_topic.paper_ids:
                    # Assign a moderate confidence of 0.5 (or 0.4 for 'Other') for outlier mappings
                    confidence = 0.4 if o_topic.name == "Other" else 0.5
                    existing_topic.paper_scores[str(pid)] = confidence
                    
                # Recalculate average confidence score
                scores = list(existing_topic.paper_scores.values())
                existing_topic.confidence_score = round(sum(scores) / len(scores), 2)
            else:
                # Outliers form a new topic
                # Adjust confidence score of individual paper mappings
                for pid in o_topic.paper_ids:
                    confidence = 0.4 if o_topic.name == "Other" else 0.5
                    o_topic.paper_scores[str(pid)] = confidence
                scores = list(o_topic.paper_scores.values())
                o_topic.confidence_score = round(sum(scores) / len(scores), 2)
                topics_response.append(o_topic)
                
    if not topics_response:
        raise ValueError("BERTopic failed to classify any paper into a valid topic.")
        
    # Sort topics by paper_count descending
    topics_response = sorted(topics_response, key=lambda x: len(x.paper_ids), reverse=True)
    return topics_response
