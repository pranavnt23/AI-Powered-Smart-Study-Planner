# Phase 2 Architecture Review - Advanced RAG Pipeline

This document reviews and summarizes all Phase 2 Retrieval-Augmented Generation (RAG) enhancements completed in the AI Smart Study Planner project. It outlines the architectural evolution, component definitions, service responsibilities, and data flow patterns of the upgraded production-grade retrieval pipeline.

---

## 1. Phase 2 Overview

Phase 2 aimed to transform a basic, single-stage retrieval pipeline into an advanced, production-oriented two-stage RAG architecture. The goal of this phase was to improve search accuracy, enable context-aware conversations, ensure explainability through grounded citations, and optimize performance.

### RAG Pipeline Evolution

#### Before Phase 2 (Naive RAG)
```
User Query
    │
    ▼
Embedding Generation
    │
    ▼
Vector Search (ChromaDB ANN)
    │
    ▼
LLM Response (Ollama Generation)
```

#### After Phase 2 (Advanced Production RAG)
```
User Query
    │
    ▼
Conversation Memory (Persistent SQL dialogue lookup)
    │
    ▼
Query Processing (Coreference query resolution)
    │
    ▼
Hybrid Retrieval (Parallel Vector Search + BM25 Lexical candidate selection)
    │
    ▼
Re-Ranking (Neural Cross-Encoder context re-ordering)
    │
    ▼
Citation Mapping (Grounded source regex matching)
    │
    ▼
Prompt Construction (XML-structured injection-resistant prompt builder)
    │
    ▼
LLM Response (Ollama streaming answers + citations metadata payload)
```

### Evolution Summary
The initial naive RAG implementation suffered from context dilution, lexical search gaps, and hallucinations, and could not resolve follow-up questions or pronouns. 

To solve this, the pipeline was upgraded to a two-stage retrieval architecture:
1. **Recall Stage (Hybrid Search):** Casts a wider retrieval net ($M = 15$) using vector similarity and BM25 lexical keyword search in parallel, guaranteeing that relevant items are not missed.
2. **Precision Stage (Neural Re-ranking):** Employs a local Cross-Encoder transformer model to evaluate candidate-query relationships in detail, filtering down to the best $N = 4$ context blocks to construct the LLM prompt.

---

## 2. Phase 2 Completed Components

| Component | Responsibility | Input | Output | Why it exists |
| :--- | :--- | :--- | :--- | :--- |
| **1. Embedding Service** | Generates normalized dense vector embeddings using a local model. | Cleaned document chunk string / Search query | 384-dimensional floating-point vector | Maps conceptual text fragments to spatial coordinates in a vector space. |
| **2. Vector Database** | Persists, indexes, and queries high-dimensional vectors. | Embedding vectors, text, metadata dicts | Cosine similarity nearest neighbors | Provides fast, sub-millisecond semantic search across document collections. |
| **3. Retrieval Service** | Coordinates semantic, lexical, and neural retrieval pipelines. | Search query, session details, metadata filters | Consolidated Top-N chunk records | Acts as the orchestrator that manages data flow between search indices and fusion layers. |
| **4. Citation Service** | Detects context usage and maps document sources. | Generated answer text, context chunks | Annotated text, structured citations list | Ensures explainability and grounding, preventing hallucinations by attributing sources. |
| **5. Metadata Mapping** | Applies query parameters to restrict search scope. | User and document parameters | ChromaDB `$where` filters / SQL filters | Restricts the candidate search pool to enforce tenant privacy and single-document chat focus. |
| **6. Conversation Memory** | Persists and loads rolling multi-turn conversations. | Session metadata, dialogue message | Chronological sliding window history | Keeps track of context across multi-turn chats, enabling follow-up question answering. |
| **7. Hybrid Search** | Blends conceptual matches with exact keyword matches. | Search query, document candidates | Fused ranking list (via RRF) | Solves term-matching failures in vector search and synonym-matching failures in keyword search. |
| **8. Re-Ranking** | Refines and re-scores candidates using full attention models. | Standalone query, coarse candidates pool | Relevance-sorted Top-N chunks | Re-scores candidates using detailed query-document word matches, placing the best answer at the top. |

---

## 3. Final Phase 2 Architecture

### Document Upload & Ingestion Pipeline
```
Documents (PDF, TXT, DOCX, PPTX)
    │
    ▼
Document Processor (File-type routing)
    │
    ▼
Text Extraction (Hybrid PDF layout parsing + slides/tables text parsing)
    │
    ▼
Chunking Service (Recursive token-bounded token character split)
    │
    ▼
Embedding Service (all-MiniLM-L6-v2) ──► Chunks persisted in PostgreSQL
    │
    ▼
ChromaDB Collection (HNSW Vector Space)
```

### Query & Context Extraction Pipeline
```
User Question
    │
    ▼
Conversation Memory (Loads last 6 dialogue messages from PostgreSQL `chat_messages` table)
    │
    ▼
Query Processing (Ollama rewrites query using history to expand pronouns)
    │
    ├───► Semantic Search (Query Vector similarity search in ChromaDB, top_k=15)
    │
    └───► Keyword Search (BM25Okapi local keyword candidate search on database, top_k=15)
    │
    ▼
Score Fusion (Reciprocal Rank Fusion (RRF) combines candidate lists, k=60)
    │
    ▼
Top-15 Candidate Chunks
    │
    ▼
Re-Ranking (Neural Cross-Encoder re-scores candidates, top_k=4)
    │
    ▼
Top-4 Relevant Chunks
    │
    ▼
Citation Service (Applies regex to extract reference indexes [doc_x] in output)
    │
    ▼
Prompt Builder (Compiles system prompt, XML context chunks, history, and query)
    │
    ▼
LLM (Ollama streams answer token-by-token)
    │
    ▼
Final Fused Answer + Citations JSON Metadata Payload
```

---

## 4. Service Responsibilities

### `embedding_service.py`
- Generates normalized 384-dimensional vectors.
- Manages the local `sentence-transformers/all-MiniLM-L6-v2` embedding model.
- Converts raw text inputs into vector representations.

### `retrieval_service.py`
- Orchestrates the full semantic and lexical context retrieval process.
- Coordinates calls to VectorStore, BM25, and neural re-ranking services.
- Returns candidate document chunks matching user scope parameters.

### `hybrid_search_service.py`
- Performs BM25 lexical term indexing and calculation across candidates.
- Combines sparse keyword search and dense vector search results using Reciprocal Rank Fusion (RRF).

### `reranking_service.py`
- Re-evaluates document sequence using a local Cross-Encoder transformer model.
- Performs semantic verification using query-document cross-attention scoring.
- Selects the final top relevance context chunks.

### `citation_service.py`
- Tracks source file names and indices to match context mappings.
- Re-indexes bracketed tags to ensure they match final user-facing citation lists.

### `memory_service.py`
- Directs CRUD database queries to load session history records from SQLAlchemy database bindings.
- Handles rolling context window limits for LLM query expansions.

### `prompt_builder.py`
- Outlines formatting constraints and system prompt instructions.
- Combines grounding context blocks, conversation dialogue records, and user queries.

### `llm_service.py`
- Formulates HTTP stream requests to Ollama API routes.
- Handles response streams and executes prompt query expansions.

---

## 5. Retrieval Flow Explanation

Here is the step-by-step lifecycle of a user request:

1. **User Sends Query:** The user submits a question through the chat interface.
2. **Memory Enrichment:** `MemoryService` fetches the last 6 dialogue messages to retain conversational context.
3. **Query Expansion:** The query rewriter expands the prompt, resolving any pronouns into concrete search terms.
4. **Embedding Generation:** The expanded query is converted into a 384-dimensional vector.
5. **Parallel Hybrid Search:**
   - **Semantic Search:** ChromaDB retrieves matches representing high-level conceptual similarity.
   - **Keyword Search:** A database query returns exact lexical character matches.
6. **Score Fusion:** The outputs are combined using Reciprocal Rank Fusion (RRF).
7. **Candidate Retrieval:** The pipeline generates a coarse pool of 15 candidate chunks.
8. **Neural Re-ranking:** A local Cross-Encoder model scores the candidates based on query-document relevance.
9. **Top-N Selection:** The top 4 highest-scoring chunks are selected for the context block.
10. **Citation Metadata Attachment:** The citation service validates source document indexes.
11. **Context Construction:** The prompt builder assembles the grounded context prompt.
12. **LLM Generation:** Ollama streams the final citation-grounded response.

---

## 6. Phase 2 AI Concepts Implemented

### Embeddings
- Numerical vector representations of text strings.
- Encodes high-dimensional semantic relationships, allowing the model to match synonyms and concepts.

### Vector Search
- High-speed retrieval of vectors using distance metrics (like Cosine Similarity) inside ChromaDB.

### Semantic Search
- Concept-based query matching that evaluates semantic intent rather than raw characters.

### Keyword Search
- Exact character sequence retrieval using term statistics (BM25 Okapi), matching names, IDs, numbers, and codes.

### Hybrid Search
- Combines sparse lexical matches and dense vector matches to improve retrieval accuracy.

### Re-Ranking
- An attention-based neural scoring step (Cross-Encoder) that re-scores candidate documents to verify query relevance.

### Conversation Memory
- Dialogue state preservation that allows the system to resolve follow-up questions and pronouns over multi-turn conversations.

### Citation Mapping
- Regex validation that maps generated answers to source citations, preventing hallucinations.

---

## 7. Data Flow Between Components

### Ingestion & Embedding Flow
```
Text Chunk ──► Embedding Model (all-MiniLM-L6-v2) ──► 384-dim Vector ──► ChromaDB Vector Space
```

### Context Retrieval Flow
```
Query ──► Query Expanded ──► [Hybrid Search (Vector + BM25)] ──► RFF ──► Re-Ranker ──► Top-4 Chunks
```

### Generation Flow
```
Top-4 Chunks + Query + Memory ──► Prompt Builder ──► Ollama (LLM) ──► Citation Service ──► User
```

---

## 8. Design Decisions

### 1. ChromaDB Vector Database Choice
- **Problem:** Needs a lightweight, persistent vector index for local development.
- **Decision:** Integrated **ChromaDB** with a persistent local folder storage path.
- **Benefit:** Simplifies setup and minimizes memory usage on local hardware.

### 2. Sentence Transformers Embedding Choice
- **Problem:** Generating embeddings and re-ranking requires lightweight, high-quality models.
- **Decision:** Selected `all-MiniLM-L6-v2` for embeddings and `ms-marco-MiniLM-L-6-v2` for re-ranking.
- **Benefit:** Both models run locally on CPU in milliseconds, keeping the pipeline free and private.

### 3. Separation of the Citation Service
- **Problem:** LLM models can generate false or hallucinated source citations.
- **Decision:** Created a distinct post-processing citation parser (`CitationService`).
- **Benefit:** Validates citations against the provided context, filtering out hallucinations before they reach the user.

### 4. Database-Backed Memory Service
- **Problem:** Dialog memory must persist across system restarts and user sessions.
- **Decision:** Implemented a PostgreSQL-backed sliding window memory using SQLAlchemy.
- **Benefit:** Session histories are persistent, and sliding window queries are optimized via standard database indexes.

---

## 9. Production Readiness Analysis

### Scalability
- The PostgreSQL `chat_messages` table handles scaling through index scopes on `session_id`.
- Hybrid retrieval is fast, limiting candidate pools before BM25 checks. Re-ranking latency scales independently of database size since it operates on a small candidate set.

### Maintainability
- Clean separation of concerns between retrieval pipelines, database models, and route controllers.

### Accuracy
- Hybrid retrieval and neural re-ranking reduce false positives, improving the quality of the LLM context.

### Explainability
- Users can verify the exact document and page number that generated an answer, ensuring source transparency.

---

## 10. Phase 2 Limitations

- **No Advanced Query Rewriting:** The query rewriter uses a basic prompt template. It does not support complex techniques like sub-query decomposition or HyDE.
- **No Agentic Routing:** The system cannot determine if a query requires external search or can be answered conversationally.
- **No Automatic Evaluation Framework:** The system lack automated regression testing to measure retrieval recall and faithfulness over time.
- **No Production Monitoring:** No integration with LLM tracing tools (like LangSmith or Arize Phoenix).

---

## 11. Phase 2 Testing Strategy

The advanced RAG pipeline is validated by a 19-test suite:

- **Retrieval Testing:** Evaluates query pre-filtering and hybrid vector/lexical candidate fusion.
- **Conversation Testing:** Verifies dialogue serialization, sliding window history loading, and query expansion.
- **Citation Testing:** Validates source matching, index shifts, and the removal of hallucinated tags.
- **Performance Testing:** Measures latency metrics during local model execution.

---

## 12. Phase 2 Final Outcome

Through Phase 2, the AI Smart Study Planner's basic RAG pipeline was upgraded into a production-grade conversational search architecture. 

By combining **parallel hybrid search**, **logical pre-filtering**, **neural re-ranking**, and **regex-based citation mapping**, the system provides highly relevant, context-grounded, and traceable answers. It handles complex follow-up questions while maintaining low query latency on standard local developer machines.
