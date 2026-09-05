from typing import List
import re

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Send

from .config import MAX_EVIDENCE_SOURCES
from .schemas import (
    ChatState,
    WorkerState,
    Plan,
    Task,
    EvidenceItem,
)
from .llm import llm, _extract_response_text


# ============================================================
# 1. WORKER PROMPT
# ============================================================

WORKER_SYSTEM = """
You are a specialist writer in a parallel multi-agent blog writing system.

You are responsible for EXACTLY ONE section of a larger blog.

Other workers are independently writing the other sections concurrently.
You must therefore respect strict section ownership.

==================================================
1. YOUR RESPONSIBILITY
==================================================

Write ONLY your assigned section.

Your assigned section is defined by:
- Its title
- Its goal
- Its bullets
- Its brief
- Its section type
- Its must_not_cover boundaries

Treat these instructions as the boundaries of your work.

Do NOT write the entire blog.

Do NOT write another worker's section.

Do NOT expand your section into topics that belong to another section.


==================================================
2. SECTION OWNERSHIP — CRITICAL
==================================================

Each section has an exclusive information responsibility.

You MUST:

- Cover the important points listed in your section's bullets.
- Stay focused on the goal of your section.
- Respect the topics listed in must_not_cover.
- Assume that another worker owns every other section.
- Avoid developing another section's main ideas.
- Avoid repeating facts, statistics, definitions, examples, historical
  events, explanations, or arguments that belong primarily to another
  section.

If another section's topic is necessary for context:

- Mention it briefly only when necessary.
- Do not explain it in detail.
- Do not turn that brief reference into a second section.

The purpose of your section is to ADD new information to the article,
not repeat information that another worker is already responsible for.


==================================================
3. MUST_NOT_COVER — CRITICAL
==================================================

The section plan may provide a list called must_not_cover.

These are topics or information areas owned by other sections.

You MUST NOT develop these topics.

For example, if your section is:

"Membership and Structure"

and must_not_cover contains:

- Origins of the G20
- Asian financial crisis
- Historical evolution
- Recent summit outcomes

then you may briefly mention the origins if needed for context, but you
must NOT explain the Asian financial crisis or the history of the G20.

Treat must_not_cover as a hard boundary.


==================================================
4. OTHER SECTION OWNERSHIP
==================================================

You may be shown the complete section map.

Use it to understand what other workers are responsible for.

If another section owns a topic, do not develop that topic in your section.

Do NOT attempt to make your section self-contained by explaining every
important aspect of the overall topic.

The complete blog will be assembled later by a reducer.

Your job is only to produce your assigned contribution.


==================================================
5. AUDIENCE
==================================================

Assume a general audience unless the topic clearly requires a different
level of expertise.

Write for the audience naturally implied by the topic.

Match terminology and depth to the subject.

For technical topics:
- Technical terminology is appropriate when relevant.
- Explain specialized concepts clearly when the reader needs the context.

For non-technical topics:
- Use natural, accessible language.
- Do not introduce programming, software engineering, developer terminology,
  or technical metaphors unless directly relevant to the subject.


==================================================
6. WRITING STYLE
==================================================

Write naturally, clearly, and professionally.

Prioritize:

- Accuracy
- Clarity
- Relevance
- Reader usefulness
- Logical explanation
- Appropriate depth
- Natural transitions
- Concrete examples when genuinely useful

Avoid:

- Unnecessary jargon
- Forced technical language
- Forced programming analogies
- Developer-centric metaphors
- Generic filler
- Repetitive explanations
- Rephrasing the same point multiple times
- Artificially sophisticated language
- Unsupported authoritative-sounding claims


==================================================
7. INTRODUCTION SECTIONS
==================================================

If your assigned section is the introduction:

- Briefly establish what the topic is.
- Explain why the topic matters.
- Give the reader enough context to understand the rest of the article.
- Do NOT explain the detailed content owned by later sections.
- Do NOT provide a detailed history, feature list, process explanation,
  examples, or current developments unless those are explicitly owned
  by the introduction.

The introduction should orient the reader, not write the entire article.


==================================================
8. CONCLUSION SECTIONS
==================================================

If your assigned section is the conclusion:

- Synthesize the major ideas of the article.
- Give the reader a useful final takeaway.
- Connect the major ideas at a high level.
- Do NOT repeat every section in detail.
- Do NOT introduce substantial new information.
- Do NOT simply copy or rephrase the article's earlier paragraphs.

The conclusion should provide synthesis rather than repetition.


==================================================
9. RESEARCH AND ACCURACY
==================================================

Use the provided evidence when it is relevant to your assigned section.

You do NOT need to use every provided source.

Only use evidence that supports the content you are writing.

Rules:

- Do not invent statistics.
- Do not invent dates.
- Do not invent studies.
- Do not invent quotations.
- Do not invent technical claims.
- Do not exaggerate conclusions from the evidence.
- Do not present unsupported claims as established facts.
- Prefer accurate and appropriately qualified statements.
- Do not repeat a factual claim merely because it appears in multiple
  sources.

If the available evidence does not adequately support a specific factual
claim, avoid presenting that claim as established fact.


==================================================
10. CITATIONS
==================================================

When citations are required by the section plan:

- Cite claims using only the provided evidence.
- Use the source URL exactly as provided by the application.
- Do not invent URLs.
- Do not cite a source that does not support the claim.
- Do not add a separate Sources section.
- Do not create a bibliography.

The reducer/application will handle final blog assembly.


==================================================
11. CODE
==================================================

Code is OPTIONAL.

Only include code when:

1. The section plan explicitly indicates that code is required, AND
2. Code is genuinely relevant and useful to the reader.

Never include code merely because this system can generate code.

For non-technical topics:

- Do NOT introduce programming examples.
- Do NOT introduce software concepts.
- Do NOT introduce debugging terminology.
- Do NOT introduce developer metaphors.

For technical topics:

- Include code only when it materially improves the explanation.


==================================================
12. SECTION LENGTH AND DEPTH
==================================================

Respect the target word count provided by the section plan.

Do not artificially inflate the section.

Do not add filler to reach the target.

Prioritize useful information over length.

If the section can be explained clearly in fewer words, prefer concise,
information-dense writing over repetition.


==================================================
13. HEADING RULE
==================================================

Return ONLY the body content of the assigned section.

Do NOT create the section heading yourself.

Do NOT add:

- A "# Title"
- A "## Section Title"
- "Sources"
- "References"
- A conclusion unless the assigned section is the conclusion
- An introduction unless the assigned section is the introduction
- Any content belonging to another section


==================================================
14. FINAL SELF-CHECK
==================================================

Before returning the section, check:

1. Am I writing ONLY my assigned section?
2. Did I cover the important bullets?
3. Did I follow the section goal and brief?
4. Did I avoid everything listed in must_not_cover?
5. Did I avoid developing another section's main ideas?
6. Did I avoid repeating major facts unnecessarily?
7. Did I use evidence only where relevant?
8. Did I avoid unsupported claims?
9. Did I avoid unnecessary filler?
10. Did I avoid adding my own heading?
11. Did I follow the requested word count?
12. Does this section add NEW information to the overall article?

If any answer is "no", revise the section before returning it.

Return ONLY the section content in the format required by the application.
"""


# ============================================================
# 2. WORKER PAYLOAD
# ============================================================

def _build_worker_payload(
    plan: Plan,
    task: Task,
    topic: str,
    mode: str,
    evidence: List[EvidenceItem],
) -> dict:
    """
    Convert the worker inputs into a serializable payload.

    Only the selected evidence sources are passed forward.
    """

    return {
        "plan": plan.model_dump(),

        "topic": topic,

        "task": task.model_dump(),

        "mode": mode,

        "evidence": [
            item.model_dump()
            for item in evidence[
                :MAX_EVIDENCE_SOURCES
            ]
        ],
    }


# ============================================================
# 3. WORKER OUTPUT CLEANING
# ============================================================

def _clean_worker_section(
    section_md: str,
    task: Task,
) -> str:
    """
    Clean and normalize a worker-generated section.

    Workers are instructed to return only section body content,
    but this function protects the final blog from accidental:

    - Markdown section headings
    - Duplicate section headings
    - Streamlit [svg](...) anchor artifacts
    - Sources / References blocks
    - Excessive blank lines
    """

    if not section_md:
        return ""

    text = section_md.strip()

    # --------------------------------------------------------
    # 1. Remove Streamlit/browser anchor artifacts
    # --------------------------------------------------------

    # Example unwanted output:
    #
    # [svg](http://localhost:8501/#some-heading)

    text = re.sub(
        r"\[svg\]\([^)]*\)",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # 2. Remove accidental heading matching this section title
    # --------------------------------------------------------

    expected_title = re.sub(
        r"[^a-z0-9]+",
        " ",
        task.title.lower(),
    ).strip()

    lines = text.splitlines()

    while lines:

        first_line = lines[0].strip()

        heading_match = re.match(
            r"^#{1,6}\s+(.+?)\s*$",
            first_line,
        )

        if not heading_match:
            break

        actual_heading = re.sub(
            r"[^a-z0-9]+",
            " ",
            heading_match.group(1).lower(),
        ).strip()

        if actual_heading == expected_title:

            lines.pop(0)

            continue

        break

    text = "\n".join(
        lines
    ).strip()

    # --------------------------------------------------------
    # 3. Remove accidental Sources / References section
    # --------------------------------------------------------

    # Workers are not supposed to create their own Sources section.
    #
    # Remove everything starting from a standalone:
    #
    # ## Sources
    # ### Sources
    # Sources:
    # ## References
    # ### References

    text = re.sub(
        r"\n#{1,6}\s*(?:Sources|References)\s*:?\s*\n.*$",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"\n(?:Sources|References)\s*:?\s*\n.*$",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # --------------------------------------------------------
    # 4. Remove trailing standalone Sources / References
    # --------------------------------------------------------

    text = re.sub(
        r"(?:^|\n)\s*#{1,6}\s*(?:Sources|References)\s*:?\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # --------------------------------------------------------
    # 5. Remove excessive blank lines
    # --------------------------------------------------------

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    ).strip()

    return text


# ============================================================
# 4. WORKER GENERATION
# ============================================================

def _generate_worker_section(
    payload: dict,
) -> tuple[int, str]:
    """
    Generate exactly one blog section from a worker payload.
    """

    task = Task(
        **payload["task"]
    )

    plan = Plan(
        **payload["plan"]
    )

    evidence = [
        EvidenceItem(**item)
        for item in payload.get(
            "evidence",
            [],
        )[
            :MAX_EVIDENCE_SOURCES
        ]
    ]

    topic = payload["topic"]

    mode = payload.get(
        "mode",
        "closed_book",
    )

    # --------------------------------------------------------
    # Build exclusive bullets
    # --------------------------------------------------------

    bullets_text = "\n".join(
        f"- {bullet}"
        for bullet in task.bullets
    )

    # --------------------------------------------------------
    # Build must_not_cover boundaries
    # --------------------------------------------------------

    must_not_cover_text = "\n".join(
        f"- {item}"
        for item in task.must_not_cover
    )

    if not must_not_cover_text:

        must_not_cover_text = (
            "- None explicitly assigned."
        )

    # --------------------------------------------------------
    # Build evidence text
    # --------------------------------------------------------

    evidence_lines = []

    for item in evidence:

        evidence_lines.append(
            (
                f"- Title: {item.title}\n"
                f"  URL: {item.url}\n"
                f"  Date: "
                f"{item.published_at or 'unknown'}\n"
                f"  Snippet: "
                f"{item.snippet or ''}"
            )
        )

    evidence_text = "\n".join(
        evidence_lines
    )

    # --------------------------------------------------------
    # Invoke Gemini
    # --------------------------------------------------------

    response = llm.invoke(
        [
            SystemMessage(
                content=WORKER_SYSTEM
            ),
            HumanMessage(
                content=(
                    f"Blog title:\n"
                    f"{plan.blog_title}\n\n"

                    f"Audience:\n"
                    f"{plan.audience}\n\n"

                    f"Tone:\n"
                    f"{plan.tone}\n\n"

                    f"Blog kind:\n"
                    f"{plan.blog_kind}\n\n"

                    f"Constraints:\n"
                    f"{plan.constraints}\n\n"

                    f"Topic:\n"
                    f"{topic}\n\n"

                    f"Mode:\n"
                    f"{mode}\n\n"

                    f"Section title:\n"
                    f"{task.title}\n\n"

                    f"Section type:\n"
                    f"{task.section_type}\n\n"

                    f"Goal:\n"
                    f"{task.goal}\n\n"

                    f"Brief:\n"
                    f"{task.brief}\n\n"

                    f"Target words:\n"
                    f"{task.target_words}\n\n"

                    f"Tags:\n"
                    f"{task.tags}\n\n"

                    f"requires_research:\n"
                    f"{task.requires_research}\n\n"

                    f"requires_citations:\n"
                    f"{task.requires_citations}\n\n"

                    f"requires_code:\n"
                    f"{task.requires_code}\n\n"

                    f"YOUR SECTION'S EXCLUSIVE BULLETS:\n"
                    f"{bullets_text}\n\n"

                    f"Must NOT cover:\n"
                    f"{must_not_cover_text or '- None specified'}\n\n"

                    "Evidence "
                    "(ONLY use these URLs when citing):\n"
                    f"{evidence_text}"
                )
            ),
        ]
    )

    # --------------------------------------------------------
    # Extract plain text from Gemini response
    # --------------------------------------------------------

    section_md = _extract_response_text(
        response
    )

    if not section_md:

        raise ValueError(
            f"Worker {task.id} received an empty "
            "response from Gemini."
        )

    # --------------------------------------------------------
    # Clean worker output
    # --------------------------------------------------------

    section_md = _clean_worker_section(
        section_md,
        task,
    )

    return (
        task.id,
        section_md,
    )


# ============================================================
# 5. WORKER NODE
# ============================================================

def worker_node(
    state: WorkerState,
) -> dict:
    """
    Generate exactly one blog section.

    LangGraph invokes this node once for every Task emitted by
    the fan-out function. The invocations can run concurrently.
    """

    payload = _build_worker_payload(
        plan=state["plan"],

        task=state["task"],

        topic=state["topic"],

        mode=state.get(
            "mode",
            "closed_book",
        ),

        evidence=state.get(
            "evidence",
            [],
        ),
    )

    task_id, section_md = _generate_worker_section(
        payload
    )

    return {
        "sections": [
            (
                task_id,
                section_md,
            )
        ]
    }


# ============================================================
# 6. PARALLEL WORKERS
#    LANGGRAPH FAN-OUT / FAN-IN
# ============================================================

def fan_out_workers(
    state: ChatState,
) -> List[Send]:
    """
    Create one LangGraph Send object for every planned section.

    Each worker receives exactly one Task.
    """

    plan = state.get(
        "plan"
    )

    if plan is None:

        raise ValueError(
            "Cannot fan out workers because plan is None."
        )

    # Only pass the selected evidence sources.
    evidence = state.get(
        "evidence",
        [],
    )[
        :MAX_EVIDENCE_SOURCES
    ]

    topic = state.get(
        "topic",
        "",
    )

    mode = state.get(
        "mode",
        "closed_book",
    )

    sends = []

    for task in plan.tasks:

        sends.append(
            Send(
                "worker",
                {
                    "plan": plan,

                    "task": task,

                    "topic": topic,

                    "mode": mode,

                    "evidence": evidence,
                },
            )
        )

    return sends