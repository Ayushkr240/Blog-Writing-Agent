import streamlit as st
from backend import run_stream


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Blog Writing Agent",
    page_icon="✍️",
    layout="wide",
)


# ============================================================
# SESSION STATE
# ============================================================

# The final blog must survive Streamlit reruns.
if "final_md" not in st.session_state:
    st.session_state.final_md = ""

if "filename" not in st.session_state:
    st.session_state.filename = "blog.md"

if "evidence_count" not in st.session_state:
    st.session_state.evidence_count = 0

if "generated_topic" not in st.session_state:
    st.session_state.generated_topic = ""


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

        .main-title {
            font-size: 2.6rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #777;
            font-size: 1.05rem;
            margin-bottom: 1.5rem;
        }

        .progress-box {
            padding: 1rem;
            border: 1px solid #e5e5e5;
            border-radius: 12px;
            margin-bottom: 1rem;
            background: #fafafa;
        }

        .stage {
            padding: 0.65rem 0.8rem;
            border-radius: 8px;
            margin: 0.35rem 0;
            font-size: 0.95rem;
        }

        .stage-done {
            background: #eaf7ee;
            color: #176b36;
        }

        .stage-running {
            background: #fff7df;
            color: #8a6500;
        }

        .stage-waiting {
            background: #f3f3f3;
            color: #777;
        }

        .blog-output {
            padding: 1.5rem;
            border: 1px solid #e5e5e5;
            border-radius: 12px;
            background: white;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">✍️ Blog Writing Agent</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        Enter a topic and watch the LangGraph workflow research,
        plan, write, and finalize your technical blog.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# INPUT
# ============================================================

topic = st.text_input(
    "Blog Topic",
    placeholder="Example: How LangGraph works with parallel agents",
    help="Enter the topic you want the blog-writing agent to cover.",
)

generate = st.button(
    "🚀 Generate Blog",
    type="primary",
    use_container_width=True,
)


# ============================================================
# PROGRESS UI
# ============================================================

STAGES = {
    "router": "🔎 Analyzing the topic",
    "research": "🌐 Collecting evidence",
    "orchestrator": "🧠 Creating the blog plan",
    "worker": "✍️ Writing blog sections",
    "reducer": "✨ Finalizing the blog",
}


def render_progress(
    status_placeholder,
    current_stage,
    completed_stages,
    written_sections,
):
    """Render the workflow progress."""

    html = '<div class="progress-box">'

    ordered_stages = [
        "router",
        "research",
        "orchestrator",
        "worker",
        "reducer",
    ]

    for stage in ordered_stages:

        label = STAGES[stage]

        if stage in completed_stages:
            state_class = "stage-done"
            icon = "✅"

        elif stage == current_stage:
            state_class = "stage-running"
            icon = "⏳"

        else:
            state_class = "stage-waiting"
            icon = "○"

        if stage == "worker" and written_sections:
            label = (
                f"{label} "
                f"({len(written_sections)}/5 sections)"
            )

        html += (
            f'<div class="stage {state_class}">'
            f"{icon} {label}"
            f"</div>"
        )

    html += "</div>"

    status_placeholder.markdown(
        html,
        unsafe_allow_html=True,
    )


# ============================================================
# BLOG GENERATION
# ============================================================

if generate:

    # --------------------------------------------------------
    # Validate topic
    # --------------------------------------------------------

    if not topic.strip():
        st.warning("Please enter a blog topic first.")
        st.stop()

    # --------------------------------------------------------
    # IMPORTANT:
    # Clear the previous result ONLY when the user starts
    # generating a NEW blog.
    #
    # We do NOT clear this during normal Streamlit reruns.
    # --------------------------------------------------------

    st.session_state.final_md = ""
    st.session_state.filename = "blog.md"
    st.session_state.evidence_count = 0
    st.session_state.generated_topic = topic.strip()

    # Local workflow state
    completed_stages = set()
    written_sections = {}
    evidence_count = 0
    final_md = ""

    st.divider()

    left, right = st.columns([1, 2])

    # ========================================================
    # LEFT — WORKFLOW PROGRESS
    # ========================================================

    with left:

        st.subheader("Workflow Progress")

        progress_placeholder = st.empty()

        render_progress(
            progress_placeholder,
            current_stage="router",
            completed_stages=set(),
            written_sections=written_sections,
        )

    # ========================================================
    # RIGHT — LIVE ACTIVITY
    # ========================================================

    with right:

        st.subheader("Live Activity")

        activity_placeholder = st.empty()

        activity_messages = []

        def add_activity(message):

            activity_messages.append(message)

            # Keep the activity panel readable
            visible = activity_messages[-8:]

            activity_placeholder.markdown(
                "\n".join(
                    f"- {item}"
                    for item in visible
                )
            )

    # ========================================================
    # RUN BACKEND
    # ========================================================

    try:

        for event in run_stream(
            topic.strip()
        ):

            if not isinstance(event, dict):
                continue

            # =================================================
            # ROUTER
            # =================================================

            if "router" in event:

                completed_stages.add(
                    "router"
                )

                router_update = event.get(
                    "router",
                    {},
                )

                mode = router_update.get(
                    "mode",
                    "unknown",
                )

                needs_research = router_update.get(
                    "needs_research",
                    False,
                )

                if needs_research:

                    add_activity(
                        f"Topic analyzed → research required "
                        f"({mode} mode)."
                    )

                    current_stage = "research"

                else:

                    add_activity(
                        f"Topic analyzed → no web research "
                        f"required ({mode} mode)."
                    )

                    current_stage = "orchestrator"

                render_progress(
                    progress_placeholder,
                    current_stage=current_stage,
                    completed_stages=completed_stages,
                    written_sections=written_sections,
                )

            # =================================================
            # RESEARCH
            # =================================================

            elif "research" in event:

                completed_stages.add(
                    "research"
                )

                research_update = event.get(
                    "research",
                    {},
                )

                evidence = research_update.get(
                    "evidence",
                    [],
                )

                evidence_count = len(
                    evidence
                )

                add_activity(
                    f"Evidence collected: "
                    f"{evidence_count} source(s)."
                )

                render_progress(
                    progress_placeholder,
                    current_stage="orchestrator",
                    completed_stages=completed_stages,
                    written_sections=written_sections,
                )

            # =================================================
            # ORCHESTRATOR
            # =================================================

            elif "orchestrator" in event:

                completed_stages.add(
                    "orchestrator"
                )

                orchestrator_update = event.get(
                    "orchestrator",
                    {},
                )

                plan = orchestrator_update.get(
                    "plan"
                )

                if plan is not None:

                    # Pydantic object
                    if hasattr(
                        plan,
                        "blog_title",
                    ):

                        blog_title = (
                            plan.blog_title
                        )

                        task_count = len(
                            plan.tasks
                        )

                    # Dictionary fallback
                    elif isinstance(
                        plan,
                        dict,
                    ):

                        blog_title = plan.get(
                            "blog_title",
                            "Untitled Blog",
                        )

                        task_count = len(
                            plan.get(
                                "tasks",
                                [],
                            )
                        )

                    else:

                        blog_title = (
                            "Blog plan created"
                        )

                        task_count = 5

                    add_activity(
                        f"Plan created: "
                        f"'{blog_title}' "
                        f"with {task_count} sections."
                    )

                else:

                    add_activity(
                        "Blog plan created."
                    )

                render_progress(
                    progress_placeholder,
                    current_stage="worker",
                    completed_stages=completed_stages,
                    written_sections=written_sections,
                )

            # =================================================
            # WORKERS
            # =================================================

            elif "worker" in event:

                worker_update = event.get(
                    "worker",
                    {},
                )

                sections = worker_update.get(
                    "sections",
                    [],
                )

                for section in sections:

                    if (
                        isinstance(
                            section,
                            (tuple, list),
                        )
                        and len(section) == 2
                    ):

                        task_id = section[0]
                        section_md = section[1]

                        written_sections[
                            task_id
                        ] = section_md

                        add_activity(
                            f"Section "
                            f"{task_id}/5 completed."
                        )

                render_progress(
                    progress_placeholder,
                    current_stage="worker",
                    completed_stages=completed_stages,
                    written_sections=written_sections,
                )

            # =================================================
            # REDUCER / FINALIZER
            # =================================================

            elif "reducer" in event:

                completed_stages.add(
                    "worker"
                )

                completed_stages.add(
                    "reducer"
                )

                reducer_update = event.get(
                    "reducer",
                    {},
                )

                final_md = reducer_update.get(
                    "final_md",
                    "",
                )

                add_activity(
                    "All sections combined and blog finalized."
                )

                render_progress(
                    progress_placeholder,
                    current_stage="reducer",
                    completed_stages=completed_stages,
                    written_sections=written_sections,
                )

        # ====================================================
        # SAVE FINAL BLOG INTO SESSION STATE
        # ====================================================

        if final_md:

            st.session_state.final_md = (
                final_md
            )

            st.session_state.evidence_count = (
                evidence_count
            )

            # ------------------------------------------------
            # Generate a safe filename
            # ------------------------------------------------

            filename = "blog.md"

            lines = final_md.splitlines()

            if lines:

                first_line = (
                    lines[0]
                    .strip()
                )

                if first_line.startswith(
                    "# "
                ):

                    title = (
                        first_line[2:]
                        .strip()
                    )

                    invalid_chars = (
                        '<>:"/\\|?*'
                    )

                    filename = "".join(
                        char
                        for char in title
                        if char
                        not in invalid_chars
                    ).strip()

                    if not filename:
                        filename = "blog"

                    filename += ".md"

            st.session_state.filename = (
                filename
            )

        else:

            st.error(
                "The workflow finished, but no final blog "
                "was returned."
            )

    except Exception as exc:

        st.error(
            "❌ An error occurred while generating the blog."
        )

        with st.expander(
            "Show technical error"
        ):

            st.exception(exc)


# ============================================================
# DISPLAY SAVED BLOG
# ============================================================
#
# This section is OUTSIDE `if generate`.
#
# That is the key fix.
#
# Even if Streamlit reruns after clicking Download,
# session_state still contains the generated blog.
# ============================================================

if st.session_state.final_md:

    st.divider()

    # ========================================================
    # SUCCESS
    # ========================================================

    st.success(
        "🎉 Blog generated successfully!"
    )

    if st.session_state.evidence_count:

        st.caption(
            f"Research used "
            f"{st.session_state.evidence_count} "
            f"evidence source(s)."
        )

    # ========================================================
    # FINAL BLOG
    # ========================================================

    st.divider()

    st.subheader(
        "📖 Final Blog"
    )

    st.markdown(
        '<div class="blog-output">',
        unsafe_allow_html=True,
    )

    st.markdown(
        st.session_state.final_md
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    st.divider()

    st.subheader(
        "📥 Download"
    )

    st.download_button(
        label="⬇️ Download Markdown File",

        data=st.session_state.final_md,

        file_name=st.session_state.filename,

        mime="text/markdown",

        use_container_width=True,

        # Prevent unnecessary Streamlit rerun
        # when the download button is clicked.
        on_click="ignore",
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Built with LangGraph, Gemini, Tavily, LangChain and Streamlit."
)
