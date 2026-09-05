from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from .config import MODEL_NAME


llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0.7,
)


def _extract_response_text(response: Any) -> str:
    """
    Normalize LangChain/Gemini response content into plain text.
    """

    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []

        def collect(item):
            if isinstance(item, str):
                if item.strip():
                    parts.append(item)
                return

            if isinstance(item, dict):
                text_value = item.get("text")

                if isinstance(text_value, str):
                    if text_value.strip():
                        parts.append(text_value)
                    return

                nested = item.get("content")

                if isinstance(nested, str):
                    if nested.strip():
                        parts.append(nested)
                    return

                if isinstance(nested, list):
                    for nested_item in nested:
                        collect(nested_item)

        for item in content:
            collect(item)

        return "\n".join(parts).strip()

    return str(content).strip()


def _invoke_structured(schema: Any, messages: Any) -> Any:
    """
    Invoke Gemini using LangChain structured output.

    Gemini's structured-output path returns a Pydantic object.
    This helper also validates unexpected structured results.
    """

    structured_llm = llm.with_structured_output(schema)

    result = structured_llm.invoke(messages)

    if isinstance(result, schema):
        return result

    try:
        return schema.model_validate(result)

    except Exception as exc:
        raise ValueError(
            "Gemini returned an unexpected structured-output "
            f"format for {schema.__name__}: {result!r}"
        ) from exc