import streamlit as st

from backend import run_stream

from exporters import (
    export_markdown,
    export_text,
    export_html,
    export_docx,
    export_pdf,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Blog Writing Agent",
    page_icon="✍️",
    layout="wide",
)


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
# SESSION STATE
# ============================================================

if "final_md" not in st.session_state:
    st.session_state.final_md = ""

if "evidence_count" not in st.session_state:
    st.session_state.evidence_count = 0

if "total_sections" not in st.session_state:
    st.session_state.total_sections = 0


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
    "worker": "✍️ Generating the blog",
    "reducer": "✨ Finalizing the blog",
}


def render_progress(
    status_placeholder,
    current_stage,
    completed_stages,
):
    """
    Render the current LangGraph workflow progress.

    The worker stage represents the complete blog-generation
    process. Individual worker/section progress is intentionally
    not displayed.
    """

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

        st.warning(
            "Please enter a blog topic first."
        )

        st.stop()

    # --------------------------------------------------------
    # Reset state for a NEW generation
    # --------------------------------------------------------

    st.session_state.final_md = ""
    st.session_state.evidence_count = 0
    st.session_state.total_sections = 0

    # --------------------------------------------------------
    # Local workflow state
    # --------------------------------------------------------

    completed_stages = set()

    final_md = ""

    evidence_count = 0

    total_sections = 0

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    st.divider()

    left, right = st.columns(
        [1, 2]
    )

    # ========================================================
    # LEFT COLUMN — WORKFLOW PROGRESS
    # ========================================================

    with left:

        st.subheader(
            "Workflow Progress"
        )

        progress_placeholder = st.empty()

        render_progress(
            progress_placeholder,
            current_stage="router",
            completed_stages=completed_stages,
        )

    # ========================================================
    # RIGHT COLUMN — LIVE ACTIVITY
    # ========================================================

    with right:

        st.subheader(
            "Live Activity"
        )

        activity_placeholder = st.empty()

        activity_messages = []

        def add_activity(message):
            """
            Add a message to the live activity panel.
            """

            activity_messages.append(
                message
            )

            visible = activity_messages[-8:]

            activity_placeholder.markdown(
                "\n".join(
                    f"- {item}"
                    for item in visible
                )
            )

    # ========================================================
    # RUN LANGGRAPH WORKFLOW
    # ========================================================

    try:

        for event in run_stream(
            topic.strip()
        ):

            if not isinstance(
                event,
                dict,
            ):
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
                        f"Topic analyzed → "
                        f"research required "
                        f"({mode} mode)."
                    )

                    current_stage = "research"

                else:

                    add_activity(
                        f"Topic analyzed → "
                        f"no web research required "
                        f"({mode} mode)."
                    )

                    current_stage = "orchestrator"

                render_progress(
                    progress_placeholder,
                    current_stage=current_stage,
                    completed_stages=completed_stages,
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

                    # -----------------------------------------
                    # Pydantic Plan object
                    # -----------------------------------------

                    if hasattr(
                        plan,
                        "blog_title",
                    ):

                        blog_title = (
                            plan.blog_title
                        )

                        total_sections = len(
                            plan.tasks
                        )

                    # -----------------------------------------
                    # Dictionary fallback
                    # -----------------------------------------

                    elif isinstance(
                        plan,
                        dict,
                    ):

                        blog_title = plan.get(
                            "blog_title",
                            "Untitled Blog",
                        )

                        total_sections = len(
                            plan.get(
                                "tasks",
                                [],
                            )
                        )

                    # -----------------------------------------
                    # Unknown plan format
                    # -----------------------------------------

                    else:

                        blog_title = (
                            "Blog plan created"
                        )

                        total_sections = 0

                    # -----------------------------------------
                    # Activity message
                    # -----------------------------------------

                    if total_sections:

                        add_activity(
                            f"Plan created: "
                            f"'{blog_title}' "
                            f"with "
                            f"{total_sections} sections."
                        )

                    else:

                        add_activity(
                            f"Plan created: "
                            f"'{blog_title}'."
                        )

                else:

                    add_activity(
                        "Blog plan created."
                    )

                render_progress(
                    progress_placeholder,
                    current_stage="worker",
                    completed_stages=completed_stages,
                )

            # =================================================
            # WORKERS / BLOG GENERATION
            # =================================================

            elif "workers" in event:

                completed_stages.add(
                    "worker"
                )

                add_activity(
                    "Blog generation completed."
                )

                render_progress(
                    progress_placeholder,
                    current_stage="reducer",
                    completed_stages=completed_stages,
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

                # ------------------------------------------------
                # Persist generated blog
                # ------------------------------------------------

                if final_md:

                    st.session_state.final_md = (
                        final_md
                    )

                add_activity(
                    "All sections combined "
                    "and blog finalized."
                )

                render_progress(
                    progress_placeholder,
                    current_stage=None,
                    completed_stages=completed_stages,
                )

        # ====================================================
        # FINAL RESULT
        # ====================================================

        if final_md:

            # ------------------------------------------------
            # Persist generated blog and metadata
            # ------------------------------------------------

            st.session_state.final_md = final_md

            st.session_state.evidence_count = (
                evidence_count
            )

            st.session_state.total_sections = (
                total_sections
            )

            # ------------------------------------------------
            # Mark all stages complete
            # ------------------------------------------------

            render_progress(
                progress_placeholder,
                current_stage=None,
                completed_stages={
                    "router",
                    "research",
                    "orchestrator",
                    "worker",
                    "reducer",
                },
            )

            st.success(
                "🎉 Blog generated successfully!"
            )

        else:

            st.error(
                "The workflow finished, "
                "but no final blog was returned."
            )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as exc:

        st.error(
            "❌ An error occurred while "
            "generating the blog."
        )

        with st.expander(
            "Show technical error"
        ):

            st.exception(exc)


# ============================================================
# FINAL BLOG
# ============================================================

if st.session_state.final_md:

    # --------------------------------------------------------
    # Research information
    # --------------------------------------------------------

    if st.session_state.evidence_count:

        st.caption(
            f"Research used "
            f"{st.session_state.evidence_count} "
            f"evidence source(s)."
        )

    # --------------------------------------------------------
    # Section information
    # --------------------------------------------------------

    if st.session_state.total_sections:

        st.caption(
            f"The orchestrator created "
            f"a {st.session_state.total_sections}-section blog."
        )

    st.divider()

    # --------------------------------------------------------
    # Blog
    # --------------------------------------------------------

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


# ============================================================
# BLOG EXPORT
# ============================================================

if st.session_state.final_md:

    st.divider()

    st.subheader(
        "📥 Export Blog"
    )

    export_format = st.selectbox(
        "Choose export format",
        options=[
            "Markdown (.md)",
            "Plain Text (.txt)",
            "HTML (.html)",
            "Word Document (.docx)",
            "PDF (.pdf)",
        ],
        key="export_format",
    )

    # --------------------------------------------------------
    # Generate export based on selected format
    # --------------------------------------------------------

    if export_format == "Markdown (.md)":

        export_data, export_filename = export_markdown(
            st.session_state.final_md
        )

        export_mime = "text/markdown"

    elif export_format == "Plain Text (.txt)":

        export_data, export_filename = export_text(
            st.session_state.final_md
        )

        export_mime = "text/plain"

    elif export_format == "HTML (.html)":

        export_data, export_filename = export_html(
            st.session_state.final_md
        )

        export_mime = "text/html"

    elif export_format == "Word Document (.docx)":

        export_data, export_filename = export_docx(
            st.session_state.final_md
        )

        export_mime = (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )

    elif export_format == "PDF (.pdf)":

        export_data, export_filename = export_pdf(
            st.session_state.final_md
        )

        export_mime = "application/pdf"

    # --------------------------------------------------------
    # Download button
    # --------------------------------------------------------

    st.download_button(
        label=f"⬇️ Download {export_format}",
        data=export_data,
        file_name=export_filename,
        mime=export_mime,
        use_container_width=True,
        on_click="ignore",
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()