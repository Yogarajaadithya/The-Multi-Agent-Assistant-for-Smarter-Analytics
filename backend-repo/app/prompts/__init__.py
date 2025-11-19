"""
Prompts Module for Multi-Agent HR Analytics System
===================================================
Centralized prompt management for all agents.
"""

from .prompts import (
    planner_agent_prompt,
    text_to_sql_agent_prompt,
    visualization_agent_prompt,
    hypothesis_agent_prompt,
    stats_agent_prompt,
)

__all__ = [
    "planner_agent_prompt",
    "text_to_sql_agent_prompt",
    "visualization_agent_prompt",
    "hypothesis_agent_prompt",
    "stats_agent_prompt",
]
