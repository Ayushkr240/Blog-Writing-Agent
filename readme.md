# ✍️ Blog Writing Agent

A multi-agent AI system that researches a topic, gathers supporting evidence, creates a structured blog plan, generates the blog sections, and combines everything into a polished final Markdown blog.

Built using **LangGraph**, **LangChain**, **OpenAI**, **Tavily**, and **Streamlit**.

---

## 🚀 Overview

The **Blog Writing Agent** is a LangGraph-based multi-agent workflow designed to automate the complete blog-writing process.

Instead of asking a single LLM to directly write an entire blog, the system divides the task into specialized stages:

1. Topic analysis
2. Research decision
3. Evidence collection
4. Blog planning
5. Section generation
6. Blog finalization
7. Markdown download

The system can determine whether web research is required, collect supporting sources when necessary, create a structured **5–7 section blog plan**, generate the planned sections sequentially, and finally combine them into a polished Markdown document.

---

## ✨ Features

- 🧠 **Multi-agent LangGraph architecture**
- 🔎 **Automatic topic analysis**
- 🌐 **Conditional web research**
- 📚 **Evidence collection using Tavily**
- 🎯 **Deterministic source-authority scoring**
- 📝 **Structured 5–7 section blog planning**
- ✍️ **Sequential blog section generation**
- 🔄 **Final blog reduction and refinement**
- 📊 **Live workflow stage progress in Streamlit**
- 📋 **Live activity updates**
- 📖 **Final Markdown blog rendering**
- 📥 **Download generated blog as `.md`**
- 🔐 **Environment-variable based API key management**
- 🛡️ **Robust parsing and fallback handling**
- 🧩 **Pydantic-based structured state**
- 🧠 **Context-aware blog generation using research evidence**

---

# 🏗️ Architecture

The system uses a **StateGraph** to coordinate the different stages of the blog-writing process.

```text
                    ┌─────────────────┐
                    │      START      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Router      │
                    │                 │
                    │ Analyze topic   │
                    │ Decide whether  │
                    │ research needed│
                    └────────┬────────┘
                             │
                   ┌─────────┴──────────┐
                   │                    │
              Research needed      No research
                   │                    │
                   ▼                    │
            ┌──────────────┐            │
            │   Research   │            │
            │              │            │
            │ Tavily search│            │
            │ Evidence     │            │
            └──────┬───────┘            │
                   │                    │
                   └─────────┬──────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │                 │
                    │ Create blog     │
                    │ plan            │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Workers     │
                    │                 │
                    │ Generate the    │
                    │ planned blog    │
                    │ sections        │
                    │ sequentially    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Reducer     │
                    │                 │
                    │ Combine and     │
                    │ finalize blog   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │      END        │
                    └─────────────────┘
```

---

# 🔄 Workflow

## 1. Topic Analysis

The router analyzes the user's topic and determines the appropriate workflow mode.

It decides whether external research is required.

Possible outcomes include:

```text
Research required
```

or:

```text
No research required
```

This allows the system to avoid unnecessary web searches for topics that do not require external evidence.

---

## 2. Research

When research is required, the system uses **Tavily** to search the web.

The research stage:

- Generates search queries
- Collects search results
- Extracts useful evidence
- Captures source metadata
- Applies deterministic source-authority scoring
- Selects the strongest evidence for the writing process

The system prioritizes sources based on factors such as:

- Domain authority
- Source reputation
- Publication date
- Availability of useful snippets

---

## 3. Evidence Collection

Collected research is converted into structured evidence.

Each evidence item can contain information such as:

```text
Title
URL
Domain
Snippet
Published date
Authority score
```

This evidence is passed to later stages so the blog can be grounded in the collected information.

---

## 4. Blog Planning

The orchestrator creates a structured blog plan.

The plan contains:

- Blog title
- Blog section tasks
- Section headings
- Section descriptions
- Required coverage

The number of sections is determined dynamically by the generated plan and is typically **5–7 sections**, depending on the topic.

This allows the blog structure to adapt to the complexity of the subject.

---

## 5. Blog Generation

The workers generate the individual blog sections defined by the orchestrator's plan.

The sections are generated **sequentially**, allowing later sections to use relevant context from previously generated sections.

Internally, the backend processes individual section-generation tasks.

However, the Streamlit interface intentionally presents this as a single user-facing stage:

```text
✍️ Generating the blog
```

Individual section progress is not displayed in the frontend.

This keeps the user interface simple and avoids exposing internal worker implementation details.

---

## 6. Blog Finalization

After all planned sections have been generated, the reducer combines them into the final blog.

The reducer is responsible for producing the final Markdown output.

The final result is then displayed directly inside Streamlit.

---

# 📊 Streamlit Interface

The frontend provides stage-level workflow progress:

```text
✅ 🔎 Analyzing the topic
✅ 🌐 Collecting evidence
✅ 🧠 Creating the blog plan
⏳ ✍️ Generating the blog
○  ✨ Finalizing the blog
```

When the workflow finishes:

```text
✅ 🔎 Analyzing the topic
✅ 🌐 Collecting evidence
✅ 🧠 Creating the blog plan
✅ ✍️ Generating the blog
✅ ✨ Finalizing the blog
```

The interface also displays:

- Live activity messages
- Number of evidence sources collected
- Number of planned blog sections
- Final generated blog
- Markdown download button

---

# 📥 Markdown Download

The generated Markdown content is kept **in memory during the workflow**.

The backend does not automatically create a `blog.md` file in the project directory.

Instead, the user can download the generated Markdown only by clicking:

```text
⬇️ Download Markdown File
```

The filename is automatically derived from the blog's Markdown title when possible.

For example:

```text
# How LangGraph Works

...
```

can result in a filename such as:

```text
How LangGraph Works.md
```

Invalid filename characters are removed to keep the generated filename safe.

---

# 🧩 Project Structure

```text
Blog_Writing_Agent/
│
├── backend.py
├── frontend.py
├── requirements.txt
├── .gitignore
├── .env
└── README.md
```

### `backend.py`

Contains the complete LangGraph backend.

Responsible for:

- State definitions
- Pydantic models
- Router
- Research
- Evidence processing
- Source scoring
- Orchestrator
- Workers
- Reducer
- Graph construction
- Streaming workflow execution

### `frontend.py`

Contains the Streamlit interface.

Responsible for:

- Topic input
- Workflow progress
- Live activity
- Final blog rendering
- Markdown download

### `requirements.txt`

Contains the Python dependencies required by the project.

### `.env`

Stores API credentials locally.

This file should **never be committed to GitHub**.

### `.gitignore`

Prevents sensitive files and unnecessary generated files from being committed.

### `README.md`

Project documentation and setup instructions.

---

# ⚙️ Technologies Used

| Technology    | Purpose                         |
| ------------- | ------------------------------- |
| Python        | Core programming language       |
| LangGraph     | Workflow orchestration          |
| LangChain     | LLM and tool integration        |
| OpenAI        | Language model                  |
| Tavily        | Web research                    |
| Pydantic      | Structured data validation      |
| Streamlit     | Frontend interface              |
| python-dotenv | Environment variable management |

---

# 🔐 Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Do not commit your `.env` file.

Make sure `.env` is included in `.gitignore`.

---

# 📦 Installation

## 1. Clone the repository

```bash
git clone https://github.com/Ayushkr240/Blog-Writing-Agent.git
```

Move into the project directory:

```bash
cd Blog_Writing_Agent
```

---

## 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create `.env`:

```env
GOOGLE_API_KEY=your_api_key
TAVILY_API_KEY=your_tavily_api_key
```

---

# ▶️ Running the Application

Start the Streamlit frontend with:

```bash
streamlit run frontend.py
```

Streamlit will provide a local URL where the application can be opened in your browser.

---

# 🧪 Example

Enter a topic such as:

```text
How LangGraph works with parallel agents
```

The workflow may proceed as:

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
🎉 Blog generated successfully!
```

The resulting Markdown blog is displayed in the application and can be downloaded using the download button.

---

# 🧠 Design Philosophy

The project follows a **specialized-agent architecture** rather than relying on one large generation call.

Each stage has a specific responsibility:

```text
Router
  ↓
Decides what workflow is required

Research
  ↓
Collects external evidence when necessary

Orchestrator
  ↓
Creates the blog structure

Workers
  ↓
Generate the planned sections

Reducer
  ↓
Combines and finalizes the blog
```

This separation improves:

- Maintainability
- Debuggability
- Control over generation
- Research grounding
- Workflow transparency
- Extensibility

---

# 🔍 Source Quality

The research pipeline uses deterministic source scoring before evidence reaches the final writing process.

High-authority domains receive stronger scores, including sources such as:

```text
.gov
.edu
github.com
arxiv.org
openai.com
python.org
pytorch.org
tensorflow.org
microsoft.com
```

Reputable publications are also given additional authority:

```text
Reuters
AP News
BBC
The New York Times
TechCrunch
The Verge
Wired
Nature
Ars Technica
```

Domain matching is boundary-aware so that unrelated domains cannot accidentally receive authority simply because their names end with a trusted domain string.

For example:

```text
github.com
docs.github.com
```

are recognized as valid GitHub domains, while:

```text
notgithub.com
github.com.evil.com
```

are not treated as GitHub.

---

# 🛡️ Reliability and Error Handling

The system includes defensive handling for:

- Invalid LLM responses
- Missing structured fields
- Malformed research results
- Unexpected plan formats
- Missing evidence
- Empty final output
- Invalid Markdown filenames
- Workflow exceptions

The frontend also exposes technical errors inside a collapsible Streamlit section when a workflow failure occurs.

---

# 🚧 Future Improvements

Possible future improvements include:

- Parallel section generation
- Improved research deduplication
- Citation insertion inside generated blogs
- Better source ranking
- Persistent blog history
- Blog editing inside the UI
- Multiple output formats
- User-selectable writing styles
- Custom blog length controls
- Additional research providers
- Streaming section-generation feedback
- Deployment to a cloud platform
- Authentication and multi-user support

---

# 👨‍💻 Project Status

The project currently supports the complete workflow:

```text
Topic
  ↓
Routing
  ↓
Conditional Research
  ↓
Evidence Collection
  ↓
Blog Planning
  ↓
Blog Generation
  ↓
Blog Finalization
  ↓
Markdown Download
```

The backend and frontend are separated so that the LangGraph workflow can evolve independently from the Streamlit interface.

---

# 📄 License

Add your preferred license here.

For example:

```text
MIT License
```

---

# ⭐ Acknowledgements

Built using:

- LangGraph
- LangChain
- OpenAI
- Tavily
- Streamlit
- Pydantic

```

```
