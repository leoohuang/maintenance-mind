# MaintenanceMind: Self-Reflective Retrieval for an Industrial Maintenance Agent

**Assignment:** Assignment 2 AI Agents  
**Author:** Tianle Huang  
**Repository:** https://github.com/leoohuang/maintenance-mind  
**Demo video:** https://drive.google.com/file/d/1311PxxFND0SnC4-Oppda534CQTNoIR5A/view?usp=sharing

## 1. Problem And Goal

The assignment asks for an AI agent that is extended in a useful way for
Information Retrieval (IR). MaintenanceMind targets industrial maintenance
investigations. A technician's question often needs context from several
sources: previous failure records, equipment documentation, and external
information. A model-only answer can sound plausible while missing site-specific
evidence. The goal of this prototype is therefore to make evidence retrieval a
first-class part of the agent loop.

The implemented system is a custom ReAct-style agent. It exposes a CLI and a
Streamlit UI and accepts an OpenAI-compatible API endpoint through the OpenAI
Python SDK. The sample domain is pharmaceutical manufacturing equipment such as
tablet presses, mixers, coating pans, blister packaging machines, filling lines,
and autoclaves.

## 2. System Design

MaintenanceMind extends the agent with four context tools. `search_work_orders`
performs semantic search over synthetic historical work orders. `search_manuals`
retrieves chunks from PDF or Markdown manuals. `get_work_order` returns full
metadata for a selected historical record. `web_search` supplies external web
snippets when internal sources are insufficient. Work orders and manuals are
embedded with SentenceTransformers and indexed locally with FAISS.

The project also uses agent architecture ideas discussed in the assignment. A
tool registry exposes OpenAI-compatible function schemas so new IR tools can be
added without changing the core loop. Markdown skill files hold search and
response instructions. A JSON memory file stores durable user or site facts and
recent issues across sessions. These components improve context acquisition
without embedding all knowledge directly in the prompt.

## 3. Creative Extension: Self-Reflective Retrieval

The project-specific extension is a self-reflective evidence evaluation step. A
normal ReAct agent may stop after one plausible search result. In
MaintenanceMind, every retrieval round is followed by a separate structured LLM
call that evaluates whether the evidence is `sufficient`, `partial`, or
`insufficient`. The evaluator also identifies missing information, proposes the
next retrieval tool and query, and records conflicts between sources.

The reflection output is injected into the next agent iteration. This makes the
retrieval process explicit and inspectable in the UI. For example, a work-order
search may find cases about tablet weight variation, while reflection recommends
checking the manual before the agent produces corrective steps. The design is
inspired by reflective retrieval ideas such as Self-RAG, but it is adapted here
to a small multi-source maintenance investigation agent.

## 4. Implementation And Evaluation

The repository includes runnable code, generated demo work orders, fallback
manual content, scripts for rebuilding vector indices, and smoke tests. Local
retrieval checks verify that example queries such as tablet-press weight
variation and blister sealing defects retrieve relevant documents. An end-to-end
agent smoke test verifies function calling, tool use, reflection steps, and
final-answer generation when a valid API key is configured.

The current data is synthetic because real maintenance records are often
restricted. This is a limitation, but it also keeps the prototype reproducible.
The manual ingestion script accepts PDF, Markdown, and text sources, so a more
realistic deployment can replace demo data with controlled site documents and
equipment manuals.

## 5. Reflection On Working With AI Coding Tools

AI coding assistance was useful for moving from an assignment brief to a
structured prototype quickly. It helped scaffold modules, compare the code
against the project manual, and identify practical integration issues such as
API-key validation, Streamlit startup behavior, and deprecated web-search
dependencies. However, generated code was not treated as automatically correct.
I verified the environment, ran retrieval and agent smoke tests, inspected the
UI, and checked which deliverables still needed human work.

The main lesson was that AI assistance is strongest when paired with explicit
architecture and verification. It can accelerate implementation, but the
developer still has to understand the retrieval pipeline, validate tool outputs,
check safety boundaries, and explain the design choices in the final report.

## References

Asai, A. et al. Self-RAG: Learning to Retrieve, Generate, and Critique through
Self-Reflection. 2023.

OpenClaw documentation on memory, tools, skills, and compaction.
