import asyncio
import json
import logging
import queue
import threading
import time
from typing import Optional, Tuple

import pandas as pd
import streamlit as st
from llama_agents.types import TaskResult
from llama_index.llms.openai import OpenAI

from llamaindex_cookbook.additional_services.human_in_the_loop import (
    HumanRequest,
    HumanService,
)
from llamaindex_cookbook.agent_services.financial_and_economic_essentials.time_series_getter_agent import (
    perform_price_aggregation,
)
from llamaindex_cookbook.agent_services.government_essentials.stats_fulfiller_agent import (
    perform_date_value_aggregation,
)
from llamaindex_cookbook.apps.controller import Controller
from llamaindex_cookbook.apps.final_task_consumer import FinalTaskConsumer

logger = logging.getLogger(__name__)

llm = OpenAI(model="gpt-4o-mini")
control_plane_host = "0.0.0.0"
control_plane_port = 8001


st.set_page_config(layout="wide")


@st.cache_resource
def startup() -> (
    Tuple[
        Controller,
        queue.Queue[TaskResult],
        FinalTaskConsumer,
        queue.Queue[HumanRequest],
        queue.Queue[str],
    ]
):
    from llamaindex_cookbook.additional_services.human_in_the_loop import (
        human_input_request_queue,
        human_input_result_queue,
        human_service,
        message_queue,
    )

    controller = Controller(
        control_plane_host=control_plane_host,
        control_plane_port=control_plane_port,
    )

    async def start_consuming_human_tasks(hs: HumanService) -> None:
        # register to control plane
        await hs.register_to_control_plane(
            control_plane_url=(
                f"http://{control_plane_host}:{control_plane_port}"
                if control_plane_port
                else f"http://{control_plane_host}"
            )
        )

        consuming_callable = await message_queue.register_consumer(
            hs.as_consumer()
        )

        ht_task = asyncio.create_task(consuming_callable())  # noqa: F841

        pl_task = asyncio.create_task(hs.processing_loop())  # noqa: F841

        await asyncio.Future()

    hr_thread = threading.Thread(
        name="Human Request thread",
        target=asyncio.run,
        args=(start_consuming_human_tasks(human_service),),
        daemon=False,
    )
    hr_thread.start()

    completed_tasks_queue: queue.Queue[TaskResult] = queue.Queue()
    final_task_consumer = FinalTaskConsumer(
        message_queue=message_queue,
        completed_tasks_queue=completed_tasks_queue,
    )

    async def start_consuming_finalized_tasks(
        final_task_consumer: FinalTaskConsumer,
    ) -> None:
        final_task_consuming_callable = (
            await final_task_consumer.register_to_message_queue()
        )

        await final_task_consuming_callable()

    # server thread will remain active as long as streamlit thread is running, or is manually shutdown
    ft_thread = threading.Thread(
        name="Consuming thread",
        target=asyncio.run,
        args=(start_consuming_finalized_tasks(final_task_consumer),),
        daemon=False,
    )
    ft_thread.start()

    time.sleep(5)
    logger.info("Started consuming.")

    return (
        controller,
        completed_tasks_queue,
        final_task_consumer,
        human_input_request_queue,
        human_input_result_queue,
    )


(
    controller,
    completed_tasks_queue,
    final_task_consumer,
    human_input_request_queue,
    human_input_result_queue,
) = startup()


### App
logo = '[<img src="https://d3ddy8balm3goa.cloudfront.net/llamaindex/LlamaLogoSquare.png" width="28" height="28" />](https://github.com/run-llama/llama-agents "Check out the llama-agents Github repo!")'
st.title("Human In The Loop With LlamaAgents")
st.markdown(f"_Powered by LlamaIndex_ &nbsp; {logo}", unsafe_allow_html=True)


# state management
if "submitted_tasks" not in st.session_state:
    st.session_state["submitted_tasks"] = []
if "human_required_tasks" not in st.session_state:
    st.session_state["human_required_tasks"] = []
if "completed_tasks" not in st.session_state:
    st.session_state["completed_tasks"] = []
if "tasks" not in st.session_state:
    st.session_state["tasks"] = []
if "consuming" not in st.session_state:
    st.session_state.consuming = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task" not in st.session_state:
    st.session_state.current_task = None
if "human_input" not in st.session_state:
    st.session_state.human_input = ""


left, right = st.columns([1, 2], vertical_alignment="top")

with left:
    task_input = st.text_input(
        "Task input",
        placeholder="Enter a task input.",
        key="task_input",
        on_change=controller.handle_task_submission,
    )


@st.fragment(run_every="5s")
def task_df() -> None:
    st.text("Task Status")
    st.button("Refresh")
    tasks = (
        [t.input for t in st.session_state.submitted_tasks]
        + [t.input for t in st.session_state.human_required_tasks]
        + [t.input for t in st.session_state.completed_tasks]
    )

    task_ids = (
        [t.task_id for t in st.session_state.submitted_tasks]
        + [t.task_id for t in st.session_state.human_required_tasks]
        + [t.task_id for t in st.session_state.completed_tasks]
    )

    status = (
        ["submitted"] * len(st.session_state.submitted_tasks)
        + ["human_required"] * len(st.session_state.human_required_tasks)
        + ["completed"] * len(st.session_state.completed_tasks)
    )

    data = {
        "task_id": task_ids,
        "input": tasks,
        "status": status,
    }

    logger.info(f"data: {data}")
    df = pd.DataFrame(data)
    event = st.dataframe(
        df,
        hide_index=True,
        selection_mode="single-row",
        use_container_width=True,
        on_select=controller.get_task_selection_handler(df),
        key="task_df",
    )

    popover_enabled = (
        len(event.selection["rows"]) > 0
        and st.session_state.current_task.status == "human_required"
    )
    with st.popover("Human Input", disabled=not popover_enabled):
        if popover_enabled:
            human_prompt = st.session_state.current_task.history[-1].content
            st.markdown(human_prompt)
            st.text_input(
                "Provide human input",
                key="human_input",
                on_change=controller.get_human_input_handler(
                    human_input_result_queue
                ),
            )

    show_task_res = (
        len(event.selection["rows"]) > 0
        and st.session_state.current_task.status == "completed"
    )

    task_res_container = st.container(height=500)
    if show_task_res:
        if task_res := controller.get_task_result(
            st.session_state.current_task.task_id
        ):
            task_type = controller.infer_task_type(task_res)

            timeseries_data = None
            value_key: str = ""
            object_key: str = ""
            color: str = ""
            if task_type == "timeseries-good":
                try:
                    timeseries_data = perform_price_aggregation(
                        task_res.result
                    )
                    value_key = "price"
                    object_key = "good"
                    color = "#FF91AF"
                except json.JSONDecodeError:
                    logger.info("Could not decode task_res")
                    pass
            elif task_type == "timeseries-city-stat":
                try:
                    timeseries_data = perform_date_value_aggregation(
                        task_res.result
                    )
                    value_key = "value"
                    object_key = "variable"
                    color = "#73CED0"
                except json.JSONDecodeError:
                    logger.info("Could not decode task_res")
                    pass

            with task_res_container:
                if timeseries_data:
                    title = timeseries_data[0][object_key]
                    chart_data = {
                        "dates": [el["date"] for el in timeseries_data],
                        value_key: [el[value_key] for el in timeseries_data],
                    }
                    st.header(title)
                    st.bar_chart(
                        data=chart_data,
                        x="dates",
                        y=value_key,
                        height=400,
                        color=color,
                    )
                else:
                    st.write(task_res.result)


task_df()


@st.fragment(run_every=5)
def process_completed_tasks(completed_queue: queue.Queue) -> None:
    task_res: Optional[TaskResult] = None
    try:
        task_res = completed_queue.get_nowait()
        logger.info("got new task result")
    except queue.Empty:
        logger.info("task result queue is empty.")

    if task_res:
        controller.update_associated_task_to_completed_status(
            task_res=task_res
        )


process_completed_tasks(completed_queue=completed_tasks_queue)


@st.fragment(run_every=5)
def process_human_input_requests(
    human_requests_queue: queue.Queue[HumanRequest],
) -> None:
    human_req: Optional[HumanRequest] = None
    try:
        human_req = human_requests_queue.get_nowait()
        logger.info("got new human request")
    except queue.Empty:
        logger.info("human request queue is empty.")

    if human_req:
        controller.update_associated_task_to_human_required_status(
            human_req=human_req
        )


process_human_input_requests(human_requests_queue=human_input_request_queue)
