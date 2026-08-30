# 📝 Blog Writing Agent

An AI-powered **Blog Writing Agent** built with **LangGraph, Google Gemini, Tavily, LangChain, and Streamlit**.

The system takes a blog topic from the user and automatically goes through a multi-stage workflow to research the topic, create a structured writing plan, generate individual sections, combine them, and produce a complete Markdown blog that can be downloaded.

---

## 🚀 Features

- 🤖 **AI-powered blog generation**
- 🔎 **Web research using Tavily**
- 🧠 **Google Gemini-powered reasoning and writing**
- 🕸️ **LangGraph workflow orchestration**
- 📚 **Evidence-based writing for researched topics**
- 📝 **Structured 5-section blog generation**
- 📊 **Live workflow progress in Streamlit**
- 📄 **Markdown (`.md`) output**
- ⬇️ **Downloadable final blog**
- 🔐 API keys kept locally using `.env`

---

## 🏗️ Architecture

The Blog Writing Agent follows a multi-stage LangGraph workflow:

```text
                    ┌───────────────┐
                    │     Topic     │
                    │    (User)     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Router     │
                    │               │
                    │ Research?     │
                    └───────┬───────┘
                            │
                   ┌────────┴────────┐
                   │                 │
                Research          No Research
                   │                 │
                   ▼                 │
             ┌───────────┐           │
             │  Tavily   │           │
             │  Search   │           │
             └─────┬─────┘           │
                   │                 │
                   ▼                 │
          ┌─────────────────┐        │
          │ Evidence        │        │
          │ Selection       │        │
          │                 │        │
          │ Max 12 Sources  │        │
          └────────┬────────┘        │
                   │                 │
                   └────────┬────────┘
                            ▼
                    ┌───────────────┐
                    │ Orchestrator  │
                    │               │
                    │ Creates 5     │
                    │ blog sections │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Workers    │
                    │               │
                    │  Section 1    │
                    │  Section 2    │
                    │  Section 3    │
                    │  Section 4    │
                    │  Section 5    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Reducer    │
                    │               │
                    │ Combines all  │
                    │ sections      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Final Markdown│
                    │     Blog      │
                    └───────────────┘
```

---

## 🔄 Workflow

### 1. Router

The router analyzes the user's topic and determines whether web research is required.

It can select between:

- `closed_book` — evergreen topics that don't require current information
- `hybrid` — evergreen topics that benefit from current information
- `open_book` — topics that depend heavily on current events or changing information

If research is required, the router generates targeted search queries.

---

### 2. Research

For research-based topics, the system uses **Tavily** to search the web.

Multiple search queries can produce multiple candidate sources.

The system then:

1. Collects the search results.
2. Removes duplicate URLs.
3. Scores sources based on relevance and authority.
4. Selects the most useful sources.
5. Sends **at most 12 selected sources** to the evidence synthesizer.

This keeps the evidence passed to the LLM focused instead of sending the entire search result set.

---

### 3. Orchestrator

The orchestrator uses Gemini to create a structured blog plan.

The plan contains **exactly 5 sections**.

Each section contains information such as:

- Section title
- Goal
- Key bullets
- Target word count
- Section type
- Research requirements
- Citation requirements
- Code requirements

This gives the writing workers a clear structure to follow.

---

### 4. Workers

The five workers generate the five individual blog sections.

Each worker receives:

- The blog topic
- The overall blog plan
- Its assigned section
- Writing requirements
- Relevant evidence

The workers generate Markdown content for their respective sections.

The workers currently run **sequentially** to reduce API rate-limit problems when using the Gemini API.

---

### 5. Reducer

The reducer takes all five generated sections and puts them back into the correct order.

It then creates the final Markdown document:

```text
# Blog Title

## Section 1

...

## Section 2

...

## Section 3

...

## Section 4

...

## Section 5

...
```

The resulting Markdown file can then be downloaded from the Streamlit interface.

---

## 🛠️ Tech Stack

| Technology        | Purpose                                   |
| ----------------- | ----------------------------------------- |
| **Python**        | Core programming language                 |
| **LangGraph**     | Workflow orchestration                    |
| **LangChain**     | LLM and tool integration                  |
| **Google Gemini** | Planning, research synthesis, and writing |
| **Tavily**        | Web research                              |
| **Streamlit**     | Frontend/UI                               |
| **Pydantic**      | Structured data validation                |
| **python-dotenv** | Environment variable management           |

---

## 📁 Project Structure

```text
Blog_Writing_Agent/
│
├── backend.py
├── frontend.py
├── requirements.txt
├── .gitignore
└── .env
```

### `backend.py`

Contains the complete LangGraph workflow, including:

- Router
- Research
- Evidence selection
- Orchestrator
- Workers
- Reducer
- Markdown generation

### `frontend.py`

Contains the Streamlit interface used to:

- Enter the blog topic
- Start the workflow
- Display workflow progress
- Display the generated blog
- Download the final Markdown file

### `requirements.txt`

Contains the Python dependencies required to run the project.

### `.env`

Stores API credentials locally.

**This file should never be committed to GitHub.**

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ayushkr240/Blog-Writing-Agent.git
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Replace the placeholder values with your actual API keys.

### ⚠️ Security

Never commit your `.env` file.

The project `.gitignore` is configured to exclude it from Git.

---

## ▶️ Running the Application

Start the Streamlit application:

```bash
streamlit run frontend.py
```

Streamlit will provide a local URL, usually similar to:

```text
http://localhost:8501
```

Open it in your browser.

---

## 💡 Example

Enter a topic such as:

```text
How does LangGraph work?
```

The agent will move through the workflow:

```text
Topic
  ↓
Routing
  ↓
Research (if required)
  ↓
Evidence Collection
  ↓
Blog Planning
  ↓
Writing Section 1
  ↓
Writing Section 2
  ↓
Writing Section 3
  ↓
Writing Section 4
  ↓
Writing Section 5
  ↓
Finalizing Blog
  ↓
Download Markdown
```

The final result is a complete `.md` blog file.

---

## 🧠 Why LangGraph?

LangGraph is used to represent the blog-generation process as a structured workflow rather than making one large LLM call.

This makes it possible to separate responsibilities:

```text
Router        → Decides what needs to happen
Research      → Collects evidence
Orchestrator  → Plans the blog
Workers       → Write sections
Reducer       → Produces the final document
```

This modular architecture makes the system easier to understand, debug, and extend.

---

## 🔮 Future Improvements

Possible future improvements include:

- [ ] Support for multiple blog styles
- [ ] User-controlled blog length
- [ ] Custom audience selection
- [ ] SEO keyword generation
- [ ] Automatic meta descriptions
- [ ] Automatic title generation
- [ ] Image generation for blog posts
- [ ] More advanced source-quality evaluation
- [ ] Citation verification
- [ ] Blog history
- [ ] Export to PDF/DOCX
- [ ] Streaming individual worker outputs
- [ ] Persistent LangGraph state
- [ ] Deployment to Streamlit Cloud

---

## ⚠️ Notes

This project requires valid **Google Gemini** and **Tavily** API credentials for its full research and generation workflow.

Research results depend on the quality and availability of external sources returned by Tavily.

The system limits the evidence passed to the synthesis stage to **12 sources** to keep the research context focused and reduce unnecessary token usage.

---

## 👨‍💻 Author

**Ayush Kumar**

Built as an AI-agent project exploring:

- LangGraph
- LangChain
- LLM workflows
- Agentic systems
- Web research
- AI-assisted content generation

---

## ⭐ If you find this project useful

Consider giving the repository a ⭐ on GitHub!
