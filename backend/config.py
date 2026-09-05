from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "gemini-3.1-flash-lite"

# Only this many useful sources are sent to the evidence
# synthesizer and later writing stages.
MAX_EVIDENCE_SOURCES = 8

# Research breadth. We can collect more than 8 raw results,
# rank them locally, and only send the best 8 to Gemini.
MAX_RESEARCH_QUERIES = 10
TAVILY_RESULTS_PER_QUERY = 4

# Keep snippets compact so prompts do not become unnecessarily
# large.
MAX_SNIPPET_CHARS = 900

# The worker graph uses LangGraph fan-out so the independent
# section-generation calls can run concurrently. The planner
# is capped at 5–7 sections, which stays below the user's
# stated 15 RPM Gemini request limit for one generation batch.
MIN_SECTIONS = 5
MAX_SECTIONS = 7