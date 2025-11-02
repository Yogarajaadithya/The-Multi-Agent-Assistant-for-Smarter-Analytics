"""Test what the Pydantic parser format instructions look like."""

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Literal

class BivariateHypothesis(BaseModel):
    """Single bivariate hypothesis with all required fields."""
    
    hypothesis_id: int = Field(description="Unique identifier for the hypothesis (1, 2, 3, ...)")
    null_hypothesis: str = Field(description="The null hypothesis (H0) stating no relationship or effect exists")
    alternative_hypothesis: str = Field(description="The alternative hypothesis (H1) stating the expected relationship or effect")
    variable_1: str = Field(description="First variable name (must exist in data dictionary)")
    variable_2: str = Field(description="Second variable name (must exist in data dictionary)")
    variable_1_type: Literal["categorical", "numerical"] = Field(description="Data type of variable 1")
    variable_2_type: Literal["categorical", "numerical"] = Field(description="Data type of variable 2")
    recommended_test: str = Field(description="Statistical test to use (e.g., 't-test', 'chi-square', 'ANOVA', 'correlation')")
    rationale: str = Field(description="Brief explanation of why this hypothesis is relevant to the user's question")


class HypothesisList(BaseModel):
    """List of bivariate hypotheses."""
    hypotheses: List[BivariateHypothesis] = Field(description="List of generated bivariate hypotheses")


parser = PydanticOutputParser(pydantic_object=HypothesisList)
format_instructions = parser.get_format_instructions()

print("="*70)
print("FORMAT INSTRUCTIONS FROM PYDANTIC PARSER:")
print("="*70)
print(format_instructions)
print("="*70)
print(f"\nLength: {len(format_instructions)} characters")
print(f"Contains '{{': {'{' in format_instructions}")
print(f"Contains '}}': {'}' in format_instructions}")
