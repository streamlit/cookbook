import json
from os import listdir
from pathlib import Path
from typing import Optional

from llama_index.finetuning import OpenAIFinetuneEngine

SINGLE_EXAMPLE_JSON_PATH = Path(
    Path(__file__).parents[1].absolute(), "finetuning_examples"
)

FINETUNING_ASSETS_PATH = Path(
    Path(__file__).parents[1].absolute(), "finetuning_assets"
)

FINETUNE_JSONL_FILENAME = "finetuning.jsonl"
FINETUNE_JOBS_FILENAME = "finetuning_jobs.jsonl"


def prepare_finetuning_jsonl_file(
    json_path: Path = SINGLE_EXAMPLE_JSON_PATH,
    assets_path: Path = FINETUNING_ASSETS_PATH,
) -> None:
    """Read all json files from data path and write a jsonl file."""
    with open(assets_path / FINETUNE_JSONL_FILENAME, "w") as jsonl_out:
        for json_name in listdir(json_path):
            with open(json_path / json_name) as f:
                for line in f:
                    jsonl_out.write(line)
                    jsonl_out.write("\n")


def submit_finetune_job(
    llm: str = "gpt-4o-2024-08-06",
    start_job_id: Optional[str] = None,
    assets_path: Path = FINETUNING_ASSETS_PATH,
) -> None:
    """Submit finetuning job."""
    finetune_engine = OpenAIFinetuneEngine(
        llm,
        (assets_path / FINETUNE_JSONL_FILENAME).as_posix(),
        start_job_id=start_job_id,
        validate_json=False,
    )
    finetune_engine.finetune()

    with open(assets_path / FINETUNE_JOBS_FILENAME, "a+") as f:
        metadata = {
            "model": llm,
            "start_job_id": finetune_engine._start_job.id,
        }
        json.dump(metadata, f)
        f.write("\n")

    print(finetune_engine.get_current_job())


def check_job_status(
    start_job_id: str,
    llm: str = "gpt-4o-2024-08-06",
    assets_path: Path = FINETUNING_ASSETS_PATH,
) -> None:
    """Check on status of most recent submitted finetuning job."""

    finetune_engine = OpenAIFinetuneEngine(
        llm,
        (assets_path / FINETUNE_JSONL_FILENAME).as_posix(),
        start_job_id=start_job_id,
        validate_json=False,
    )

    print(finetune_engine.get_current_job())
