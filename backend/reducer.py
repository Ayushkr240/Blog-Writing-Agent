from .schemas import ChatState


def reducer_node(state: ChatState) -> dict:
    """
    Validate worker results and assemble the final Markdown blog.
    """

    plan = state.get("plan")

    if plan is None:
        raise ValueError(
            "Cannot reduce because plan is None."
        )

    sections = state.get(
        "sections",
        []
    )

    # --------------------------------------------------------
    # 1. Build expected task map
    # --------------------------------------------------------

    task_by_id = {
        task.id: task
        for task in plan.tasks
    }

    expected_ids = set(
        task_by_id.keys()
    )

    # --------------------------------------------------------
    # 2. Collect returned worker IDs
    # --------------------------------------------------------

    returned_ids = [
        task_id
        for task_id, _ in sections
    ]

    returned_id_set = set(
        returned_ids
    )

    # --------------------------------------------------------
    # 3. Detect duplicate worker results
    # --------------------------------------------------------

    if len(returned_ids) != len(returned_id_set):

        duplicates = sorted(
            task_id
            for task_id in returned_id_set
            if returned_ids.count(task_id) > 1
        )

        raise ValueError(
            "Duplicate worker results detected for "
            f"task IDs: {duplicates}"
        )

    # --------------------------------------------------------
    # 4. Detect unknown worker results
    # --------------------------------------------------------

    unknown_ids = (
        returned_id_set
        - expected_ids
    )

    if unknown_ids:

        raise ValueError(
            "Worker returned unknown task IDs: "
            f"{sorted(unknown_ids)}"
        )

    # --------------------------------------------------------
    # 5. Detect missing worker results
    # --------------------------------------------------------

    missing_ids = (
        expected_ids
        - returned_id_set
    )

    if missing_ids:

        missing_titles = [
            task_by_id[task_id].title
            for task_id in sorted(
                missing_ids
            )
        ]

        raise ValueError(
            "Missing worker results for task IDs: "
            f"{sorted(missing_ids)}. "
            f"Missing sections: {missing_titles}"
        )

    # --------------------------------------------------------
    # 6. Validate worker content
    # --------------------------------------------------------

    for task_id, markdown in sections:

        if (
            not isinstance(markdown, str)
            or not markdown.strip()
        ):

            task_title = task_by_id[
                task_id
            ].title

            raise ValueError(
                "Worker returned empty content for "
                f"task {task_id}: '{task_title}'"
            )

    # --------------------------------------------------------
    # 7. Sort sections by task ID
    # --------------------------------------------------------

    ordered_sections = []

    for task_id, markdown in sorted(
        sections,
        key=lambda item: item[0],
    ):

        task = task_by_id[
            task_id
        ]

        ordered_sections.append(
            f"## {task.title}\n\n"
            f"{markdown.strip()}"
        )

    # --------------------------------------------------------
    # 8. Assemble final blog
    # --------------------------------------------------------

    body = "\n\n".join(
        ordered_sections
    ).strip()

    return {
        "final_md": (
            f"# {plan.blog_title}\n\n"
            f"{body}\n"
        )
    }