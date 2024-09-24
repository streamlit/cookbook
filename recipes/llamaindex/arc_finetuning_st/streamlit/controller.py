import asyncio
import json
import logging
from os import listdir
from pathlib import Path
from typing import Any, List, Literal, Optional, cast

import pandas as pd
import plotly.express as px
import streamlit as st
from llama_index.core.workflow.handler import WorkflowHandler
from llama_index.llms.openai import OpenAI

from arc_finetuning_st.finetuning.finetuning_example import FineTuningExample
from arc_finetuning_st.workflows.arc_task_solver import (
    ARCTaskSolverWorkflow,
    WorkflowOutput,
)
from arc_finetuning_st.workflows.models import Attempt, Prediction

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self) -> None:
        self._handler: Optional[WorkflowHandler] = None
        self._attempts: List[Attempt] = []
        self._passing_results: List[bool] = []
        self._data_path = Path(
            Path(__file__).parents[2].absolute(), "data", "training"
        )
        self._finetuning_examples_path = Path(
            Path(__file__).parents[2].absolute(), "finetuning_examples"
        )
        self._finetuning_examples_path.mkdir(exist_ok=True, parents=True)

    def reset(self) -> None:
        # clear prediction
        st.session_state.prediction = None
        st.session_state.disable_continue_button = True
        st.session_state.disable_abort_button = True
        st.session_state.disable_preview_button = True
        st.session_state.disable_start_button = False
        st.session_state.critique = None
        st.session_state.metric_value = "N/A"

        self._handler = None
        self._attempts = []
        self._passing_results = []

    def selectbox_selection_change_handler(self) -> None:
        # only reset states
        # loading of task is delegated to relevant calls made with each
        # streamlit element
        self.reset()

    @staticmethod
    def plot_grid(
        grid: List[List[int]],
        kind: Literal["input", "output", "prediction", "latest prediction"],
    ) -> Any:
        m = len(grid)
        n = len(grid[0])
        fig = px.imshow(
            grid,
            text_auto=True,
            labels={"x": f"{kind.title()}<br><sup>{m}x{n}</sup>"},
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(
            yaxis={"visible": False},
            xaxis={"visible": True, "showticklabels": False},
            margin=dict(
                l=20,
                r=20,
                b=20,
                t=20,
            ),
        )
        return fig

    async def show_progress_bar(self, handler: WorkflowHandler) -> None:
        progress_text_template = "{event} completed. Next step in progress."
        my_bar = st.progress(0, text="Workflow run in progress. Please wait.")
        num_steps = 5.0
        current_step = 1
        async for ev in handler.stream_events():
            my_bar.progress(
                current_step / num_steps,
                text=progress_text_template.format(event=type(ev).__name__),
            )
            current_step += 1
        my_bar.empty()

    def handle_abort_click(self) -> None:
        self.reset()

    async def handle_prediction_click(self) -> None:
        """Run workflow to generate prediction."""
        selected_task = st.session_state.selected_task
        if selected_task:
            task = self.load_task(selected_task)
            w = ARCTaskSolverWorkflow(
                timeout=None, verbose=False, llm=OpenAI("gpt-4o")
            )

            if not self._handler:  # start a new solver
                handler = w.run(task=task)

            else:  # continuing from past Workflow execution
                # need to reset this queue otherwise will use nested event loops
                self._handler.ctx._streaming_queue = asyncio.Queue()

                # use the critique and prediction str from streamlit
                critique = st.session_state.get("critique")
                self._attempts[-1].critique = critique
                await self._handler.ctx.set("attempts", self._attempts)

                # run Workflow
                handler = w.run(ctx=self._handler.ctx, task=task)

            # progress bar
            _ = asyncio.create_task(self.show_progress_bar(handler))

            res: WorkflowOutput = await handler

            handler = cast(WorkflowHandler, handler)
            self._handler = handler
            self._passing_results.append(res.passing)
            self._attempts = res.attempts

            # update streamlit states
            grid = Prediction.prediction_str_to_int_array(
                prediction=str(res.attempts[-1].prediction)
            )
            prediction_fig = Controller.plot_grid(
                grid, kind="latest prediction"
            )
            st.session_state.prediction = prediction_fig
            st.session_state.critique = str(res.attempts[-1].critique)
            st.session_state.disable_continue_button = False
            st.session_state.disable_abort_button = False
            st.session_state.disable_preview_button = False
            st.session_state.disable_start_button = True
            metric_value = "✅" if res.passing else "❌"
            st.session_state.metric_value = metric_value

    @property
    def saved_finetuning_examples(self) -> List[str]:
        return listdir(self._finetuning_examples_path)

    @property
    def task_file_names(self) -> List[str]:
        return listdir(self._data_path)

    def radio_format_task_name(self, selected_task: str) -> str:
        if selected_task in self.saved_finetuning_examples:
            return f"{selected_task} ✅"
        return selected_task

    def load_task(self, selected_task: str) -> Any:
        task_path = Path(self._data_path, selected_task)

        with open(task_path) as f:
            task = json.load(f)
        return task

    @property
    def passing(self) -> Optional[bool]:
        if self._passing_results:
            return self._passing_results[-1]
        return None

    @property
    def attempts_history_df(
        self,
    ) -> pd.DataFrame:
        if self._attempts:
            attempt_number_list: List[int] = []
            passings: List[str] = []
            rationales: List[str] = []
            critiques: List[str] = []
            predictions: List[str] = []
            for ix, a in enumerate(self._attempts):
                passings = ["✅" if a.passing else "❌"] + passings
                rationales = [a.prediction.rationale] + rationales
                predictions = [str(a.prediction)] + predictions
                critiques = [str(a.critique)] + critiques
                attempt_number_list = [ix + 1] + attempt_number_list
            return pd.DataFrame(
                {
                    "attempt #": attempt_number_list,
                    "passing": passings,
                    "rationale": rationales,
                    "critique": critiques,
                    # hidden from UI
                    "prediction": predictions,
                }
            )
        return pd.DataFrame(
            {
                "attempt #": [],
                "passing": [],
                "rationale": [],
                "critique": [],
                # hidden from UI
                "prediction": [],
            }
        )

    def handle_workflow_run_selection(self) -> None:
        @st.dialog("Past Attempt")
        def _display_attempt(
            fig: Any, rationale: str, critique: str, passing: bool
        ) -> None:
            st.plotly_chart(
                fig,
                use_container_width=True,
                key="prediction",
            )
            st.markdown(body=f"### Passing\n{passing}")
            st.markdown(body=f"### Rationale\n{rationale}")
            st.markdown(body=f"### Critique\n{critique}")

        selected_rows = (
            st.session_state.get("attempts_history_df")
            .get("selection")
            .get("rows")
        )

        if selected_rows:
            row_ix = selected_rows[0]
            df_row = self.attempts_history_df.iloc[row_ix]

            grid = Prediction.prediction_str_to_int_array(
                prediction=df_row["prediction"]
            )
            prediction_fig = Controller.plot_grid(grid, kind="prediction")

            _display_attempt(
                fig=prediction_fig,
                rationale=df_row["rationale"],
                critique=df_row["critique"],
                passing=df_row["passing"],
            )

    async def handle_finetuning_preview_click(self) -> None:
        if self._handler:
            st.session_state.show_finetuning_preview_dialog = True
            prompt_vars = await self._handler.ctx.get("prompt_vars")

            @st.dialog("Finetuning Example", width="large")
            def _display_finetuning_example() -> None:
                nonlocal prompt_vars

                finetuning_example = FineTuningExample.from_attempts(
                    task_name=st.session_state.selected_task,
                    attempts=self._attempts,
                    examples=prompt_vars["examples"],
                    test_input=prompt_vars["test_input"],
                )

                with st.container(height=500, border=False):
                    save_col, close_col = st.columns([1, 1])
                    with save_col:
                        if st.button("Save", use_container_width=True):
                            finetuning_example.write_json(
                                self._finetuning_examples_path,
                            )
                            st.session_state.show_finetuning_preview_dialog = (
                                False
                            )
                            st.rerun()
                    with close_col:
                        if st.button("Close", use_container_width=True):
                            st.session_state.show_finetuning_preview_dialog = (
                                False
                            )
                            st.rerun()

                    st.code(
                        finetuning_example.to_json(),
                        language="json",
                        wrap_lines=True,
                    )

            if st.session_state.show_finetuning_preview_dialog:
                _display_finetuning_example()
