import uuid
from typing import List, Optional

from llama_index.core.bridge.pydantic import BaseModel, Field


class Prediction(BaseModel):
    """Prediction data class for LLM structured predict."""

    rationale: str = Field(
        description="Brief description of pattern and why prediction was made. Limit to 250 words."
    )
    prediction: str = Field(
        description="Predicted grid as a single string. e.g. '0,0,1\n1,1,1\n0,0,0'"
    )

    def __str__(self) -> str:
        return self.prediction

    @staticmethod
    def prediction_str_to_int_array(prediction: str) -> List[List[int]]:
        return [
            [int(a) for a in el.split(",")] for el in prediction.split("\n")
        ]


class Critique(BaseModel):
    """Critique data class for LLM structured predict."""

    critique: str = Field(
        description="Brief critique of the previous prediction and rationale. Limit to 250 words."
    )

    def __str__(self) -> str:
        return self.critique


class Attempt(BaseModel):
    """Container class of a single solution attempt."""

    id_: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prediction: Prediction
    critique: Optional[Critique] = Field(default=None)
    passing: bool = Field(default=False)
