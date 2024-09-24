import json
from pathlib import Path
from typing import Annotated, Any, Callable, List

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.bridge.pydantic import BaseModel, Field, WrapSerializer

from arc_finetuning_st.finetuning.templates import (
    ASSISTANT_TEMPLATE,
    SYSTEM_MESSAGE,
    USER_CRITIQUE_TEMPLATE,
    USER_TASK_TEMPLATE,
)
from arc_finetuning_st.workflows.models import Attempt


def remove_additional_kwargs(value: Any, handler: Callable, info: Any) -> Any:
    partial_result = handler(value, info)
    del partial_result["additional_kwargs"]
    return partial_result


class FineTuningExample(BaseModel):
    messages: List[
        Annotated[ChatMessage, WrapSerializer(remove_additional_kwargs)]
    ]
    task_name: str = Field(exclude=True)

    @classmethod
    def from_attempts(
        cls,
        task_name: str,
        examples: str,
        test_input: str,
        attempts: List[Attempt],
        system_message: str = SYSTEM_MESSAGE,
        user_task_template: str = USER_TASK_TEMPLATE,
        user_critique_template: str = USER_CRITIQUE_TEMPLATE,
        assistant_template: str = ASSISTANT_TEMPLATE,
    ) -> "FineTuningExample":
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_message),
            ChatMessage(
                role=MessageRole.USER,
                content=user_task_template.format(
                    examples=examples, test_input=test_input
                ),
            ),
        ]
        for a in attempts:
            messages.extend(
                [
                    ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=assistant_template.format(
                            predicted_output=str(a.prediction),
                            rationale=a.prediction.rationale,
                        ),
                    ),
                    ChatMessage(
                        role=MessageRole.USER,
                        content=user_critique_template.format(
                            critique=str(a.critique)
                        ),
                    ),
                ]
            )

        # always end with an asst message or else openai finetuning job will failt
        if a.critique == "This predicted output is correct.":
            final_asst_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Glad, we were able to solve the puzzle!",
            )
        else:
            final_asst_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Thanks for the feedback. I'll incorporate this into my next prediction.",
            )

        messages.append(final_asst_message)
        return cls(messages=messages, task_name=task_name)

    def to_json(self) -> str:
        data = self.model_dump()
        return json.dumps(data, indent=4)

    def write_json(self, dirpath: Path) -> None:
        data = self.model_dump()
        with open(Path(dirpath, self.task_name), "w") as f:
            json.dump(data, f)
