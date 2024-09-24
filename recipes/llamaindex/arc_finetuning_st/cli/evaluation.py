import asyncio
from os import listdir
from pathlib import Path
from typing import Any, List, cast

from llama_index.core.async_utils import chunks
from llama_index.llms.openai import OpenAI

from arc_finetuning_st.workflows.arc_task_solver import (
    ARCTaskSolverWorkflow,
    WorkflowOutput,
)

DATA_PATH = Path(Path(__file__).parents[1].absolute(), "data", "evaluation")


async def batch_runner(
    workflow: ARCTaskSolverWorkflow,
    task_paths: List[Path],
    batch_size: int = 5,
    verbose: bool = False,
    sleep: int = 10,
    num_workers: int = 3,
) -> List[Any]:
    output: List[Any] = []
    sem = asyncio.Semaphore(num_workers)
    for task_chunk in chunks(task_paths, batch_size):
        task_chunk = (
            workflow.load_and_run_task(task_path=task_path, sem=sem)
            for task_path in task_chunk
            if task_path is not None
        )
        output_chunk = await asyncio.gather(*task_chunk)
        output.extend(output_chunk)
        if verbose:
            print(
                f"Completed {len(output)} out of {len(task_paths)} tasks",
                flush=True,
            )
        await asyncio.sleep(sleep)
    return output


async def main() -> None:
    task_paths = [DATA_PATH / t for t in listdir(DATA_PATH)]
    w = ARCTaskSolverWorkflow(
        timeout=None, verbose=False, llm=OpenAI("gpt-4o")
    )
    results = await batch_runner(w, task_paths[:10], verbose=True)
    results = cast(List[WorkflowOutput], results)
    num_solved = sum(el.passing for el in results)
    print(
        f"Solved: {num_solved}\nTotal Tasks:{len(results)}\nAverage Solve Rate: {float(num_solved) / len(results)}"
    )


if __name__ == "__main__":
    asyncio.run(main())
