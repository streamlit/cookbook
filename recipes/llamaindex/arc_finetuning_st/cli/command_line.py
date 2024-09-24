import argparse
import asyncio
import json
from os import listdir
from pathlib import Path
from typing import Any, List, Optional, cast

from llama_index.llms.openai import OpenAI

from arc_finetuning_st.cli.evaluation import batch_runner
from arc_finetuning_st.cli.finetune import (
    FINETUNE_JOBS_FILENAME,
    check_job_status,
    prepare_finetuning_jsonl_file,
    submit_finetune_job,
)
from arc_finetuning_st.workflows.arc_task_solver import (
    ARCTaskSolverWorkflow,
    WorkflowOutput,
)

SINGLE_EXAMPLE_JSON_PATH = Path(
    Path(__file__).parents[2].absolute(), "finetuning_examples"
)
FINETUNING_ASSETS_PATH = Path(
    Path(__file__).parents[2].absolute(), "finetuning_assets"
)


def handle_evaluate(
    llm: str,
    batch_size: int,
    num_workers: int,
    verbose: bool,
    sleep: int,
    **kwargs: Any,
) -> None:
    data_path = Path(
        Path(__file__).parents[2].absolute(), "data", "evaluation"
    )
    task_paths = [data_path / t for t in listdir(data_path)]
    llm = OpenAI(llm)
    w = ARCTaskSolverWorkflow(llm=llm, timeout=None)
    results = asyncio.run(
        batch_runner(
            w,
            task_paths[:10],
            verbose=verbose,
            batch_size=batch_size,
            num_workers=num_workers,
            sleep=sleep,
        )
    )
    results = cast(List[WorkflowOutput], results)
    num_solved = sum(el.passing for el in results)
    print(
        f"Solved: {num_solved}\nTotal Tasks:{len(results)}\nAverage Solve Rate: {float(num_solved) / len(results)}"
    )


def handle_finetune_job_submit(
    llm: str,
    start_job_id: Optional[str],
    continue_latest: bool = False,
    **kwargs: Any,
) -> None:
    prepare_finetuning_jsonl_file(
        json_path=SINGLE_EXAMPLE_JSON_PATH, assets_path=FINETUNING_ASSETS_PATH
    )
    if continue_latest:
        try:
            with open(FINETUNING_ASSETS_PATH / FINETUNE_JOBS_FILENAME) as f:
                lines = f.read().splitlines()
                metadata_str = lines[-1]
                metadata = json.loads(metadata_str)
                start_job_id = metadata["start_job_id"]
                llm = metadata["model"]
        except FileNotFoundError:
            # no previous finetune model
            raise ValueError(
                "Missing `finetuning_jobs.jsonl` file. Have you submitted a prior job?"
            )

    submit_finetune_job(
        llm=llm,
        start_job_id=start_job_id,
        assets_path=FINETUNING_ASSETS_PATH,
    )


def handle_check_finetune_job(
    start_job_id: Optional[str],
    llm: Optional[str],
    latest: bool,
    **kwargs: Any,
) -> None:
    if latest:
        try:
            with open(FINETUNING_ASSETS_PATH / FINETUNE_JOBS_FILENAME) as f:
                lines = f.read().splitlines()
                metadata_str = lines[-1]
                metadata = json.loads(metadata_str)
                start_job_id = metadata["start_job_id"]
                llm = metadata["model"]
        except FileNotFoundError:
            raise ValueError(
                "No finetuning_jobs.json file exists. You likely haven't submitted a job yet."
            )
    if not latest and (start_job_id is None or llm is None):
        raise ValueError(
            "If not `use_latest` then must provide `start_job_id` and `llm`."
        )

    # make type checking happy
    if start_job_id and llm:
        check_job_status(
            start_job_id=start_job_id,
            llm=llm,
            assets_path=FINETUNING_ASSETS_PATH,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="arc-finetuning cli tool.")

    # Subparsers
    subparsers = parser.add_subparsers(
        title="commands", dest="command", required=True
    )

    # evaluate command
    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluation of ARC Task predictions with LLM and ARCTaskSolverWorkflow.",
    )
    evaluate_parser.add_argument(
        "-m",
        "--llm",
        type=str,
        default="gpt-4o",
        help="The OpenAI LLM model to use with the Workflow.",
    )
    evaluate_parser.add_argument("-b", "--batch-size", type=int, default=5)
    evaluate_parser.add_argument("-w", "--num-workers", type=int, default=3)
    evaluate_parser.add_argument(
        "-v", "--verbose", action=argparse.BooleanOptionalAction
    )
    evaluate_parser.add_argument("-s", "--sleep", type=int, default=10)
    evaluate_parser.set_defaults(
        func=lambda args: handle_evaluate(**vars(args))
    )

    # finetune command
    finetune_parser = subparsers.add_parser(
        "finetune", help="Finetune OpenAI LLM on ARC Task Solver examples."
    )
    finetune_parser.add_argument(
        "-m",
        "--llm",
        type=str,
        default="gpt-4o-2024-08-06",
        help="The OpenAI LLM model to finetune.",
    )
    finetune_parser.add_argument(
        "-j",
        "--start-job-id",
        type=str,
        default=None,
        help="Previously started job id, to continue finetuning.",
    )
    finetune_parser.add_argument(
        "--continue-latest", action=argparse.BooleanOptionalAction
    )
    finetune_parser.set_defaults(
        func=lambda args: handle_finetune_job_submit(**vars(args))
    )

    # job status command
    job_status_parser = subparsers.add_parser(
        "job-status", help="Check the status of finetuning job."
    )
    job_status_parser.add_argument(
        "-j",
        "--start-job-id",
        type=str,
        default=None,
        help="Previously started job id, to continue finetuning.",
    )
    job_status_parser.add_argument(
        "-m",
        "--llm",
        type=str,
        default="gpt-4o-2024-08-06",
        help="The OpenAI LLM model to finetune.",
    )
    job_status_parser.add_argument(
        "--latest",
        action=argparse.BooleanOptionalAction,
        help="If set, checks the status of the last submitted job.",
    )
    job_status_parser.set_defaults(
        func=lambda args: handle_check_finetune_job(**vars(args))
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the appropriate function based on the command
    args.func(args)


if __name__ == "__main__":
    main()
