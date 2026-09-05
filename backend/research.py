from typing import List, Optional
import re
from urllib.parse import urlparse

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from .config import (
    MAX_EVIDENCE_SOURCES,
    MAX_RESEARCH_QUERIES,
    TAVILY_RESULTS_PER_QUERY,
    MAX_SNIPPET_CHARS,
)
from .schemas import (
    ChatState,
    RouterDecision,
    EvidencePack,
)
from .llm import _invoke_structured


# ============================================================
# 1. ROUTER
# ============================================================

ROUTER_SYSTEM = """
You are a routing module for a general-purpose blog writing agent.

Your job is to analyze the user's requested topic and decide whether the blog
requires external web research.

The blog may cover ANY subject, including but not limited to:
- Technology
- Programming
- Science
- Health and fitness
- Sports
- Education
- History
- Travel
- Business
- Lifestyle
- Hobbies
- General knowledge

Choose "web" when:
- The topic depends on current or changing information.
- The user asks about recent events, current trends, latest information,
  current statistics, recent products, or other time-sensitive facts.
- External evidence would materially improve factual accuracy.
- The topic contains claims that should be supported by recent or authoritative
  sources.

Choose "closed_book" when:
- The topic can be explained accurately without current web information.
- The topic is primarily evergreen knowledge, concepts, explanations,
  educational material, opinions, or general guidance.
- External research is not necessary for producing a useful and accurate blog.

Return ONLY valid JSON matching the required RouterDecision schema.
Do not include markdown, explanations, or additional text.
"""


def router_node(state: ChatState) -> dict:
    """
    Analyze the topic and decide whether external research is required.
    """

    topic = state["topic"]

    decision = _invoke_structured(
        RouterDecision,
        [
            SystemMessage(
                content=ROUTER_SYSTEM
            ),
            HumanMessage(
                content=(
                    "User's blog topic:\n"
                    f"{topic}"
                )
            ),
        ],
    )

    queries = [
        q.strip()
        for q in decision.queries
        if isinstance(q, str) and q.strip()
    ][:MAX_RESEARCH_QUERIES]

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": queries,
    }


def route_next(state: ChatState) -> str:
    """
    Decide which node should execute after the router.
    """

    if state["needs_research"]:
        return "research"

    return "orchestrator"


# ============================================================
# 2. TAVILY SEARCH HELPERS
# ============================================================

def _compact_snippet(value: Optional[str]) -> str:
    """
    Normalize and shorten a search-result snippet.
    """

    if not value:
        return ""

    text = " ".join(
        str(value).split()
    )

    return text[:MAX_SNIPPET_CHARS]


def _domain_from_url(url: str) -> str:
    """
    Extract a normalized domain from a URL.
    """

    try:
        return (
            urlparse(url)
            .netloc
            .lower()
            .replace("www.", "")
        )

    except Exception:
        return ""


def _tavily_search(
    query: str,
    max_results: int = TAVILY_RESULTS_PER_QUERY,
) -> List[dict]:
    """
    Run one Tavily search and normalize the output.
    """

    tool = TavilySearchResults(
        max_results=max_results
    )

    results = tool.invoke(
        {
            "query": query
        }
    )

    normalized: List[dict] = []

    for result in results or []:

        if not isinstance(result, dict):
            continue

        url = str(
            result.get("url")
            or ""
        ).strip()

        if not url:
            continue

        normalized.append(
            {
                "title": str(
                    result.get("title")
                    or ""
                ).strip(),

                "url": url,

                "snippet": _compact_snippet(
                    result.get("content")
                    or result.get("snippet")
                    or ""
                ),

                "published_at": (
                    result.get("published_date")
                    or result.get("published_at")
                ),

                "source": (
                    result.get("source")
                    or _domain_from_url(url)
                ),
            }
        )

    return normalized


# ============================================================
# 3. DETERMINISTIC SOURCE RANKING
# ============================================================

def _domain_matches(
    domain: str,
    allowed_domain: str,
) -> bool:
    """
    Return True only when the domain is exactly the allowed
    domain or is a legitimate subdomain of it.

    Examples:

    github.com            -> True
    docs.github.com       -> True
    notgithub.com         -> False
    github.com.evil.com   -> False
    """

    domain = domain.lower().strip(".")

    allowed_domain = (
        allowed_domain
        .lower()
        .strip(".")
    )

    return (
        domain == allowed_domain
        or domain.endswith(
            "." + allowed_domain
        )
    )


def _source_authority_score(item: dict) -> int:
    """
    Lightweight deterministic authority scoring.

    This happens BEFORE the evidence synthesizer, so only the
    strongest sources are sent to Gemini.
    """

    url = item.get(
        "url",
        "",
    )

    domain = _domain_from_url(
        url
    )

    score = 0

    high_authority_domains = (
        ".gov",
        ".edu",
        "github.com",
        "arxiv.org",
        "openai.com",
        "developers.google.com",
        "ai.google.dev",
        "cloud.google.com",
        "python.org",
        "pytorch.org",
        "tensorflow.org",
        "microsoft.com",
        "aws.amazon.com",
        "anthropic.com",
        "meta.com",
        "developer.mozilla.org",
    )

    reputable_domains = (
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "nytimes.com",
        "techcrunch.com",
        "theverge.com",
        "wired.com",
        "nature.com",
        "arstechnica.com",
    )

    # --------------------------------------------------------
    # High-authority sources
    # --------------------------------------------------------

    if any(
        (
            domain.endswith(suffix)
            if suffix.startswith(".")
            else _domain_matches(
                domain,
                suffix,
            )
        )
        for suffix in high_authority_domains
    ):
        score += 8

    # --------------------------------------------------------
    # Reputable sources
    # --------------------------------------------------------

    if any(
        _domain_matches(
            domain,
            suffix,
        )
        for suffix in reputable_domains
    ):
        score += 5

    # --------------------------------------------------------
    # Freshness
    # --------------------------------------------------------

    if item.get(
        "published_at"
    ):
        score += 1

    # --------------------------------------------------------
    # Useful snippet
    # --------------------------------------------------------

    if item.get(
        "snippet"
    ):
        score += 2

    return score


def _rank_and_select_sources(
    raw_results: List[dict],
    topic: str,
    queries: List[str],
) -> List[dict]:
    """
    Deduplicate, score and select at most 8 sources.

    The full raw Tavily result set is NEVER passed to Gemini.
    """

    query_terms = set(
        re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]{2,}\b",
            " ".join(
                [topic] + queries
            ).lower(),
        )
    )

    unique = {}

    for item in raw_results:

        url = item.get(
            "url",
            "",
        ).strip()

        if not url:
            continue

        if url not in unique:

            unique[url] = item

            continue

        # Keep the richer duplicate.
        old = unique[url]

        if len(
            item.get(
                "snippet",
                "",
            )
        ) > len(
            old.get(
                "snippet",
                "",
            )
        ):

            unique[url] = item

    scored = []

    for item in unique.values():

        title = item.get(
            "title",
            "",
        ).lower()

        snippet = item.get(
            "snippet",
            "",
        ).lower()

        text = f"{title} {snippet}"

        overlap = sum(
            1
            for term in query_terms
            if term in text
        )

        score = (
            overlap * 2
            + _source_authority_score(item)
        )

        scored.append(
            (
                score,
                item,
            )
        )

    scored.sort(
        key=lambda pair: (
            pair[0],
            len(
                pair[1].get(
                    "snippet",
                    "",
                )
            ),
        ),
        reverse=True,
    )

    return [
        item
        for _, item in scored[
            :MAX_EVIDENCE_SOURCES
        ]
    ]


# ============================================================
# 4. RESEARCH SYNTHESIZER
# ============================================================

RESEARCH_SYSTEM = """
You are a research synthesizer for technical writing.

You are given ONLY the most useful web sources selected by a
deterministic ranking stage.

Create an EvidencePack from those sources.

Rules:

- Preserve the supplied URLs exactly.
- Only include items with a non-empty URL.
- Do not invent URLs.
- Prefer relevant and authoritative sources.
- Prefer official documentation, company sources,
  research papers, government sources, and reputable
  publications when available.
- Preserve an explicitly supplied publication date.
- Never guess a publication date.
- Keep snippets concise.
- Do not create additional sources.
- Deduplicate by URL.
- Return at most 8 evidence items.

Return only the EvidencePack fields.
"""


def research_node(state: ChatState) -> dict:
    """
    Search Tavily, rank locally, and send ONLY the best 8
    sources to Gemini.
    """

    queries = (
        state.get(
            "queries",
            [],
        )
        or []
    )[:MAX_RESEARCH_QUERIES]

    raw_results: List[dict] = []

    for query in queries:

        try:

            results = _tavily_search(
                query,
                max_results=TAVILY_RESULTS_PER_QUERY,
            )

            raw_results.extend(
                results
            )

        except Exception as exc:

            print(
                f"Research failed for query "
                f"'{query}': {exc}"
            )

    if not raw_results:

        return {
            "evidence": []
        }

    selected_sources = _rank_and_select_sources(
        raw_results=raw_results,
        topic=state["topic"],
        queries=queries,
    )

    # IMPORTANT:
    # Only selected_sources (max 8) are passed to Gemini.
    compact_sources = []

    for item in selected_sources:

        compact_sources.append(
            {
                "title": item.get(
                    "title",
                    "",
                ),

                "url": item.get(
                    "url",
                    "",
                ),

                "snippet": item.get(
                    "snippet",
                    "",
                ),

                "published_at": item.get(
                    "published_at"
                ),

                "source": item.get(
                    "source"
                ),
            }
        )

    pack = _invoke_structured(
        EvidencePack,
        [
            SystemMessage(
                content=RESEARCH_SYSTEM
            ),
            HumanMessage(
                content=(
                    "Topic:\n"
                    f"{state['topic']}\n\n"
                    "Selected source candidates "
                    f"(maximum {MAX_EVIDENCE_SOURCES}):\n"
                    f"{compact_sources}"
                )
            ),
        ],
    )

    # Final deterministic URL deduplication + hard cap.
    dedup = {}

    for item in pack.evidence:

        if item.url:

            dedup[
                item.url
            ] = item

    final_evidence = list(
        dedup.values()
    )[
        :MAX_EVIDENCE_SOURCES
    ]

    return {
        "evidence": final_evidence
    }