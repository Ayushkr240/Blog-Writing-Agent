# ✍️ Blog Writing Agent

An AI-powered multi-agent blog writing system that can **analyze a topic, perform web research when needed, create a structured writing plan, generate blog sections in parallel, and assemble the final blog into multiple export formats.**

Built with **LangGraph, LangChain, Google Gemini, Tavily, Streamlit, Pydantic, and LangSmith**.

---

## 🚀 Features

- 🧠 **Multi-agent LangGraph architecture**
- 🔎 **Automatic research routing**
- 🌐 **Conditional web research with Tavily**
- 📚 **Evidence-based content generation**
- 🎯 **Deterministic source-authority scoring**
- 📝 **Dynamic 5–7 section blog planning**
- ⚡ **Parallel section generation using LangGraph fan-out**
- 🔒 **Exclusive section ownership with `must_not_cover` boundaries**
- 🛡️ **Worker-result validation**
- 🔄 **Automatic section ordering and blog reduction**
- 📊 **Live workflow progress in Streamlit**
- 💾 **Session-state blog persistence**
- 📥 **Multi-format export**
- 🔍 **LangSmith workflow observability**

### Export Formats

| Format     | Extension |
| ---------- | --------- |
| Markdown   | `.md`     |
| Plain Text | `.txt`    |
| HTML       | `.html`   |
| Word       | `.docx`   |
| PDF        | `.pdf`    |

---

# 🏗️ Architecture

The application uses a **LangGraph StateGraph** to coordinate specialized stages.

```text
┌─────────────┐
│    START    │
└──────┬──────┘
       ↓
┌─────────────┐
│   Router    │
│             │
│ Analyze     │
│ topic       │
└──────┬──────┘
       │
   ┌───┴───────────────┐
   ↓                   ↓
┌──────────────┐    No Research
│   Research   │         │
│              │         │
│ Tavily       │         │
│ Search       │         │
└──────┬───────┘         │
       └──────────┬──────┘
                  ↓
          ┌──────────────┐
          │ Orchestrator │
          │              │
          │ Create Plan  │
          └──────┬───────┘
                 ↓
       ┌─────────────────────┐
       │   Parallel Workers  │
       │                     │
       │ Section 1 ──┐       │
       │ Section 2 ──┤       │
       │ Section 3 ──┤       │
       │ Section 4 ──┤       │
       │ Section 5 ──┤       │
       │ Section 6 ──┤       │
       │ Section 7 ──┘       │
       └──────────┬──────────┘
                  ↓
          ┌─────────────┐
          │   Reducer   │
          │             │
          │ Validate &  │
          │ combine     │
          └──────┬──────┘
                 ↓
                END
                 ↓
        ┌─────────────────┐
        │    Exporters    │
        │ MD/TXT/HTML     │
        │ DOCX/PDF        │
        └─────────────────┘
```

---

# 🔄 How It Works

## 1. 🔎 Routing

The router analyzes the user's topic and determines whether external research is required.

It can choose between:

- `closed_book` — no web research required
- `hybrid` — research combined with model knowledge
- `open_book` — research-driven generation

This prevents unnecessary web searches for evergreen topics.

---

## 2. 🌐 Research

When research is required, Tavily searches the web using generated queries.

The research pipeline:

1. Collects search results
2. Deduplicates sources
3. Scores source authority
4. Considers relevance and available metadata
5. Selects the strongest evidence
6. Passes only the selected evidence to later stages

The system limits the evidence passed to the generation pipeline to **8 sources**.

---

## 3. 🧠 Planning

The orchestrator creates a structured blog plan containing:

- Blog title
- Audience
- Tone
- Blog type
- Section tasks
- Section goals
- Section bullets
- Target word counts
- Research requirements
- Citation requirements
- Code requirements
- Section ownership boundaries

The plan dynamically contains **5–7 sections** depending on the topic.

---

## 4. ⚡ Parallel Blog Generation

Each planned section is assigned to an independent worker.

LangGraph uses **fan-out/fan-in** execution to generate the sections concurrently.

Each worker receives:

- Its assigned section
- Section goal
- Section bullets
- Section brief
- Target word count
- Relevant evidence
- `must_not_cover` boundaries

### Exclusive Section Ownership

Workers are explicitly instructed to avoid content owned by other sections.

For example:

```text
Section A
    ↓
Owns: History

Section B
    ↓
Owns: Current Applications

    must_not_cover:
    - History
    - Future Developments

Section C
    ↓
Owns: Future Developments
```

This reduces repetition and prevents multiple workers from writing the same ideas.

---

## 5. 🔄 Reduction

After the workers finish, the reducer:

- Validates worker task IDs
- Detects missing worker results
- Detects duplicate worker results
- Rejects unknown task IDs
- Rejects empty worker content
- Sorts sections according to their planned order
- Adds section headings
- Combines everything into the final Markdown blog

The final blog is then stored in Streamlit session state.

---

# 📊 Streamlit Interface

The Streamlit frontend provides a simple user-facing workflow:

```text
🔎 Analyzing the topic
        ↓
🌐 Collecting evidence
        ↓
🧠 Creating the blog plan
        ↓
✍️ Generating the blog
        ↓
✨ Finalizing the blog
        ↓
🎉 Blog generated successfully
```

The interface displays:

- Workflow progress
- Activity updates
- Evidence count
- Planned section count
- Generated blog
- Export format selector
- Download button

Internal worker execution remains hidden from the user to keep the interface simple.

---

# 📥 Export System

The exporter layer is separated from the Streamlit UI.

The generated Markdown blog can be converted into:

- Markdown
- Plain Text
- HTML
- DOCX
- PDF

This separation keeps the application architecture modular and makes it easier to add additional export formats later.

---

# 🔍 LangSmith Observability

The project integrates **LangSmith** for developer-facing observability.

It can be used to inspect:

- LangGraph executions
- Node execution
- LLM calls
- Tool calls
- Errors
- Latency
- Token usage
- Workflow traces

LangSmith is intentionally kept separate from the Streamlit interface.

---

# 📁 Project Structure

```text
Blog_Writing_Agent/
│
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── schemas.py
│   ├── llm.py
│   ├── research.py
│   ├── planner.py
│   ├── workers.py
│   ├── reducer.py
│   └── graph.py
│
├── frontend.py
├── exporters.py
├── requirements.txt
├── .gitignore
├── .env
└── README.md
```

### `backend/`

The backend is organized into focused modules instead of a single large file.

#### `config.py`

Contains:

- Environment configuration
- Model configuration
- Research limits
- Evidence limits
- Section limits

#### `schemas.py`

Contains:

- Pydantic schemas
- Router decision schema
- Evidence schemas
- Blog plan schema
- Task schema
- LangGraph state definitions

#### `llm.py`

Handles:

- Google Gemini initialization
- LLM response text extraction
- Structured LLM invocation

#### `research.py`

Handles:

- Research routing
- Tavily search
- Search-result processing
- Source deduplication
- Source-authority scoring
- Evidence selection
- Evidence synthesis

#### `planner.py`

Handles:

- Blog planning
- Section ownership
- Plan validation
- Orchestrator node

#### `workers.py`

Handles:

- Worker prompts
- Worker payload construction
- Section generation
- Worker output cleanup
- Parallel worker fan-out

#### `reducer.py`

Handles:

- Worker-result validation
- Section ordering
- Final Markdown assembly

#### `graph.py`

Handles:

- LangGraph StateGraph construction
- Node connections
- Conditional routing
- Application compilation
- Backend runners

#### `__init__.py`

Provides the public backend interface:

```python
from backend import run, run_stream, generate_blog
```

---

### `frontend.py`

Contains the Streamlit application:

- Topic input
- Workflow progress
- Activity updates
- Blog rendering
- Session-state persistence
- Export selection
- Downloads

---

### `exporters.py`

Handles:

- Markdown
- TXT
- HTML
- DOCX
- PDF generation

---

# 🛠️ Tech Stack

| Technology        | Purpose                                       |
| ----------------- | --------------------------------------------- |
| **Python**        | Core programming language                     |
| **LangGraph**     | Workflow orchestration and parallel execution |
| **LangChain**     | LLM and tool integration                      |
| **Google Gemini** | Blog planning and generation                  |
| **Tavily**        | Web research                                  |
| **Pydantic**      | Structured output validation                  |
| **Streamlit**     | User interface                                |
| **LangSmith**     | Observability and tracing                     |
| **python-docx**   | Word document generation                      |
| **ReportLab**     | PDF generation                                |
| **python-dotenv** | Environment configuration                     |

---

# ⚙️ Setup

## 1. Clone the repository

```bash
git clone https://github.com/Ayushkr240/Blog-Writing-Agent.git

cd Blog-Writing-Agent
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv

source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_api_key

TAVILY_API_KEY=your_tavily_api_key

LANGSMITH_API_KEY=your_langsmith_api_key

LANGSMITH_TRACING=true

LANGSMITH_PROJECT=your_project_name
```

**Never commit your `.env` file to GitHub.**

Make sure it is included in `.gitignore`.

---

# ▶️ Run the Application

Start the Streamlit application:

```bash
streamlit run frontend.py
```

Then open the local URL provided by Streamlit.

---

# 🧪 Example

Enter a topic such as:

```text
How LangGraph works with parallel agents
```

The system processes it through:

```text
Topic
  ↓
Router
  ↓
Research (if required)
  ↓
Evidence Selection
  ↓
Blog Planning
  ↓
Parallel Section Generation
  ↓
Worker Validation
  ↓
Blog Reduction
  ↓
Final Markdown
  ↓
Export
```

---

# 🧠 Design Philosophy

The project follows a **specialized multi-agent architecture** instead of relying on one large LLM call.

Each component has a focused responsibility:

```text
Router
    ↓
Decides whether research is required

Research
    ↓
Collects and ranks external evidence

Orchestrator
    ↓
Creates the blog structure and section ownership

Workers
    ↓
Generate independent sections in parallel

Reducer
    ↓
Validates and assembles the final blog

Exporters
    ↓
Convert the blog into multiple formats
```

This separation improves:

- Maintainability
- Reliability
- Debugging
- Scalability
- Content consistency
- Control over generation

---

# 🚧 Future Improvements

Possible future improvements include:

- Plan approval before generation
- Blog editing and revision agents
- Persistent generation history
- Improved citation insertion
- Better semantic source ranking
- User-selectable writing styles
- Custom blog length controls
- Additional research providers
- Cloud deployment
- Authentication and multi-user support

---

# ⭐ Project Status

The project currently supports the complete AI-assisted blog-writing workflow:

```text
Routing
   ↓
Conditional Research
   ↓
Evidence Selection
   ↓
Dynamic Blog Planning
   ↓
Parallel Section Generation
   ↓
Worker Validation
   ↓
Blog Reduction
   ↓
Multi-format Export
   ↓
LangSmith Observability
```

The **backend, frontend, exporter, and observability layers are separated** so they can evolve independently.

The backend has also been modularized into focused components and verified with an automated test suite.

---

# 👨‍💻 Author

**Ayush Kumar**

Built as a practical exploration of **agent systems, LangGraph workflows, research-grounded generation, and AI application development.**
