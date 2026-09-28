"""
Agent 2: Feature Request Agent (Milestone 2).
Specializes in extracting user feature requests, semantically grouping similar capabilities,
and computing priority and demand levels.
"""

from crewai import Agent, Task


def create_feature_request_agent(llm) -> Agent:
    """Instantiate the Feature Request & Opportunity Clustering Agent."""
    return Agent(
        role="Feature Request & Opportunity Clustering Strategist",
        goal="Extract customer feature requests, cluster related capabilities into cohesive opportunities, and calculate priority and demand scores",
        backstory="""You are an expert Technical Product Manager with deep experience in product discovery.
You excel at parsing thousands of raw user feature suggestions, filtering noise,
semantically grouping related requests into unified feature clusters, and calculating
data-driven priority scores based on customer demand and business impact.""",
        llm=llm,
        verbose=True,
        memory=False,
    )


def create_feature_clustering_task(agent: Agent, feedback_summary: str, workspace_name: str) -> Task:
    """Create the feature clustering and prioritization task."""
    return Task(
        description=f"""Review customer feature suggestions, enhancements, and wishlist items in workspace '{workspace_name}':
{feedback_summary}

Tasks:
1. Extract and aggregate related feature requests into 3-6 distinct Feature Clusters (e.g., Export capabilities, Dark mode, Mobile app, Multi-account support).
2. For each cluster, summarize the user requirement and determine Demand Level (High/Medium/Low).
3. Provide a Priority Score (0-100) and rationale considering customer reach and satisfaction potential.""",
        expected_output="""A list of structured feature opportunity clusters with demand levels, priority scores, and deduplicated user request examples.""",
        agent=agent,
    )
