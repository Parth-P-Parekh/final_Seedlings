from typing import Optional

SYSTEM_PROMPT = """You are an expert GitHub issue analyzer. Your task is to analyze GitHub issues and provide structured, actionable insights.

You must ALWAYS respond with valid JSON matching this exact structure:
{
  "summary": "A one-sentence summary of the issue",
  "type": "bug|feature_request|documentation|question|other",
  "priority_score": {
    "score": 1-5,
    "justification": "Why this priority level (1-2 sentences)"
  },
  "suggested_labels": ["label1", "label2", "label3"],
  "potential_impact": "Brief sentence on impact if this is a bug"
}

CRITICAL RULES:
1. Response MUST be valid JSON only - no markdown, no code blocks
2. type MUST be one of: bug, feature_request, documentation, question, other
3. priority_score.score MUST be integer 1-5
4. suggested_labels MUST be array of 2-3 strings
5. All string values must be concise and clear"""

FEW_SHOT_EXAMPLES = [
    {
        "issue": {
            "title": "Bug: React rendering performance drops with 1000+ items",
            "body": "When rendering lists with 1000 or more items, React takes 5+ seconds to mount. This causes browser hang.",
            "comments": [
                "Same issue here with 500+ items",
                "Can reproduce on React 18.2.0",
                "Might be reconciliation algorithm issue"
            ]
        },
        "analysis": {
            "summary": "React rendering performance degrades significantly with large lists (1000+ items).",
            "type": "bug",
            "priority_score": {
                "score": 4,
                "justification": "Critical for apps handling large datasets. Blocks production usage at scale."
            },
            "suggested_labels": ["performance", "react-core", "urgent"],
            "potential_impact": "Users with large datasets experience browser hangs, poor UX."
        }
    },
    {
        "issue": {
            "title": "Feature: Add built-in dark mode support",
            "body": "Request for React to include dark mode utilities in core library. Would help with theme switching.",
            "comments": [
                "Great idea! Many apps need this",
                "Could be a separate package instead"
            ]
        },
        "analysis": {
            "summary": "Request to add native dark mode support utilities to React core.",
            "type": "feature_request",
            "priority_score": {
                "score": 2,
                "justification": "Nice-to-have feature. Can be implemented via separate packages."
            },
            "suggested_labels": ["enhancement", "style", "low-priority"],
            "potential_impact": "Would reduce boilerplate for theme management in React apps."
        }
    },
    {
        "issue": {
            "title": "Docs: useEffect cleanup function documentation unclear",
            "body": "The documentation for cleanup functions in useEffect doesn't explain when they're called. Need clarification.",
            "comments": [
                "Agree, took me days to understand this",
                "Examples would help significantly"
            ]
        },
        "analysis": {
            "summary": "Documentation for useEffect cleanup function behavior needs clarification with examples.",
            "type": "documentation",
            "priority_score": {
                "score": 3,
                "justification": "Impacts developer experience. High confusion among learners."
            },
            "suggested_labels": ["documentation", "help-wanted", "good-first-issue"],
            "potential_impact": "Clearer docs will reduce developer confusion and support questions."
        }
    }
]


def create_analysis_prompt(
    issue_title: str,
    issue_body: str,
    comments: list[str],
    repo_context: Optional[str] = None
) -> str:
    """
    Create a detailed prompt for LLM analysis with few-shot examples.

    Args:
        issue_title: Title of the GitHub issue
        issue_body: Body/description of the issue
        comments: List of comments on the issue
        repo_context: Optional repository context (e.g., "React is a UI library")

    Returns:
        Complete prompt string with few-shot examples
    """

    # Truncate long content to avoid token limits
    truncated_body = issue_body[:8000] if len(issue_body) > 8000 else issue_body
    truncated_comments = [
        c[:1000] if len(c) > 1000 else c
        for c in comments[:20]
    ]

    # Build few-shot prompt section
    few_shot_section = "\nREFERENCE EXAMPLES (follow this format exactly):\n"
    for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
        few_shot_section += f"\nEXAMPLE {i}:\n"
        few_shot_section += f"Issue Title: {example['issue']['title']}\n"
        few_shot_section += f"Issue Body: {example['issue']['body']}\n"
        few_shot_section += f"Comments: {example['issue']['comments']}\n"
        few_shot_section += f"Analysis Result:\n{example['analysis']}\n"

    # Build the main analysis prompt
    prompt = f"""{SYSTEM_PROMPT}

{few_shot_section}

---

NOW ANALYZE THIS ISSUE:

Repository: {repo_context or 'Unknown'}

Issue Title: {issue_title}

Issue Body:
{truncated_body}

Comments from Community:
{chr(10).join(f'- {c}' for c in truncated_comments) if truncated_comments else '(No comments yet)'}

---

Provide ONLY the JSON analysis result, no additional text:
"""

    return prompt


def create_batch_analysis_prompt(issues: list[dict]) -> str:
    """
    Create a prompt for batch analysis of multiple issues.

    Args:
        issues: List of issue dictionaries

    Returns:
        Complete batch analysis prompt
    """

    issues_section = "\n".join([
        f"""
Issue #{i+1}:
- Title: {issue['title']}
- Body: {issue['body'][:500]}...
- Comments: {len(issue.get('comments', []))} comments
"""
        for i, issue in enumerate(issues[:5])  # Max 5 for batch
    ])

    prompt = f"""{SYSTEM_PROMPT}

Analyze the following {len(issues)} issues and return a JSON array with analysis for each:

{issues_section}

Return format: [{{"summary": "...", "type": "...", ...}}, {{"summary": "...", "type": "...", ...}}]
"""

    return prompt


def create_summary_prompt(analyses: list[dict]) -> str:
    """
    Create a prompt to summarize multiple analyses.

    Args:
        analyses: List of analysis results

    Returns:
        Summary prompt
    """

    prompt = f"""Based on these {len(analyses)} GitHub issue analyses, provide:
1. Top 3 most critical issues
2. Common issue patterns
3. Recommended prioritization strategy

Analyses:
{analyses}

Provide response as a JSON object with keys: critical_issues, patterns, prioritization.
"""

    return prompt