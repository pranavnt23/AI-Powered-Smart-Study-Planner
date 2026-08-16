import logging
import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.syllabus_topic import SyllabusTopic
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


class TopicImportanceService:
    """
    Dedicated Stage 12 service layers to calculate a unified continuous importance_score,
    a balanced priority level (High, Medium, Low), and generate explanations.
    """

    @classmethod
    def calculate_and_save_importance(cls, db: Session, document_id: uuid.UUID) -> List[Dict[str, Any]]:
        logger.info(f"Calculating Topic Importance weights for document ID: {document_id}")

        # 1. Retrieve all SyllabusTopics associated with this document
        topics = db.query(SyllabusTopic).filter(SyllabusTopic.document_id == document_id).all()
        if not topics:
            logger.warning(f"No syllabus topics found in PostgreSQL for document ID: {document_id}")
            return []

        # 2. Retrieve all related text chunks for keyword frequency checks
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()

        # 3. Calculate separate raw signals
        # Signal A: Syllabus Analyzer Score (already stored on the topic model as 0-10 float)
        
        # Signal B: Topic Frequency count inside document chunks
        frequency_counts = {}
        for t in topics:
            freq = sum(chunk.chunk_text.lower().count(t.topic_name.lower()) for chunk in chunks)
            frequency_counts[t.topic_name] = freq

        # Signal C: Dependency prerequisite transitive reachability count (DAG graph DFS)
        adj = {t.topic_name: [] for t in topics}
        for t in topics:
            if t.dependencies:
                # Comma-separated dependencies list
                deps = [d.strip() for d in t.dependencies.split(",") if d.strip()]
                for dep in deps:
                    # Find parent topic case-insensitively
                    for parent_t in topics:
                        if parent_t.topic_name.lower() == dep.lower():
                            adj[parent_t.topic_name].append(t.topic_name)

        def count_reachable(node: str, visited: set) -> int:
            visited.add(node)
            count = 0
            for child in adj.get(node, []):
                if child not in visited:
                    count += 1 + count_reachable(child, visited)
            return count

        reachability_weights = {}
        for t in topics:
            reachability_weights[t.topic_name] = count_reachable(t.topic_name, set())

        # Signal D: Difficulty mapping weights
        difficulty_mapping = {"easy": 1.0, "medium": 2.0, "hard": 3.0}
        difficulty_weights = {}
        for t in topics:
            level = (t.difficulty_level or "medium").lower().strip()
            difficulty_weights[t.topic_name] = difficulty_mapping.get(level, 2.0)

        # 4. Normalize signals helper
        def normalize(values: List[float]) -> List[float]:
            if not values:
                return []
            v_min = min(values)
            v_max = max(values)
            if v_max == v_min:
                # Fallback to balanced 1.0 if there is no variance
                return [1.0] * len(values)
            return [(v - v_min) / (v_max - v_min) for v in values]

        norm_syllabus = normalize([t.importance_score or 0.0 for t in topics])
        norm_prereq = normalize([reachability_weights[t.topic_name] for t in topics])
        norm_freq = normalize([frequency_counts[t.topic_name] for t in topics])
        norm_diff = normalize([difficulty_weights[t.topic_name] for t in topics])

        # 5. Compute unified weights score (Syllabus 40%, Prerequisite 25%, Frequency 20%, Difficulty 15%)
        final_scores = []
        for idx, t in enumerate(topics):
            score = (
                0.40 * norm_syllabus[idx] +
                0.25 * norm_prereq[idx] +
                0.20 * norm_freq[idx] +
                0.15 * norm_diff[idx]
            ) * 100.0
            final_scores.append(round(score, 1))

        # 6. Relative percentile-based priority classification (High top 25%, Low bottom 25%, Medium middle 50%)
        n = len(topics)
        indexed_scores = list(enumerate(final_scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        high_cutoff = max(1, round(n * 0.25))
        low_cutoff = max(1, round(n * 0.25))

        priorities = [None] * n
        for rank_idx, (orig_idx, score) in enumerate(indexed_scores):
            if rank_idx < high_cutoff:
                priorities[orig_idx] = "high"
            elif rank_idx >= n - low_cutoff:
                priorities[orig_idx] = "low"
            else:
                priorities[orig_idx] = "medium"

        # 7. Generate reasoning text and update records in PostgreSQL
        results = []
        for idx, t in enumerate(topics):
            priority = priorities[idx]
            score = final_scores[idx]
            prereqs = reachability_weights[t.topic_name]
            freq = frequency_counts[t.topic_name]

            # Construct dynamic reasoning description
            reasons_list = []
            if t.importance_score and t.importance_score > 7:
                reasons_list.append("has a high focus in the syllabus exam blueprint")
            if prereqs > 0:
                reasons_list.append(f"acts as a prerequisite for {prereqs} downstream topic(s)")
            if freq > 3:
                reasons_list.append("is frequently discussed throughout the study material chunks")
            if (t.difficulty_level or "").lower().strip() == "hard":
                reasons_list.append("contains highly complex material requiring extra master study time")

            reasoning = f"This topic is prioritized as {priority} priority (importance score: {score}/100). "
            if reasons_list:
                reasoning += "It " + ", and ".join(reasons_list[:-1]) + (" and " + reasons_list[-1] if len(reasons_list) > 1 else reasons_list[0]) + "."
            else:
                reasoning += "It has standard curriculum relevance and moderate complexity."

            # Update database record columns
            t.importance_score = score
            t.priority = priority
            t.reasoning = reasoning

            results.append({
                "topic_name": t.topic_name,
                "importance_score": score,
                "priority": priority,
                "difficulty": t.difficulty_level,
                "reasoning": reasoning
            })

        db.commit()
        logger.info(f"Successfully calculated and updated weights for {len(topics)} topics of document: {document_id}")
        return results
