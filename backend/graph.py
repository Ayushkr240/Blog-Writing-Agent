from langgraph.graph import StateGraph, START, END

from .schemas import ChatState

from .research import (
    router_node,
    route_next,
    research_node,
)

from .planner import (
    orchestrator_node,
)

from .workers import (
    worker_node,
    fan_out_workers,
)

from .reducer import (
    reducer_node,
)


# ============================================================
# 1. INITIAL STATE
# ============================================================

def _initial_state(
    topic: str,
) -> ChatState:
    """
    Create the initial state for a new blog-generation run.
    """

    return {
        "topic": topic,

        "mode": "",

        "needs_research": False,

        "queries": [],

        "evidence": [],

        "plan": None,

        "sections": [],

        "final_md": "",
    }


# ============================================================
# 2. BUILD LANGGRAPH
# ============================================================

g = StateGraph(
    ChatState
)


# ============================================================
# NODES
# ============================================================

g.add_node(
    "router",
    router_node,
)

g.add_node(
    "research",
    research_node,
)

g.add_node(
    "orchestrator",
    orchestrator_node,
)

# One reusable worker node is dynamically fanned out by
# fan_out_workers().
#
# LangGraph creates one worker branch for each planned
# section, allowing independent sections to run concurrently.

g.add_node(
    "worker",
    worker_node,
)

g.add_node(
    "reducer",
    reducer_node,
)


# ============================================================
# EDGES
# ============================================================

# ------------------------------------------------------------
# START → ROUTER
# ------------------------------------------------------------

g.add_edge(
    START,
    "router",
)


# ------------------------------------------------------------
# ROUTER → RESEARCH / ORCHESTRATOR
# ------------------------------------------------------------

g.add_conditional_edges(
    "router",
    route_next,
    {
        "research": "research",
        "orchestrator": "orchestrator",
    },
)


# ------------------------------------------------------------
# RESEARCH → ORCHESTRATOR
# ------------------------------------------------------------

g.add_edge(
    "research",
    "orchestrator",
)


# ------------------------------------------------------------
# ORCHESTRATOR → PARALLEL WORKERS
# ------------------------------------------------------------

g.add_conditional_edges(
    "orchestrator",
    fan_out_workers,
)


# ------------------------------------------------------------
# WORKER → REDUCER
# ------------------------------------------------------------

g.add_edge(
    "worker",
    "reducer",
)


# ------------------------------------------------------------
# REDUCER → END
# ------------------------------------------------------------

g.add_edge(
    "reducer",
    END,
)


# ============================================================
# 3. COMPILE GRAPH
# ============================================================

app = g.compile()


# ============================================================
# 4. NORMAL RUNNER
# ============================================================

def run(
    topic: str,
):
    """
    Run the complete blog-generation workflow.

    This executes the compiled LangGraph application and
    returns the final state.
    """

    topic = str(
        topic
    ).strip()

    if not topic:

        raise ValueError(
            "Topic cannot be empty."
        )

    return app.invoke(
        _initial_state(
            topic
        )
    )


# ============================================================
# 5. STREAMING RUNNER
# ============================================================

def run_stream(
    topic: str,
):
    """
    Stream updates from the LangGraph workflow.

    The frontend uses these updates to display workflow
    progress while the blog is being generated.
    """

    topic = str(
        topic
    ).strip()

    if not topic:

        raise ValueError(
            "Topic cannot be empty."
        )

    initial_state = _initial_state(
        topic
    )

    for event in app.stream(
        initial_state,
        stream_mode="updates",
    ):

        yield event


# ============================================================
# 6. CONVENIENCE FUNCTION
# ============================================================

def generate_blog(
    topic: str,
) -> str:
    """
    Generate a complete blog and return only the final
    Markdown content.
    """

    result = run(
        topic
    )

    return result[
        "final_md"
    ]