"""
Agent 3: Trend Analysis Agent (Milestone 2).
Specializes in tracking sentiment trajectory, volume velocity, and overall product health.
"""

from crewai import Agent, Task


def create_trend_analysis_agent(llm) -> Agent:
    """Instantiate the Product Trend & Sentiment Trajectory Analyst Agent."""
    return Agent(
        role="Product Trend & Sentiment Trajectory Analyst",
        goal="Analyze sentiment shifts, feedback volume velocity over time, and formulate overall product sentiment health insights",
        backstory="""You are a Quantitative Product Operations Lead and Sentiment Analytics Specialist.
You track how customer sentiment shifts across app releases, detect whether satisfaction is trending up or down,
and evaluate overall product health metrics to guide executive decisions.""",
        llm=llm,
        verbose=True,
        memory=False,
    )


def create_trend_task(agent: Agent, feedback_summary: str, workspace_name: str) -> Task:
    """Create the trend analysis and health evaluation task."""
    return Task(
        description=f"""Analyze the sentiment distribution, temporal trends, and rating metrics for workspace '{workspace_name}':
{feedback_summary}

Tasks:
1. Assess the overall Product Health Score (0-100) based on positive vs negative feedback ratio and ratings.
2. Identify notable sentiment shifts or velocity patterns across feedback categories.
3. Formulate a 2-paragraph executive briefing summarizing current product health and immediate focus areas.""",
        expected_output="""An executive briefing on product health score, trajectory analysis, and key sentiment indicators.""",
        agent=agent,
    )
