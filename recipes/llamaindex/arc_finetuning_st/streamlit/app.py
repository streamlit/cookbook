from typing import Tuple

import streamlit as st
from llama_index.core.tools.function_tool import async_to_sync

from arc_finetuning_st.streamlit.controller import Controller

# startup
st.set_page_config(layout="wide")


@st.cache_resource
def startup() -> Tuple[Controller,]:
    controller = Controller()
    return (controller,)


(controller,) = startup()

# states
if "show_finetuning_preview_dialog" not in st.session_state:
    st.session_state["show_finetuning_preview_dialog"] = True
if "disable_continue_button" not in st.session_state:
    st.session_state["disable_continue_button"] = True
if "disable_start_button" not in st.session_state:
    st.session_state["disable_start_button"] = False
if "disable_abort_button" not in st.session_state:
    st.session_state["disable_abort_button"] = True
if "disable_preview_button" not in st.session_state:
    st.session_state["disable_preview_button"] = True
if "metric_value" not in st.session_state:
    st.session_state["metric_value"] = "N/A"

logo = '[<img src="https://d3ddy8balm3goa.cloudfront.net/llamaindex/LlamaLogoSmall.png" width="28" height="28" />](https://github.com/run-llama/llama-agents "Check out the llama-agents Github repo!")'
st.title("ARC Task Solver with Human Input")
st.markdown(
    f"{logo} &nbsp; _Powered with LlamaIndex Worfklows_",
    unsafe_allow_html=True,
)

# sidebar
with st.sidebar:
    task_selection = st.radio(
        label="Tasks",
        options=controller.task_file_names,
        index=0,
        on_change=controller.selectbox_selection_change_handler,
        key="selected_task",
        format_func=controller.radio_format_task_name,
    )

train_col, test_col = st.columns(
    [1, 1], vertical_alignment="top", gap="medium"
)

with train_col:
    st.subheader("Train Examples")
    with st.container():
        selected_task = st.session_state.selected_task
        if selected_task:
            task = controller.load_task(selected_task)
            num_examples = len(task["train"])
            tabs = st.tabs(
                [f"Example {ix}" for ix in range(1, num_examples + 1)]
            )
            for ix, tab in enumerate(tabs):
                with tab:
                    left, right = st.columns(
                        [1, 1], vertical_alignment="top", gap="medium"
                    )
                    with left:
                        ex = task["train"][ix]
                        grid = ex["input"]
                        fig = Controller.plot_grid(grid, kind="input")
                        st.plotly_chart(fig, use_container_width=True)

                    with right:
                        ex = task["train"][ix]
                        grid = ex["output"]
                        fig = Controller.plot_grid(grid, kind="output")
                        st.plotly_chart(fig, use_container_width=True)


with test_col:
    header_col, start_col, preview_col = st.columns(
        [4, 1, 2], vertical_alignment="bottom", gap="small"
    )
    with header_col:
        st.subheader("Test")
    with start_col:
        st.button(
            "start",
            on_click=async_to_sync(controller.handle_prediction_click),
            use_container_width=True,
            type="primary",
            disabled=st.session_state.get("disable_start_button"),
        )
    with preview_col:
        st.button(
            "fine-tuning example",
            on_click=async_to_sync(controller.handle_finetuning_preview_click),
            use_container_width=True,
            disabled=st.session_state.get("disable_preview_button"),
            key="preview_button",
        )

    with st.container():
        selected_task = st.session_state.selected_task
        if selected_task:
            task = controller.load_task(selected_task)
            num_cases = len(task["test"])
            tabs = st.tabs(
                [f"Test Case {ix}" for ix in range(1, num_cases + 1)]
            )
            for ix, tab in enumerate(tabs):
                with tab:
                    left, right = st.columns(
                        [1, 1], vertical_alignment="top", gap="medium"
                    )
                    with left:
                        ex = task["test"][ix]
                        grid = ex["input"]
                        fig = Controller.plot_grid(grid, kind="input")
                        st.plotly_chart(fig, use_container_width=True)

                    with right:
                        prediction_fig = st.session_state.get(
                            "prediction", None
                        )
                        if prediction_fig:
                            st.plotly_chart(
                                prediction_fig,
                                use_container_width=True,
                                key="prediction",
                            )

        # metrics and past attempts
        with st.container():
            metric_col, critique_col = st.columns(
                [1, 7], vertical_alignment="top"
            )
            with metric_col:
                metric_value = st.session_state.get("metric_value")
                st.markdown(body="Passing")
                st.markdown(body=f"# {metric_value}")

            with critique_col:
                st.markdown(body="Critique of Attempt")
                st.text_area(
                    label="This critique is passed to the LLM to generate a new prediction.",
                    key="critique",
                    help=(
                        "An LLM was prompted to critique the prediction on why it might not fit the pattern. "
                        "This critique is passed in the PROMPT in the next prediction attempt. "
                        "Feel free to make edits to the critique or use your own."
                    ),
                )

        with st.expander("Past Attempts"):
            st.dataframe(
                controller.attempts_history_df,
                hide_index=True,
                selection_mode="single-row",
                on_select=controller.handle_workflow_run_selection,
                column_order=(
                    "attempt #",
                    "passing",
                    "critique",
                    "rationale",
                ),
                key="attempts_history_df",
                use_container_width=True,
            )

        with st.container():
            continue_col, abort_col = st.columns([3, 1])
            with continue_col:
                st.button(
                    "continue",
                    on_click=async_to_sync(controller.handle_prediction_click),
                    use_container_width=True,
                    disabled=st.session_state.get("disable_continue_button"),
                    key="continue_button",
                    type="primary",
                )

            with abort_col:

                @st.dialog("Are you sure you want to abort the session?")
                def abort_solving() -> None:
                    st.write(
                        "Confirm that you want to abort the session by clicking 'confirm' button below."
                    )
                    if st.button("Confirm"):
                        controller.reset()
                        st.rerun()

                st.button(
                    "abort",
                    on_click=abort_solving,
                    use_container_width=True,
                    disabled=st.session_state.get("disable_abort_button"),
                )
