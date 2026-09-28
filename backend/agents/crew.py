"""
Milestone 2 CrewAI Orchestrator: PM Copilot Multi-Agent Insights Crew.
Orchestrates 3 specialized agents:
1. Theme & Pain Point Agent
2. Feature Request Agent
3. Trend Analysis Agent
"""

import os
import logging
from typing import List, Dict, Any, Optional
from crewai import Crew, Process, LLM
from config import settings

from agents.theme_agent import create_theme_and_pain_point_agent, create_theme_task, create_pain_point_task
from agents.feature_agent import create_feature_request_agent, create_feature_clustering_task
from agents.trend_agent import create_trend_analysis_agent, create_trend_task

from services.theme_extraction import extract_themes_from_feedback, extract_pain_points_from_feedback
from services.clustering import cluster_feature_requests
from services.trend_analysis import generate_trend_analysis, calculate_health_score

logger = logging.getLogger(__name__)


def get_crew_llm():
    """Create configured Groq LLM instance for CrewAI agents."""
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        # Use Groq LLM through CrewAI's native LLM wrapper
        return LLM(
            model="groq/llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0.2,
        )
    except Exception as e:
        logger.warning(f"Could not initialize CrewAI LLM: {e}")
        return None


def format_feedback_context(feedback_items: List[Dict[str, Any]], max_items: int = 40) -> str:
    """Format raw feedback records into concise markdown for agent context."""
    sampled = feedback_items[:max_items]
    lines = []
    for i, item in enumerate(sampled, 1):
        cat = item.get("category") or "general_feedback"
        sent = item.get("sentiment") or "neutral"
        rating = item.get("rating")
        rating_str = f", {rating}★" if rating else ""
        title = item.get("title") or ""
        content = item.get("content") or ""
        text = f"{title}: {content}".strip() if title else content
        lines.append(f"{i}. [{cat} | {sent}{rating_str}] {text[:180]}")
    return "\n".join(lines)


def run_milestone2_crew(
    feedback_records: List[Dict[str, Any]],
    workspace_name: str = "Product Workspace"
) -> Dict[str, Any]:
    """
    Execute the Milestone 2 CrewAI multi-agent pipeline.
    Runs Theme Agent, Feature Request Agent, and Trend Agent in sequence.
    Blends agent qualitative intelligence with deterministic statistical models.
    """
    # 1. Run baseline deterministic NLP & metrics
    themes = extract_themes_from_feedback(feedback_records)
    pain_points = extract_pain_points_from_feedback(feedback_records)
    clusters = cluster_feature_requests(feedback_records)
    trends = generate_trend_analysis(feedback_records)
    health_score = calculate_health_score(feedback_records)

    # 2. Check if CrewAI LLM is available
    llm = get_crew_llm()
    crew_output_text = None
    crew_executed = False

    if llm and len(feedback_records) > 0:
        try:
            feedback_summary = format_feedback_context(feedback_records, max_items=35)

            # Instantiate the 3 Milestone 2 Agents
            theme_agent = create_theme_and_pain_point_agent(llm)
            feature_agent = create_feature_request_agent(llm)
            trend_agent = create_trend_analysis_agent(llm)

            # Instantiate Tasks
            t_theme = create_theme_task(theme_agent, feedback_summary, workspace_name)
            t_pain = create_pain_point_task(theme_agent, feedback_summary, workspace_name)
            t_feature = create_feature_clustering_task(feature_agent, feedback_summary, workspace_name)
            t_trend = create_trend_task(trend_agent, feedback_summary, workspace_name)

            # Form Crew and execute sequential multi-agent workflow
            crew = Crew(
                agents=[theme_agent, feature_agent, trend_agent],
                tasks=[t_theme, t_pain, t_feature, t_trend],
                process=Process.sequential,
                verbose=False,
            )

            # Check if there is an active event loop and use appropriate execution
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    result = executor.submit(crew.kickoff).result()
            else:
                result = crew.kickoff()

            crew_output_text = str(result)
            crew_executed = True
            logger.info("CrewAI Milestone 2 multi-agent analysis completed successfully.")
        except Exception as e:
            logger.warning(f"CrewAI execution warning: {e}. Falling back to heuristic insights.")

    return {
        "themes": themes,
        "pain_points": pain_points,
        "feature_clusters": clusters,
        "trends": trends,
        "health_score": health_score,
        "crew_executed": crew_executed,
        "crew_output": crew_output_text,
        "agents": [
            "Theme & Pain Point Analyst",
            "Feature Request Strategist",
            "Trend & Sentiment Analyst",
        ],
    }
