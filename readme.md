# ✍️ Blog Writing Agent

A multi-agent AI system that researches a topic, gathers supporting evidence, creates a structured blog plan, generates the blog sections, combines everything into a polished final Markdown blog, and allows the user to export the generated blog in multiple formats.

Built using **LangGraph**, **LangChain**, **Tavily**, **Streamlit**, **Pydantic**, and **LangSmith**.

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
7. Multi-format export
8. Workflow observability with LangSmith

The system can determine whether web research is required, collect supporting sources when necessary, create a structured blog plan, generate the planned sections sequentially, and finally combine them into a polished Markdown document.

The generated blog can then be exported as:

- Markdown
- Plain Text
- HTML
- Word Document
- PDF

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
- 📥 **Multi-format blog export**
- 📄 **Markdown (`.md`) export**
- 📝 **Plain Text (`.txt`) export**
- 🌐 **HTML (`.html`) export**
- 📘 **Word (`.docx`) export**
- 📕 **PDF (`.pdf`) export**
- 💾 **Session-state based generated blog persistence**
- 🔐 **Environment-variable based API key management**
- 🛡️ **Robust parsing and fallback handling**
- 🧩 **Pydantic-based structured state**
- 🧠 **Context-aware blog generation using research evidence**
- 🔍 **LangSmith observability and workflow tracing**

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
                    │ research needed │
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
                    └────────┬────────┘
                             │
                             ▼
                 ┌──────────────────────┐
                 │   Exporter Layer     │
                 │                      │
                 │ MD / TXT / HTML      │
                 │ DOCX / PDF           │
                 └──────────────────────┘
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

The final result is then stored in Streamlit session state and displayed directly inside the application.

Using session state allows the generated blog to remain available across normal Streamlit UI reruns, such as changing the selected export format.

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
- Export format selector
- Download button

The observability information is **not displayed in the Streamlit UI**. LangSmith is used separately for tracing and inspecting workflow execution.

---

# 📥 Blog Export

The generated Markdown blog can be exported into multiple formats.

The export functionality is implemented separately from the Streamlit frontend through:

```text
exporters.py
```

This keeps file-generation logic separated from UI logic.

The available formats are:

| Format     | Extension | Purpose                          |
| ---------- | --------- | -------------------------------- |
| Markdown   | `.md`     | Original Markdown blog           |
| Plain Text | `.txt`    | Simple text version              |
| HTML       | `.html`   | Browser-ready web document       |
| Word       | `.docx`   | Editable Microsoft Word document |
| PDF        | `.pdf`    | Portable document format         |

The user selects the desired format from the Streamlit interface:

```text
Choose export format

[ Markdown (.md) ▼ ]
```

The corresponding exporter is then used to generate the downloadable file.

---

## 📄 Markdown Export

The original Markdown content is exported as:

```text
Blog Title.md
```

---

## 📝 Plain Text Export

Markdown formatting is converted into a clean plain-text representation.

The resulting file uses:

```text
Blog Title.txt
```

---

## 🌐 HTML Export

The Markdown blog is converted into a standalone HTML document.

The generated HTML includes:

- HTML structure
- Metadata
- Responsive viewport configuration
- Basic typography
- Heading styles
- Lists
- Code blocks
- Tables
- Links
- Images

The resulting file can be opened directly in a browser.

Example:

```text
Blog Title.html
```

---

## 📘 Word Export

The blog can be converted into a Microsoft Word document using `python-docx`.

The resulting document uses:

```text
Blog Title.docx
```

This makes the generated blog editable in Word-compatible applications.

---

## 📕 PDF Export

The blog can also be converted into a PDF document using `reportlab`.

The resulting document uses:

```text
Blog Title.pdf
```

---

# 💾 Blog Persistence During UI Interaction

Streamlit reruns the application whenever certain widgets change.

To prevent the generated blog from disappearing when the user changes the export format, the final Markdown content is stored in:

```python
st.session_state.final_md
```

The architecture is therefore:

```text
Generate Blog
      ↓
final_md
      ↓
st.session_state.final_md
      ↓
Streamlit rerun
      ↓
Blog remains available
      ↓
Change export format
      ↓
Generate selected export
```

This allows the user to switch between:

```text
Markdown
TXT
HTML
DOCX
PDF
```

without losing the generated blog.

---

# 🔍 Observability with LangSmith

The project integrates **LangSmith** for workflow observability.

LangSmith provides a separate environment where the execution of the LangGraph workflow can be inspected.

It can be used to understand:

- Workflow execution
- Graph runs
- Individual node execution
- LLM calls
- Tool calls
- Execution traces
- Errors and failures
- Latency
- Token usage
- Intermediate execution behavior

The observability layer is intentionally **not exposed in the Streamlit interface**.

The application UI remains focused on the blog-writing experience while LangSmith provides the developer-facing monitoring and debugging layer.

---

# 🧩 Project Structure

```text
Blog_Writing_Agent/
│
├── backend.py
├── frontend.py
├── exporters.py
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
- Session-state persistence
- Export format selection
- File downloads

### `exporters.py`

Contains the blog export functionality.

Responsible for:

- Markdown export
- Plain-text export
- HTML export
- DOCX export
- PDF export
- Export filename generation

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
| Gemini        | Language model                  |
| Tavily        | Web research                    |
| Pydantic      | Structured data validation      |
| Streamlit     | Frontend interface              |
| LangSmith     | Observability and tracing       |
| Markdown      | Markdown-to-HTML conversion     |
| python-docx   | Word document generation        |
| ReportLab     | PDF generation                  |
| python-dotenv | Environment variable management |

---

# 🔐 Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_api_key
TAVILY_API_KEY=your_tavily_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=your_project_name
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

The export functionality requires:

```text
Markdown
python-docx
reportlab
```

---

## 4. Configure environment variables

Create `.env`:

```env
GOOGLE_API_KEY=your_api_key
TAVILY_API_KEY=your_tavily_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=your_project_name
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

The resulting blog is displayed in the application.

The user can then select an export format:

```text
Markdown
Plain Text
HTML
Word Document
PDF
```

and download the generated blog in the selected format.

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

Exporters
  ↓
Convert the final blog into multiple formats
```

This separation improves:

- Maintainability
- Debuggability
- Control over generation
- Research grounding
- Workflow transparency
- Extensibility
- Reusability of generated content

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
- Export generation errors

The frontend also exposes technical errors inside a collapsible Streamlit section when a workflow failure occurs.

---

# 🚧 Future Improvements

Planned or possible future improvements include:

- Plan approval before blog generation
- Blog editing and revision stage
- Persistent generation history
- Improved research deduplication
- Citation insertion inside generated blogs
- Better source ranking
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
Multi-format Export
  ├── Markdown
  ├── TXT
  ├── HTML
  ├── DOCX
  └── PDF
  ↓
LangSmith Observability
```

The backend, frontend, exporter layer, and observability layer are separated so that each part of the system can evolve independently.

---

# ⭐ Acknowledgements

Built using:

- LangGraph
- LangChain
- Google Gemini
- Tavily
- Streamlit
- Pydantic
- LangSmith
- python-docx
- ReportLab
