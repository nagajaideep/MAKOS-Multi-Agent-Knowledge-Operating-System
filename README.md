# MAKOS - Multi-Agent Knowledge Operating System

MAKOS (Multi-Agent Knowledge Operating System) is a unified AI platform that combines knowledge management, Retrieval-Augmented Generation (RAG), natural language database interaction, multi-agent orchestration, persistent memory, and workflow automation into a single modular system.

## Project Information

- **Project:** Multi-Agent Knowledge Operating System (MAKOS)
- **Course:** Project Stage - I (CM752PC)
- **Department:** Emerging Technologies (CSM & CSD)
- **Program:** B.Tech CSE (AI & ML)
- **Academic Year:** 2026-27
- **Semester:** VII
- **Team Size:** 4

## Team

| Member | Responsibility |
|---|---|
| Person 1 | Team Lead — Architecture, Integration & Coordination |
| Person 2 | Knowledge Management & Database Layer |
| Person 3 | RAG Pipeline & Multi-Agent Orchestration |
| Person 4 | API, Workflow Interface & Testing |

All members report progress, blockers, and completed work to **Person 1**, who owns final integration and Pull Request review.

---

## 1. Problem Statement

Organizations often use separate systems for document management, knowledge retrieval, database interaction, and workflow automation. This fragments information access and makes it difficult to perform tasks that require pulling from multiple sources at once.

MAKOS solves this by providing a unified AI platform where specialized agents retrieve information, interact with structured and unstructured data, reason over retrieved knowledge, and execute workflows — all through one interface.

---

## 2. Objectives

1. Build a unified multi-agent AI platform for knowledge management and workflow automation.
2. Implement Retrieval-Augmented Generation (RAG).
3. Enable natural-language interaction with databases and documents.
4. Develop a multi-agent orchestration system for task planning and execution.
5. Implement persistent contextual memory.
6. Provide workflow automation capabilities.
7. Evaluate retrieval accuracy, execution efficiency, scalability, and overall system performance.

---

## 3. Proposed Architecture

```text
                         USER
                           |
                           v
                 +-------------------+
                 |   Frontend / API  |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |   Main Controller |
                 |   / Router Agent  |
                 +---------+---------+
                           |
              +------------+------------+
              |            |            |
              v            v            v
        +----------+  +----------+  +----------+
        | RAG      |  | Database |  | Workflow |
        | Agent    |  | Agent    |  | Agent    |
        +----+-----+  +----+-----+  +----+-----+
             |             |             |
             v             v             v
       Vector Store    SQL Database   Tools/APIs
             |
             v
       Document Store
             |
             v
       Knowledge Base

                 +-------------------+
                 | Persistent Memory |
                 +-------------------+
```

The exact architecture can evolve during implementation.

---

## 4. Major Components

### 4.1 User Interface

Users interact with MAKOS using natural language, e.g.:

```text
"Find all documents related to employee leave policy
and tell me the maximum number of paid leaves."
```

### 4.2 Controller / Router

The controller receives the request and decides which agent(s) should handle it:

```text
User Query
    |
    v
Router
    |
    +----> RAG Agent
    |
    +----> Database Agent
    |
    +----> Workflow Agent
```

For complex queries, the controller coordinates multiple agents.

---

## 5. RAG System

```text
Documents -> Document Loader -> Text Extraction -> Chunking -> Embedding Model
   -> Vector Database -> Retriever -> Relevant Documents -> LLM -> Final Answer
```

Supports: document ingestion, text extraction, chunking, embedding generation, vector storage, similarity search, context retrieval, and LLM-based answer generation.

---

## 6. Knowledge Management

A centralized knowledge layer covering PDFs, text documents, structured databases, and other sources, with efficient semantic retrieval.

Candidate technologies: PostgreSQL, pgvector, FAISS, Chroma. Final choice to be decided by the team before implementation.

---

## 7. Natural Language Database Interaction

```text
Natural Language -> Database Agent -> Query Generation -> SQL Validation
   -> Database -> Result -> Natural Language Response
```

The system must include safeguards against unsafe database operations.

---

## 8. Multi-Agent Orchestration

```text
                    Controller
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
      RAG Agent    Database Agent  Workflow Agent
          |             |             |
          +-------------+-------------+
                        |
                        v
                  Final Response
```

Supports: agent selection, task planning, agent-to-agent communication, sequential/parallel execution, error handling, final response generation.

---

## 9. Persistent Memory

MAKOS retains relevant context between interactions (e.g., a follow-up question about "maternity leave" is understood in the context of a previously discussed leave policy), while avoiding unnecessary retention of irrelevant information.

---

## 10. Workflow Automation

```text
User request -> Controller -> Database Agent -> Retrieve data
   -> Workflow Agent -> Generate report -> Return result
```

Future integrations may include external APIs and enterprise tools.

---

## 11. Suggested Technology Stack

**Backend:** Python, FastAPI
**AI / ML:** LLM API, LangChain/LangGraph (if required), Sentence Transformers / embedding models
**RAG:** PostgreSQL + pgvector, FAISS/Chroma as alternatives
**Database:** PostgreSQL
**Frontend:** React / Next.js
**Development:** Git, GitHub, Docker, VS Code

Avoid adding unnecessary frameworks — every technology should have a clear purpose.

---

## 12. Repository Structure

```text
makos/
│
├── README.md
│
├── backend/
│   ├── main.py
│   ├── config/
│   ├── api/
│   ├── agents/
│   ├── orchestration/
│   ├── rag/
│   ├── database/
│   ├── memory/
│   ├── workflows/
│   └── services/
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── utils/
│
├── data/
│   ├── documents/
│   └── sample/
│
├── tests/
│   ├── agents/
│   ├── rag/
│   ├── database/
│   └── api/
│
├── docs/
│   ├── architecture/
│   └── reports/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── docker-compose.yml
```

---

## 13. GitHub Workflow

All members work on separate branches:

```text
main
 |
 +---- person1
 |
 +---- person2
 |
 +---- person3
 |
 +---- person4
```

Do **not** push experimental code directly to `main`.

```bash
git clone <repository-url>
git checkout -b person1
```

After completing a task:

```bash
git add .
git commit -m "feat: implement controller architecture"
git push origin person1
```

Then open a Pull Request.

---

## 14. Pull Request Rules

Every Pull Request should include:

- **What was implemented?** — brief explanation of the feature
- **What files were changed?** — list the major files
- **How was it tested?**
- **Dependencies** — any new packages
- **Screenshots** — if the change affects the UI

---

## 15. Development Order

### Phase 1 — Foundation
1. Create GitHub repository
2. Create folder structure
3. Configure Python environment
4. Configure PostgreSQL
5. Configure environment variables
6. Define API structure
7. Define agent interfaces

### Phase 2 — Individual Modules
1. Database layer
2. Document ingestion
3. RAG pipeline
4. Agent framework
5. Workflow layer
6. Frontend/API

### Phase 3 — Integration
```text
Frontend -> API -> Controller -> [RAG Agent | Database Agent | Workflow Agent] -> Memory
```

### Phase 4 — Testing
Document retrieval, RAG accuracy, database queries, agent selection, agent communication, workflow execution, error handling, API responses, end-to-end queries.

### Phase 5 — Evaluation
Retrieval accuracy, response quality, query execution time, agent execution time, workflow success rate, scalability, overall system performance.

---

## 16. Example End-to-End Query

```text
User: "Find the leave policy document and tell me how many paid leaves
an employee gets. Also check the employee database and tell me how
many employees are currently eligible."

                    User
                      |
                      v
                 Controller
                      |
             +--------+--------+
             |                 |
             v                 v
         RAG Agent       Database Agent
             |                 |
             v                 v
       Leave Document      Employee DB
             |                 |
             +--------+--------+
                      |
                      v
                Orchestrator
                      |
                      v
                Final Answer
```

This is why MAKOS needs multiple specialized agents rather than a single chatbot.

---

## 17. Definition of Done

A feature is complete only when:

- Code is implemented and pushed to the member's branch
- Unit tests are added where applicable
- The feature works locally
- Documentation is updated
- A Pull Request is created
- Person 1 has reviewed the implementation
- Integration issues are resolved

---

## 18. Final Expected System

Users should be able to: search organizational knowledge, ask questions about documents, query structured databases in natural language, execute AI-assisted workflows, maintain contextual conversations, let specialized agents collaborate, retrieve information via RAG, and perform complex multi-step tasks. The system should be modular enough to add new agents, tools, databases, and external services later.

---

## 19. Project Success Criteria

1. Accurate document retrieval
2. Reliable RAG responses
3. Correct database interaction
4. Successful multi-agent coordination
5. Persistent contextual memory
6. Successful workflow execution
7. Reasonable response latency
8. Modular and maintainable architecture
9. Successful end-to-end execution of complex user queries

---

## 20. Suggested Milestone

Create one GitHub milestone: **`MAKOS Stage I - Core System`**, and place all four issues (see below) under it.

Dependency flow:

```text
Person 1
   |
   +--------------------+
   |                    |
   v                    v
Person 2             Person 3
Database             RAG + Agents
   |                    |
   +----------+---------+
              |
              v
          Person 4
       API + Workflow
              |
              v
       Person 1 Integration
              |
              v
          Final MAKOS
```
