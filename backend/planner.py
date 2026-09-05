from langchain_core.messages import SystemMessage, HumanMessage

from .config import (
    MIN_SECTIONS,
    MAX_SECTIONS,
    MAX_EVIDENCE_SOURCES,
)
from .schemas import (
    ChatState,
    Plan,
)
from .llm import _invoke_structured


# ============================================================
# 1. ORCHESTRATOR PROMPT
# ============================================================

ORCH_MESSAGE = """
You are the senior content strategist and blog planner for a general-purpose
AI blog writing system.

Your job is to create a strong, logical, reader-focused plan for the user's
requested topic.

The blog can be about ANY subject.

IMPORTANT AUDIENCE RULE:
- Assume the reader is a general audience.
- Determine the appropriate level of explanation from the topic itself.
- Use technical terminology only when it is relevant to the topic.
- If the topic is technical, technical terminology is appropriate.
- If the topic is non-technical, use language appropriate for a general reader.
- Never inject programming, software engineering, developer terminology, or
  technical analogies unless they are genuinely relevant to the topic.


============================================================
SECTION STRUCTURE
============================================================

Create between 5 and 7 meaningful sections.

The exact structure must be determined by the topic.

Do NOT use a fixed template for every blog.

Choose sections that naturally explain the specific topic and provide a
logical progression for the reader.


============================================================
SECTION OWNERSHIP — CRITICAL
============================================================

The blog will be written by multiple independent workers running concurrently.

Each worker will receive exactly ONE section.

Therefore, sections MUST have strict and exclusive information ownership.

Every important fact, concept, statistic, historical event, example, process,
argument, explanation, or topic MUST have ONE clear section owner.

NEVER assign the same major information to multiple sections.

For every section:

1. Define exactly what information the section owns.
2. Define the specific concepts, facts, examples, or ideas that belong in it.
3. Use the `bullets` field to list concrete information that this section owns.
4. Use the `must_not_cover` field to explicitly identify important topics that
   belong to OTHER sections.
5. Make sure the section's bullets and `must_not_cover` do not contradict each
   other.

The `must_not_cover` field is a HARD boundary for the worker.

If a topic belongs to another section, explicitly place that topic in
`must_not_cover`.

Do not leave important boundaries implicit when they can be stated clearly.


============================================================
HOW TO AVOID OVERLAPPING SECTIONS
============================================================

Before creating the final plan, mentally perform an ownership check.

For every major topic ask:

"Which ONE section owns this information?"

Assign it to exactly one section.

Then ask:

"Could another section accidentally explain this same information?"

If yes, add that topic to the other section's `must_not_cover`.

Sections should complement one another, not compete with one another.


============================================================
SECTION EXAMPLES
============================================================

For example, if the topic is about the G20, a possible ownership structure
could be:

Section: Origins and Evolution

Owns:
- Why the G20 was created
- The 1999 establishment
- Its evolution from a finance-focused forum
- Major historical changes in its role

Must NOT cover:
- Current membership details
- Current organizational structure
- Detailed discussion of recent summit initiatives


Section: Membership and Structure

Owns:
- Current membership
- Member categories
- Rotating presidency
- How the forum operates

Must NOT cover:
- Detailed history of the G20's creation
- Detailed analysis of individual summit initiatives


Section: Current Role and Influence

Owns:
- What the G20 does today
- Areas currently addressed by the forum
- Its influence on international cooperation

Must NOT cover:
- Detailed history of its creation
- Detailed membership mechanics
- Repeating the full historical evolution


These are ONLY examples of ownership thinking.

Do not force this exact structure onto unrelated topics.


============================================================
INTRODUCTION RULE
============================================================

If an introduction section is appropriate:

- Introduce the topic.
- Establish why the topic matters.
- Give only enough context for the reader to understand the article.
- Do NOT provide detailed explanations that belong to later sections.
- Do NOT repeat statistics, examples, history, or detailed concepts that later
  sections own.

The introduction should set up the article, not consume the article.


============================================================
CONCLUSION RULE
============================================================

If a conclusion section is appropriate:

- Synthesize the main ideas.
- Explain the overall takeaway.
- Leave the reader with a useful final perspective.

Do NOT:

- Re-explain every section.
- Repeat large amounts of information.
- Introduce substantial new concepts.
- Repeat detailed statistics or examples from the body.


============================================================
BULLET RULE
============================================================

Every bullet must describe information primarily owned by that section.

Bullets must be:

- Concrete
- Topic-specific
- Non-overlapping
- Useful to the worker writing that section

Avoid vague bullets such as:

- "Explain the topic"
- "Discuss its importance"
- "Talk about key points"
- "Explain how it works"

Instead, identify exactly WHAT the worker should explain.


============================================================
MUST_NOT_COVER RULE
============================================================

`must_not_cover` should contain the important topics that belong to other
sections.

Examples:

- Current membership
- Historical origins
- Detailed implementation steps
- Advanced technical architecture
- Specific examples assigned to another section
- Detailed statistics owned by another section

Do NOT simply copy the same section's bullets into `must_not_cover`.

The purpose of `must_not_cover` is to protect boundaries between workers.


============================================================
WRITING QUALITY
============================================================

The goal is to create a useful, accurate, engaging, and logically structured
blog — not to make the content sound unnecessarily sophisticated.

Prefer:

- Clear explanations
- Useful information
- Logical progression
- Appropriate depth
- Concrete examples when useful
- Reader-friendly language
- Topic-specific terminology when relevant

Avoid:

- Unnecessary jargon
- Forced technical terminology
- Forced analogies
- Developer-oriented language for non-technical topics
- Overly complicated explanations
- Generic filler
- Repetitive sections
- Generic sections that could apply to any unrelated topic


============================================================
CODE RULE
============================================================

Code is OPTIONAL.

Include code only when it is genuinely useful and relevant to the topic.

For programming, software, technical, or other code-related topics:

- Code may be appropriate.
- Set `requires_code` to true only when a code example genuinely improves
  the section.

For non-technical topics:

- Set `requires_code` to false.
- Do not force programming examples into the article.


============================================================
RESEARCH RULE
============================================================

When research evidence is provided:

- Use the evidence to guide factual coverage.
- Prioritize authoritative and relevant sources.
- Do not invent facts that are not supported by the evidence.
- Do not force every source into every section.
- Assign each important research fact to the section that owns it.
- Avoid repeating the same researched fact across multiple sections.
- Mark `requires_research` and `requires_citations` according to the actual
  needs of the section.


============================================================
FINAL OWNERSHIP CHECK
============================================================

Before returning the plan, verify ALL of the following:

1. There are 5–7 sections.
2. Every section has a distinct purpose.
3. Every section has concrete, topic-specific bullets.
4. Major information has exactly one clear owner.
5. Important cross-section boundaries are represented in `must_not_cover`.
6. No section substantially duplicates another section.
7. The introduction does not consume detailed body content.
8. The conclusion does not repeat the entire article.
9. Code is not forced into non-technical topics.
10. Research is used only where relevant.
11. The sections together form a logical progression.
12. The plan can safely be handed to independent parallel workers without
    causing them to write overlapping content.


============================================================
INPUT
============================================================

Topic:
{topic}

Research mode:
{research_mode}

Evidence:
{evidence}


Return the result using the required Plan schema.
"""


# ============================================================
# 2. PLAN VALIDATION
# ============================================================

def validate_plan(plan: Plan) -> Plan:
    """
    Validate the orchestrator's dynamic blog plan.

    The orchestrator may choose 5, 6, or 7 sections,
    but never fewer than 5 or more than 7.
    """

    task_count = len(
        plan.tasks
    )

    if not (
        MIN_SECTIONS
        <= task_count
        <= MAX_SECTIONS
    ):
        raise ValueError(
            f"Plan must contain between "
            f"{MIN_SECTIONS} and {MAX_SECTIONS} sections, "
            f"got {task_count}"
        )

    # --------------------------------------------------------
    # Validate task IDs
    # --------------------------------------------------------

    task_ids = [
        task.id
        for task in plan.tasks
    ]

    if len(
        set(task_ids)
    ) != len(task_ids):

        raise ValueError(
            "Task IDs must be unique."
        )

    expected_ids = list(
        range(
            1,
            task_count + 1,
        )
    )

    if sorted(
        task_ids
    ) != expected_ids:

        raise ValueError(
            "Task IDs must be sequential starting from 1. "
            f"Expected {expected_ids}, "
            f"got {sorted(task_ids)}"
        )

    # --------------------------------------------------------
    # Optional historical validation
    # --------------------------------------------------------
    #
    # This was intentionally kept commented out in the
    # original backend. We preserve that behavior here.
    #
    # common_mistakes_count = sum(
    #     task.section_type == "common_mistakes"
    #     for task in plan.tasks
    # )
    #
    # if common_mistakes_count != 1:
    #
    #     raise ValueError(
    #         "Plan must contain exactly one "
    #         "'common_mistakes' section."
    #     )

    return plan


# ============================================================
# 3. ORCHESTRATOR NODE
# ============================================================

def orchestrator_node(
    state: ChatState,
) -> dict:
    """
    Generate and validate the structured blog plan.
    """

    evidence = state.get(
        "evidence",
        [],
    )

    # Never pass more than the selected 8 sources.
    evidence_for_prompt = [
        item.model_dump()
        for item in evidence[
            :MAX_EVIDENCE_SOURCES
        ]
    ]

    mode = state.get(
        "mode",
        "closed_book",
    )

    plan = _invoke_structured(
        Plan,
        [
            SystemMessage(
                content=ORCH_MESSAGE
            ),
            HumanMessage(
                content=(
                    f"Topic:\n"
                    f"{state['topic']}\n\n"

                    f"Mode:\n"
                    f"{mode}\n\n"

                    "Evidence "
                    "(ONLY use for fresh claims; "
                    "may be empty):\n"
                    f"{evidence_for_prompt}"
                )
            ),
        ],
    )

    # --------------------------------------------------------
    # Validate the generated plan before passing it forward.
    # --------------------------------------------------------

    plan = validate_plan(
        plan
    )

    return {
        "plan": plan
    }