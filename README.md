# TailoredLetter

> AI-powered RAG pipeline for generating personalized cover letters from job offers and a candidate's professional experience.

TailoredLetter is a Python application designed to automate the personalization of cover letters.

Instead of asking an LLM to generate a letter directly from a job description and a complete candidate profile, the application uses a **Retrieval-Augmented Generation (RAG)** pipeline to identify the experiences that are actually relevant to the target position.

The system progressively transforms a job offer into structured hiring requirements, retrieves matching professional experiences from a vector database, reranks them with an LLM, builds a writing strategy, and finally generates the cover letter.

## Table of Contents

* [Overview](#overview)
* [Architecture](#architecture)

  * [Application](#application)
  * [Services](#services)

    * [`OfferAnalyzer`](#offeranalyzer)
    * [`ExperienceRetriever`](#experienceretriever)
    * [`ExperienceReranker`](#experiencereranker)
    * [`LetterWriter`](#letterwriter)
  * [Infrastructures](#infrastructures)
  * [Schemas](#schemas)
* [RAG Pipeline](#rag-pipeline)

  * [1. Job offer ingestion](#1-job-offer-ingestion)
  * [2. Structured job analysis](#2-structured-job-analysis)
  * [3. Query generation](#3-query-generation)
  * [4. Vector retrieval](#4-vector-retrieval)
  * [5. Retrieval post-processing](#5-retrieval-post-processing)
  * [6. LLM reranking](#6-llm-reranking)
  * [7. Experience selection](#7-experience-selection)
  * [8. Writing plan](#8-writing-plan)
  * [9. Cover-letter generation](#9-cover-letter-generation)
* [Grounding and hallucination control](#grounding-and-hallucination-control)
* [Structured Outputs](#structured-outputs)
* [Architecture and Dependency Injection](#architecture-and-dependency-injection)
* [Persistence](#persistence)
* [Vector database](#vector-database)
* [Configuration](#configuration)
* [Technologies](#technologies)
* [Project structure](#project-structure)
* [Installation](#installation)
* [Qdrant](#qdrant)
* [Indexing candidate experiences](#indexing-candidate-experiences)
* [Running the pipeline](#running-the-pipeline)
* [Current state](#current-state)
* [Known limitations](#known-limitations)
* [Roadmap](#roadmap)
* [Technical Design Principles](#technical-design-principles)
* [Why RAG instead of a single LLM prompt?](#why-rag-instead-of-a-single-llm-prompt)
* [License](#license)
* [AI Assistance](#ai-assistance)
* [Human Verification](#human-verification)
* [Author](#author)

---

## Overview

Generating a convincing personalized cover letter requires more than simply asking an LLM to "write a letter for this job".

A candidate may have dozens of professional experiences, projects and skills, but only a subset of them is relevant to a particular position.

TailoredLetter therefore treats cover-letter generation as a **selection and evidence-matching problem**:

```text
Job Offer
    │
    ▼
Offer Extraction
    │
    ▼
Structured Job Analysis
    │
    ▼
Hiring Needs
    │
    ▼
Search Query Generation
    │
    ▼
Vector Retrieval
    │
    ▼
Retrieval Post-Processing
    │
    ▼
LLM Reranking
    │
    ▼
Relevant Experiences
    │
    ▼
Writing Plan
    │
    ▼
Cover Letter Generation
```

The objective is to provide the final LLM with a **small, relevant and evidence-based subset of the candidate's experience**, rather than the candidate's entire history.

---

# Architecture

The application is divided into several layers.

```text
                         ┌─────────────────────┐
                         │       main.py       │
                         │   Application Entry │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Application     │
                         │ Composition +       │
                         │ Pipeline            │
                         └──────────┬──────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
               ▼                    ▼                    ▼
        OfferAnalyzer       ExperienceRetriever   ExperienceReranker
               │                    │                    │
               │                    │                    │
               └────────────────────┼────────────────────┘
                                    │
                                    ▼
                              LetterWriter
                                    │
                                    ▼
                              Cover Letter
```

The main architectural layers are:

```text
Src/
├── Application/
├── Services/
├── Infrastructures/
├── Schemas/
├── Helpers/
└── config/
```

### Application

The `Application` layer is responsible for assembling the application and orchestrating the pipeline.

It contains:

* dependency construction;
* application composition;
* pipeline orchestration.

The application is built through a dedicated composition function:

```python
application = build_application(settings)
```

This keeps dependency construction outside the business logic and prevents `main.py` from becoming responsible for instantiating every component.

---

### Services

Services contain the application's business workflow.

#### `OfferAnalyzer`

Analyzes the job offer using an LLM and stores a structured representation of the hiring intent.

#### `ExperienceRetriever`

Transforms the identified needs into search queries and retrieves relevant candidate experiences from the vector database.

#### `ExperienceReranker`

Uses an LLM to compare retrieved experiences against the requirements of the job and assign a relevance score.

#### `LetterWriter`

Selects the highest-ranked experiences, verifies that enough relevant evidence exists, builds a strategic writing plan and generates the final cover letter.

---

### Infrastructures

The infrastructure layer contains external-system implementations.

It currently includes:

* LLM inference;
* Qdrant vector search;
* vector database indexing;
* retrieval post-processing;
* job-offer extraction.

This keeps external technologies isolated from the core workflow.

---

### Schemas

The application uses typed schemas to define the contracts between pipeline stages.

Examples include:

* `JobOfferInput`
* `JobAnalysisResponse`
* `Need`
* `Skill`
* `SearchQuery`
* `MinimalistRerank`
* `ExperienceEvaluation`
* `LetterPlan`

Pydantic models are used for structured LLM outputs, while dataclasses and typed dictionaries are used for internal application data.

---

# RAG Pipeline

## 1. Job offer ingestion

The pipeline starts with a job offer.

The application supports two ingestion modes.

### URL-based extraction

`offer_parser.py` can download the job page, remove irrelevant HTML elements and extract the textual content.

The extracted offer is represented as:

```python
JobOffer(
    title=...,
    url=...,
    content=...
)
```

### User-provided content

Some job boards may block automated requests.

For this reason, the application also supports providing the offer text directly.

This allows the rest of the pipeline to remain identical regardless of where the job description came from.

---

# 2. Structured job analysis

The raw job description is sent to the LLM using a structured-output schema.

The model does not directly write the cover letter.

Instead, it extracts the hiring intent of the company.

The analysis includes:

* job title;
* company context signals;
* hard skills;
* soft skills;
* hiring needs;
* priorities;
* implicit signals;
* ideal experience signals;
* differentiating signals;
* potential cover-letter angles;
* mandatory elements.

A simplified representation looks like:

```json
{
  "needs": [
    {
      "name": "Data analysis",
      "priority": 1,
      "description": "...",
      "implicit_signals": ["..."],
      "impact_area": "..."
    }
  ]
}
```

The output is validated using Pydantic before being used by the following stages.

This creates a stable contract between the LLM analysis stage and the retrieval pipeline.

---

# 3. Query generation

Each identified hiring need is transformed into a semantic search query.

A query combines:

* the need name;
* its description;
* implicit signals;
* priority;
* impact area.

For example:

```text
Need:
"Automatisation des processus"

Description:
"Capacité à identifier et automatiser des tâches répétitives"

Implicit signals:
["amélioration de la productivité", "structuration"]

→

Semantic query:
"Automatisation des processus capacité identifier automatiser
tâches répétitives amélioration productivité structuration"
```

The objective is to search for **evidence of the underlying capability**, rather than simply matching the exact words of the job offer.

---

# 4. Vector retrieval

Candidate experiences are indexed in Qdrant using embeddings.

The current embedding model is:

```text
intfloat/multilingual-e5-large
```

The model is particularly useful for multilingual semantic retrieval.

For E5-style embeddings, documents are indexed using:

```text
passage:
```

while retrieval queries use:

```text
query:
```

The retrieval process is:

```text
Job Requirement
      │
      ▼
Search Query
      │
      ▼
Embedding
      │
      ▼
Qdrant
      │
      ▼
Top-K Chunks
```

The system retrieves chunks rather than entire experiences.

This allows a specific part of an experience to match a particular requirement.

---

# 5. Retrieval post-processing

The raw vector search results are transformed before being passed to the reranker.

The post-processing stage:

* associates retrieved chunks with the corresponding experience;
* keeps the associated job requirement;
* preserves the section from which the chunk originated;
* removes duplicate chunks;
* groups information by experience.

The goal is to transform:

```text
query → chunk → score
```

into a richer representation:

```text
experience
├── section
├── content
├── retrieved_for
└── associated job needs
```

This gives the reranking model enough context to reason about the relevance of the complete experience.

---

# 6. LLM reranking

Vector similarity alone is not sufficient.

A semantically similar experience is not necessarily the best evidence for a recruiter.

The system therefore introduces a second ranking stage using an LLM.

The reranker compares the retrieved experiences against the identified job requirements.

Each experience receives:

* a relevance score;
* a rank;
* a decision;
* a short justification.

The current decision categories are:

```text
0–39   → reject
40–69  → possible
70–100 → strong_match
```

The reranking prompt explicitly instructs the model to:

* compare experiences against each other;
* use only the provided evidence;
* prefer direct evidence over generic transferable skills;
* prefer demonstrated achievements;
* assign unique ranks.

This creates a two-stage retrieval architecture:

```text
                Candidate Experiences
                         │
                         ▼
                 Vector Retrieval
                  high recall
                         │
                         ▼
                    LLM Rerank
                 high relevance
                         │
                         ▼
                 Top Experiences
```

---

# 7. Experience selection

The highest-ranked experiences are selected according to the configured `reranking_top_k`.

Before generating a letter, the application also checks the relevance threshold.

If the retrieved evidence is not sufficiently relevant, the system does not proceed with the final generation.

This prevents the model from being forced to construct a convincing narrative from weak evidence.

---

# 8. Writing plan

The selected experiences are then combined with:

* the structured job analysis;
* the candidate's complete experience data;
* personal facts;
* the job description.

A dedicated LLM generates a structured `LetterPlan`.

The plan contains:

```text
Main message
    │
    ├── Priority experiences
    ├── Key arguments
    ├── Transferable qualities
    ├── Gaps
    ├── Letter structure
    ├── Must include
    └── Must avoid
```

The purpose of this intermediate step is to separate:

```text
"what should be said?"
```

from:

```text
"how should it be written?"
```

This avoids asking a single LLM call to simultaneously perform retrieval reasoning, candidate selection, argument construction and prose generation.

---

# 9. Cover-letter generation

The final LLM receives:

1. the job analysis;
2. candidate information;
3. the selected experiences;
4. the writing plan.

The writing prompt explicitly prohibits inventing:

* skills;
* technologies;
* responsibilities;
* experiences;
* results;
* metrics;
* company knowledge;
* motivations;
* professional achievements.

The intended generation principle is:

```text
Claim
  ↓
Evidence
  ↓
Relevance to the job
```

Rather than:

```text
Generic claim
  ↓
Generic claim
  ↓
Generic claim
```

The final output is a structured response containing the generated letter.

---

# Grounding and hallucination control

One of the central design goals of the project is to keep the generated letter grounded in the candidate's actual experience.

The LLM is therefore not given unrestricted freedom to invent a candidate profile.

The pipeline progressively reduces the information available to the final generation:

```text
Complete Candidate Profile
          │
          ▼
Relevant Experiences
          │
          ▼
Reranked Experiences
          │
          ▼
Selected Evidence
          │
          ▼
Writing Plan
          │
          ▼
Final Letter
```

The final model is instructed to use the candidate information and selected evidence as the source of truth.

This is an important distinction from a simple prompt-based cover-letter generator.

---

# Structured Outputs

Structured outputs are used throughout the reasoning pipeline.

For example:

```python
JobAnalysisResponse
```

defines the expected structure of the job analysis.

Similarly:

```python
MinimalistRerank
```

defines the expected reranking result, and:

```python
LetterPlan
```

defines the writing strategy.

This provides:

* predictable interfaces between LLM calls;
* validation of generated data;
* easier debugging;
* easier downstream processing;
* less reliance on parsing arbitrary LLM text.

---

# Architecture and Dependency Injection

The application uses explicit dependency injection.

The LLM client is instantiated once:

```python
llm = LlmInference(settings=settings)
```

and injected into the services that require it:

```text
                 LlmInference
                 /     |     \
                /      |      \
               ▼       ▼       ▼
          Analyzer  Reranker  Writer
```

Similarly, `OfferRepository` and `VectorSearch` are injected into the relevant services.

This keeps the services testable and separates dependency construction from business logic.

---

# Persistence

The current pipeline uses JSON files as an intermediate persistence layer.

The `OfferRepository` provides a small abstraction around:

```python
load(path)
save(path, data)
```

The offer JSON progressively contains the results of the different pipeline stages.

Conceptually:

```text
Offer
  │
  ├── offer_analysis
  │
  ├── retrieval
  │
  ├── rerank
  │
  ├── plan
  │
  └── letter
```

This approach is intentionally simple for the current stage of the project.

A future version could replace this file-based state management with dedicated domain objects or a database.

---

# Vector database

Qdrant is used to store the candidate's experience chunks.

Each indexed chunk contains:

* an embedding;
* the experience identifier;
* the section;
* the chunk content;
* metadata.

Document identifiers are generated deterministically from:

```text
experience + section + chunk
```

using UUID5.

This makes repeated indexing idempotent at the document-ID level.

The vector indexer also supports batch embedding generation.

---

# Configuration

Application configuration is centralized using `pydantic-settings`.

Configuration covers:

* LLM credentials;
* LLM model;
* system prompts;
* embedding model;
* Qdrant connection;
* retrieval parameters;
* reranking parameters;
* candidate data sources.

Configuration is loaded from environment variables and a local `.env` file during development.

A `.env.example` file is provided as a template.

Do not commit real API keys.

---

# Technologies

## Language

* Python

## LLM

The application uses an OpenAI-compatible chat-completion interface with structured outputs.

The model, API key and endpoint are configurable through environment variables.

This allows the inference provider to be changed without modifying the business services.

## Retrieval

* Qdrant
* `intfloat/multilingual-e5-large`
* LangChain HuggingFace embeddings
* PyTorch

## LLM integration

* OpenAI Python SDK
* Pydantic
* pydantic-settings

## Job-offer extraction

* Requests
* BeautifulSoup

---

# Project structure

```text
TailoredLetter/
│
├── Prompts/
│   ├── offer_analysis_structured.txt
│   ├── reranking.txt
│   ├── plan_writing.txt
│   └── write_lm.txt
│
├── Src/
│   │
│   ├── Application/
│   │   ├── build_application.py
│   │   └── pipeline.py
│   │
│   ├── Services/
│   │   ├── offer_analyzer.py
│   │   ├── write_queries.py
│   │   ├── experience_retriever.py
│   │   ├── experience_reranker.py
│   │   └── letter_writer.py
│   │
│   ├── Infrastructures/
│   │   ├── offer_parser.py
│   │   ├── llm_inference.py
│   │   ├── vector_search.py
│   │   ├── vector_db.py
│   │   └── retrieval_post_processing.py
│   │
│   ├── Schemas/
│   │   ├── application.py
│   │   ├── job_offer_input.py
│   │   ├── job_analysis.py
│   │   ├── experiences.py
│   │   ├── search_query.py
│   │   ├── rerank_format.py
│   │   ├── write_plan.py
│   │   └── write_cover_letter.py
│   │
│   ├── Helpers/
│   │   └── OfferRepository.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── main.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/ArthurCoquet/TailoredLetter.git
cd TailoredLetter
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Requirements

* Python **3.14.5**
* CUDA-compatible GPU recommended for local embedding inference
* Qdrant
* An OpenAI-compatible LLM API
* Hugging Face access for the embedding model

### Python dependencies

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

The project currently relies on:

* `openai` — LLM inference
* `pydantic-settings` — configuration management
* `python-dotenv` — environment variables
* `beautifulsoup4` — job offer parsing
* `requests` — HTTP requests and web scraping
* `PyYAML` — YAML-related utilities
* `qdrant-client[fastembed]` — vector database access
* `langchain-huggingface` — Hugging Face embedding integration
* `sentence-transformers` — embedding models
* `torch` — tensor computation and GPU acceleration
* `torchvision` — PyTorch ecosystem dependency

### Python version

The project is currently **tested exclusively with Python 3.14.5**.

Other Python versions may work, but they are not currently part of the tested configuration.


The project currently includes a PyTorch CUDA package index in `requirements.txt`. For a CPU-only environment, the dependency configuration may need to be adapted.

---

# Configuration

Create a `.env` file from the provided example:

```bash
cp .env.example .env
```

On Windows, copy the file manually if necessary.

Configure the LLM:

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=your_provider_base_url
OPENAI_MODEL=your_model
```

Configure embeddings:

```env
HF_TOKEN=
EMBEDDING_MODEL=intfloat/multilingual-e5-large
```

Configure Qdrant:

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=experiences
```

Configure retrieval:

```env
RETRIEVAL_TOP_K=10
RERANKING_TOP_K=3
SCORE_THRESHOLD=0
```

Configure the data sources:

```env
COMPLETE_EXPERIENCES_FILEPATH=Docs/experiences.json
PERSONAL_FACTS_FILEPATH=Docs/personal_facts.json
```

The prompt paths can also be configured through environment variables.

---

# Qdrant

The application expects a Qdrant instance.

A local instance can be started with Docker:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

The Qdrant dashboard is then available at:

```text
http://localhost:6333/dashboard
```

---

# Indexing candidate experiences

Before retrieval can be performed, the candidate's experiences must be indexed in Qdrant.

The indexing pipeline:

```text
Experience Data
      │
      ▼
Chunking / Structured Experience
      │
      ▼
E5 Embeddings
      │
      ▼
Qdrant Collection
```

The indexer:

* creates the collection if necessary;
* computes embeddings;
* generates deterministic document IDs;
* stores embeddings and metadata;
* upserts the documents.

---

# Running the pipeline

The current entry point is:

```bash
python Src/main.py
```

The application currently constructs a `JobOfferInput` and passes it to the pipeline.

The intended workflow is:

```python
job_offer = JobOfferInput(
    url="...",
    title="...",
    content="..."
)

await pipeline(
    application=application,
    job_offer=job_offer
)
```

The pipeline then executes:

```text
Offer ingestion
      ↓
Offer analysis
      ↓
Query generation
      ↓
Vector retrieval
      ↓
Experience reranking
      ↓
Experience selection
      ↓
Writing plan
      ↓
Cover letter generation
```

---

# Current state

## Implemented

* Job-offer ingestion from URL or provided text
* HTML cleaning and text extraction
* Structured LLM analysis
* Pydantic validation of LLM outputs
* Hiring-needs extraction
* Semantic query generation
* Vector embeddings
* Qdrant indexing
* Batch vector retrieval
* Retrieval post-processing
* Experience grouping
* LLM-based experience reranking
* Relevance thresholds
* Experience selection
* Structured cover-letter planning
* Final cover-letter generation
* Centralized configuration
* Dependency injection
* Application-level pipeline orchestration

---

# Known limitations

The project is currently a working prototype and several areas can still be improved.

### File-based state

Intermediate pipeline results are currently stored in JSON files.

This is simple and useful during development but is not yet ideal for a production application.

### Retrieval quality

The current retrieval stage is based primarily on semantic vector search.

Keyword-based retrieval and more advanced hybrid strategies are not yet implemented.

### Reranking

The current reranking stage relies on an LLM.

A dedicated cross-encoder reranker could provide a more deterministic and potentially cheaper second-stage ranking.

### Evaluation

A major next step is to create a reproducible evaluation dataset containing:

* job offers;
* expected relevant experiences;
* retrieval results;
* reranking judgments;
* final letter quality criteria.

This would make it possible to measure improvements rather than evaluating the system only through manual inspection.

### External dependencies

The application currently depends on:

* an LLM API;
* Qdrant;
* a local embedding model.

---

# Roadmap

## Retrieval

* [ ] Hybrid retrieval: BM25 + vector search
* [ ] Cross-encoder reranking
* [ ] Better chunking strategies
* [ ] Retrieval evaluation dataset
* [ ] Recall@K / Precision@K / MRR evaluation
* [ ] Better handling of multiple needs and priorities

## Generation

* [ ] Improve writing-plan evaluation
* [ ] Improve factual-grounding checks
* [ ] Automatic letter quality evaluation
* [ ] Stylistic personalization
* [ ] Better handling of missing candidate evidence

## Architecture

* [ ] Reduce the JSON file as an intermediate communication mechanism
* [ ] Introduce stronger domain models between pipeline stages
* [ ] Improve service interfaces
* [ ] Add automated tests
* [ ] Improve lifecycle management of external clients
* [ ] Add dependency injection for more infrastructure components

## Product

* [ ] Command-line interface
* [ ] Web API
* [ ] User interface
* [ ] Multiple candidate profiles
* [ ] Application history
* [ ] Export generated letters

---

# Technical Design Principles

TailoredLetter follows several principles.

### Retrieval before generation

The final LLM should not decide which parts of the candidate's entire history are relevant from scratch.

The system first retrieves and ranks evidence.

### Structured reasoning

Intermediate LLM outputs are represented using explicit schemas instead of arbitrary text.

### Evidence-based generation

Experiences are selected because they provide evidence for requirements of the target position.

### Separation of responsibilities

The application separates:

```text
Business logic
      │
      ├── Services
      │
      ├── Application orchestration
      │
      ├── Infrastructure
      │
      └── Data schemas
```

### Configurable infrastructure

LLM configuration, embedding model, Qdrant connection and retrieval parameters are externalized through application settings.

---

# Why RAG instead of a single LLM prompt?

A simple implementation could provide the complete candidate profile and job description to an LLM and ask it to generate a cover letter.

This approach has several weaknesses:

* too much irrelevant candidate information;
* less control over experience selection;
* higher risk of unsupported claims;
* difficult-to-debug decisions;
* difficult-to-evaluate retrieval quality;
* no explicit separation between matching and generation.

TailoredLetter instead decomposes the problem:

```text
Understanding the job
        +
Finding evidence
        +
Ranking evidence
        +
Building an argument
        +
Writing
```

This makes each stage independently observable and improvable.

---

# License

This project is released under the MIT License.

See [`LICENSE`](LICENSE) for details.

---

# AI Assistance

The project's architecture, implementation and Python code were designed and written by the author.

AI tools were used selectively as development assistance, primarily for:

* README documentation;
* refinement and iteration of some system prompts;
* occasional technical discussion and review.

The core architecture, RAG pipeline, service design, schemas, retrieval strategy and implementation were developed and validated by the author.

# Human Verification

The generated cover letter is systematically reviewed by the author before being used.

This final human verification step is intended to ensure that:

* factual claims accurately reflect the candidate's actual experience;
* no unsupported skills, responsibilities or achievements have been introduced;
* dates, technologies, metrics and other concrete details are correct;
* the final letter remains consistent with the candidate's professional background.

The RAG pipeline and generation constraints are designed to reduce unsupported content, but the final human review remains the ultimate verification step.

---

# Author

Developed by Arthur Coquet as an exploration of RAG architectures, LLM-based information extraction, semantic retrieval, reranking and controlled text generation applied to personalized job applications.
