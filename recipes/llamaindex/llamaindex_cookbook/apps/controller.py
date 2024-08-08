import json
import logging
import queue
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generator, List, Optional

import pandas as pd
import streamlit as st
from llama_agents import LlamaAgentsClient
from llama_agents.types import TaskResult
from llama_index.core.llms import ChatMessage, ChatResponseGen

from llamaindex_cookbook.additional_services.human_in_the_loop import (
    HumanRequest,
)

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    HUMAN_REQUIRED = "human_required"
    COMPLETED = "completed"
    SUBMITTED = "submitted"


@dataclass
class TaskModel:
    task_id: str
    input: str
    status: TaskStatus
    prompt: Optional[str] = None
    history: List[ChatMessage] = field(default_factory=list)


class Controller:
    def __init__(
        self,
        control_plane_host: str = "127.0.0.1",
        control_plane_port: Optional[int] = 8000,
    ):
        self._client = LlamaAgentsClient(
            control_plane_url=(
                f"http://{control_plane_host}:{control_plane_port}"
                if control_plane_port
                else f"http://{control_plane_host}"
            )
        )
        self._step_interval = 0.5
        self._timeout = 60

    def llama_index_stream_wrapper(
        self,
        llama_index_stream: ChatResponseGen,
    ) -> Generator[str, Any, Any]:
        for chunk in llama_index_stream:
            yield chunk.delta

    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        return self._client.get_task_result(task_id=task_id)

    def handle_task_submission(self) -> None:
        """Handle the user submitted message. Clear task submission box, and
        add the new task to the submitted list.
        """

        # create new task and store in state
        task_input = st.session_state.task_input
        if task_input == "":
            return
        task_id = self._client.create_task(task_input)
        task = TaskModel(
            task_id=task_id,
            input=task_input,
            history=[
                ChatMessage(role="user", content=task_input),
            ],
            status=TaskStatus.SUBMITTED,
        )
        st.session_state.submitted_tasks.append(task)
        logger.info("Added task to submitted queue")
        st.session_state.current_task = task
        st.session_state.task_input = ""

    def get_human_input_handler(
        self, human_input_result_queue: queue.Queue
    ) -> Callable:
        def human_input_handler() -> None:
            human_input = st.session_state.human_input
            if human_input == "":
                return
            human_input_result_queue.put_nowait(human_input)
            logger.info("pushed human input to human input result queue.")

        return human_input_handler

    def update_associated_task_to_completed_status(
        self,
        task_res: TaskResult,
    ) -> None:
        """
        Update task status to completed for received task result.

        Update session_state lists as well.
        """

        def remove_task_from_list(
            task_list: List[TaskModel],
        ) -> List[TaskModel]:
            try:
                ix, task = next(
                    (ix, t)
                    for ix, t in enumerate(task_list)
                    if t.task_id == task_res.task_id
                )
                task.status = TaskStatus.COMPLETED
                task.history.append(
                    ChatMessage(role="assistant", content=task_res.result)
                )
                del task_list[ix]
                st.session_state.completed_tasks.append(task)
                logger.info("updated submitted and completed tasks list.")
            except StopIteration:
                raise ValueError("Cannot find task in list of tasks.")
            return task_list

        submitted_tasks = st.session_state.get("submitted_tasks")
        human_required_tasks = st.session_state.get("human_required_tasks")

        if task_res.task_id in [t.task_id for t in submitted_tasks]:
            updated_task_list = remove_task_from_list(submitted_tasks)
            st.session_state.submitted_tasks = updated_task_list
        elif task_res.task_id in [t.task_id for t in human_required_tasks]:
            updated_task_list = remove_task_from_list(human_required_tasks)
            st.session_state.human_required_tasks = updated_task_list
        else:
            raise ValueError(
                "Completed task not in submitted or human_required lists."
            )

    def update_associated_task_to_human_required_status(
        self,
        human_req: HumanRequest,
    ) -> None:
        """
        Update task status to human_required for received task request.

        Update session_state lists as well.
        """
        try:
            task_list = st.session_state.get("submitted_tasks")
            print(f"submitted tasks: {task_list}")
            ix, task = next(
                (ix, t)
                for ix, t in enumerate(task_list)
                if t.task_id == human_req["task_id"]
            )
            task.status = TaskStatus.HUMAN_REQUIRED
            task.history.append(
                ChatMessage(role="assistant", content=human_req["prompt"])
            )
            del task_list[ix]
            st.session_state.submitted_tasks = task_list
            st.session_state.human_required_tasks.append(task)
            logger.info("updated submitted and human required tasks list.")
        except StopIteration:
            raise ValueError("Cannot find task in list of tasks.")

    def get_task_selection_handler(self, task_df: pd.DataFrame) -> Callable:
        def task_selection_handler() -> None:
            dataframe_selection_state = st.session_state.task_df["selection"][
                "rows"
            ]

            if not dataframe_selection_state:
                st.session_state.current_task = None
                return

            # display chat history in console
            selected_row = st.session_state.task_df["selection"]["rows"][0]
            selection = task_df.iloc[selected_row]
            task_status = selection["status"]
            task_id = selection["task_id"]
            if task_status == TaskStatus.COMPLETED:
                task_list = st.session_state.completed_tasks
            elif task_status == TaskStatus.HUMAN_REQUIRED:
                task_list = st.session_state.human_required_tasks
            else:
                task_list = st.session_state.submitted_tasks

            try:
                task = next(t for t in task_list if t.task_id == task_id)
                st.session_state.current_task = task
            except StopIteration:
                pass  # handle this better

        return task_selection_handler

    def infer_task_type(self, task_res: TaskResult) -> str:
        def try_parse_as_json(text: str) -> Any:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None

        if task_res_json := try_parse_as_json(task_res.result):
            if "good" in task_res_json[0]:
                return "timeseries-good"
            if "variable" in task_res_json[0]:
                return "timeseries-city-stat"

        return "text"
