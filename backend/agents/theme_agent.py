"""
Agent 1: Theme & Pain Point Agent (Milestone 2).
Specializes in extracting recurring product themes and diagnosing customer friction areas
with explainable severity and root-cause analysis.
"""

from crewai import Agent, Task
from typing import Optional


def create_theme_and_pain_point_agent(llm) -> Agent:
    """Instantiate the Theme & Customer Pain-Point Analyst Agent."""
    return Agent(
        role="Theme & Customer Pain-Point Analyst",
        goal="Extract recurring high-level product themes and uncover high-severity customer pain points with root-cause explanations",
        backstory="""You are a seasoned Principal User Researcher and Feedback Diagnostics Specialist.
You have analyzed hundreds of thousands of customer reviews and support tickets.
Your superpower is identifying hidden technical and UX frictions beneath customer complaints,
grouping conversations into clear product themes, and formulating precise root-cause diagnoses.""",
        llm=llm,
        verbose=True,
        memory=False,
    )


def create_theme_task(agent: Agent, feedback_summary: str, workspace_name: str) -> Task:
    """Create the theme extraction task."""
    return Task(
        description=f"""Analyze the customer feedback for workspace '{workspace_name}':
{feedback_summary}

Tasks:
1. Identify the top recurring product themes (e.g., Performance, Authentication, UI/UX, Sync).
2. For each theme, identify the primary category, dominant sentiment, and representative quotes.
3. Summarize what users love vs what causes friction in each theme.""",
        expected_output="""A structured report listing recurring product themes, category alignments, sentiment breakdowns, and sample quotes.""",
        agent=agent,
    )


def create_pain_point_task(agent: Agent, feedback_summary: str, workspace_name: str) -> Task:
    """Create the customer pain point detection task."""
    return Task(
        description=f"""Analyze the customer complaints, bug reports, and low-rating feedback in workspace '{workspace_name}':
{feedback_summary}

Tasks:
1. Identify the top critical customer pain points.
2. Determine the Severity Level (High, Medium, Low) and affected workflow for each.
3. Formulate a clear Root-Cause Diagnosis and Recommended Action for the product/engineering team.""",
        expected_output="""A list of ranked customer pain points with severity ratings, root-cause diagnostics, and actionable engineering recommendations.""",
        agent=agent,
    )
