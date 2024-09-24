import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.llms import LLM
from llama_index.core.workflow import (
    Context,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

from arc_finetuning_st.workflows.events import (
    EvaluationEvent,
    FormatTaskEvent,
    PredictionEvent,
)
from arc_finetuning_st.workflows.models import Attempt, Critique, Prediction
from arc_finetuning_st.workflows.prompts import (
    CORRECTION_PROMPT_TEMPLATE,
    PREDICTION_PROMPT_TEMPLATE,
    REFLECTION_PROMPT_TEMPLATE,
)

EXAMPLE_TEMPLATE = """===
EXAMPLE

INPUT:
{input}

OUTPUT:
{output}
"""

PAST_ATTEMPT_TEMPLATE = """◦◦◦
PAST ATTEMPT {past_attempt_number}

PREDICTED_OUTPUT:
{past_predicted_output}

CRITIQUE:
{past_critique}
"""


class WorkflowOutput(BaseModel):
    passing: bool
    attempts: List[Attempt]


class ARCTaskSolverWorkflow(Workflow):
    def __init__(self, llm: LLM, max_attempts: int = 3, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.llm = llm
        self._max_attempts = max_attempts

    def _format_past_attempt(self, attempt: Attempt, attempt_num: int) -> str:
        return PAST_ATTEMPT_TEMPLATE.format(
            past_attempt_number=attempt_num,
            past_predicted_output=str(attempt.prediction),
            past_critique=str(attempt.critique) if attempt.critique else "",
        )

    @step
    async def format_task(
        self, ctx: Context, ev: StartEvent
    ) -> FormatTaskEvent:
        ctx.write_event_to_stream(ev)

        def _format_row(row: List[int]) -> str:
            return ",".join(str(el) for el in row)

        def pretty_print_grid(grid: List[List[int]]) -> str:
            formatted_rows = [_format_row(row) for row in grid]
            return "\n".join(formatted_rows)

        def format_train_example(train_pair: Dict) -> str:
            return EXAMPLE_TEMPLATE.format(
                input=pretty_print_grid(train_pair["input"]),
                output=pretty_print_grid(train_pair["output"]),
            )

        task = ev.get("task", {})
        await ctx.set("task", task)

        # prepare prompt_vars
        attempts = await ctx.get("attempts", [])
        if attempts:
            # update past predictions
            prompt_vars = await ctx.get("prompt_vars")
            formatted_past_attempts = [
                self._format_past_attempt(a, ix + 1)
                for ix, a in enumerate(attempts)
            ]
            prompt_vars.update(
                past_attempts="\n".join(formatted_past_attempts)
            )
        else:
            examples = [format_train_example(t) for t in task["train"]]
            prompt_vars = {
                "test_input": pretty_print_grid(task["test"][0]["input"]),
                "examples": "\n".join(examples),
            }
            await ctx.set("prompt_vars", prompt_vars)

        return FormatTaskEvent()

    @step
    async def prediction(
        self, ctx: Context, ev: FormatTaskEvent
    ) -> PredictionEvent | StopEvent:
        ctx.write_event_to_stream(ev)
        attempts = await ctx.get("attempts", [])
        attempts = cast(List[Attempt], attempts)
        prompt_vars = await ctx.get("prompt_vars")

        if attempts:
            # generating a correction from last Workflow run
            correction: Prediction = await self.llm.astructured_predict(
                Prediction, CORRECTION_PROMPT_TEMPLATE, **prompt_vars
            )
            attempts.append(Attempt(prediction=correction))
        else:
            # starting a new correction with no previous Workflow runs
            pred: Prediction = await self.llm.astructured_predict(
                Prediction, PREDICTION_PROMPT_TEMPLATE, **prompt_vars
            )
            attempts = [Attempt(prediction=pred)]

        await ctx.set("attempts", attempts)
        return PredictionEvent()

    @step
    async def evaluation(
        self, ctx: Context, ev: PredictionEvent
    ) -> EvaluationEvent:
        ctx.write_event_to_stream(ev)
        task = await ctx.get("task")
        attempts: List[Attempt] = await ctx.get("attempts")
        latest_prediction = attempts[-1].prediction
        latest_prediction_as_array = Prediction.prediction_str_to_int_array(
            str(latest_prediction)
        )
        ground_truth = task["test"][0]["output"]

        return EvaluationEvent(
            passing=(latest_prediction_as_array == ground_truth)
        )

    @step
    async def reflection(self, ctx: Context, ev: EvaluationEvent) -> StopEvent:
        ctx.write_event_to_stream(ev)
        attempts = await ctx.get("attempts")
        attempts = cast(List[Attempt], attempts)
        latest_attempt = attempts[-1]

        # check if passing
        if not ev.passing:
            prompt_vars = await ctx.get("prompt_vars")
            formatted_past_attempts = [
                self._format_past_attempt(a, ix + 1)
                for ix, a in enumerate(attempts)
            ]
            prompt_vars.update(
                past_attempts="\n".join(formatted_past_attempts)
            )

            # generate critique
            critique: Critique = await self.llm.astructured_predict(
                Critique, REFLECTION_PROMPT_TEMPLATE, **prompt_vars
            )

            # update states
            latest_attempt.critique = critique
        else:
            latest_attempt.critique = "This predicted output is correct."

        latest_attempt.passing = ev.passing
        attempts[-1] = latest_attempt
        await ctx.set("attempts", attempts)

        result = WorkflowOutput(passing=ev.passing, attempts=attempts)
        return StopEvent(result=result)

    async def load_and_run_task(
        self,
        task_path: Path,
        ctx: Optional[Context] = None,
        sem: Optional[asyncio.Semaphore] = None,
    ) -> Any:
        """Convenience function for loading a task json and running it."""
        with open(task_path) as f:
            task = json.load(f)

        async def _run_workflow() -> Any:
            return await self.run(ctx=ctx, task=task)

        if sem:  # in case running in batch with other workflow runs
            await sem.acquire()
            try:
                res = await _run_workflow()
            finally:
                sem.release()
        else:
            res = await _run_workflow()

        return res


async def _test_workflow() -> None:
    import json
    from pathlib import Path

    from llama_index.llms.openai import OpenAI

    task_path = Path(
        Path(__file__).parents[2].absolute(), "data/training/0a938d79.json"
    )
    with open(task_path) as f:
        task = json.load(f)

    w = ARCTaskSolverWorkflow(
        timeout=None, verbose=False, llm=OpenAI("gpt-4o")
    )
    attempts = await w.run(task=task)

    print(attempts)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_test_workflow())
