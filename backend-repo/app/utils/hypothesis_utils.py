"""
Hypothesis Agent Utility Functions
===================================
Helper functions for parsing and processing hypothesis generation responses.

Author: Yogarajaadithya
Date: November 19, 2025
"""

import json
import re
from typing import Dict, Any


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling markdown code blocks.
    
    Extracts JSON from markdown code blocks (```json or ```) and removes
    thinking tags before parsing. Handles common LLM response formats.
    
    Args:
        response (str): Raw LLM response text
    
    Returns:
        dict: Parsed JSON object
    
    Raises:
        ValueError: If JSON parsing fails
    
    Example:
        >>> response = "```json\\n{\"hypotheses\": [...]}\\n```"
        >>> data = parse_json_response(response)
        >>> print(data['hypotheses'])
    """
    # Try to extract from ```json ... ``` blocks
    json_block = re.search(r"```json\s*(.*?)```", response, re.IGNORECASE | re.DOTALL)
    if json_block:
        json_str = json_block.group(1)
    else:
        # Try generic ``` ... ``` blocks
        code_block = re.search(r"```\s*(.*?)```", response, re.DOTALL)
        json_str = code_block.group(1) if code_block else response
    
    # Remove thinking tags if present
    json_str = re.sub(r'<think>.*?</think>', '', json_str, flags=re.DOTALL | re.IGNORECASE)
    
    # Parse JSON
    try:
        return json.loads(json_str.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\n\nResponse: {response}")
