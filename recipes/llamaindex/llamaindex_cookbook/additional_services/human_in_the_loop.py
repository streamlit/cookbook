import asyncio
import logging
import queue
from typing import Any, TypedDict

from llama_agents import HumanService, ServiceComponent
from llama_agents.message_queues.rabbitmq import RabbitMQMessageQueue

from llamaindex_cookbook.utils import load_from_env

logger = logging.getLogger("llamaindex_cookbook")
logging.basicConfig(level=logging.INFO)

message_queue_host = load_from_env("RABBITMQ_HOST")
message_queue_port = load_from_env("RABBITMQ_NODE_PORT")
message_queue_username = load_from_env("RABBITMQ_DEFAULT_USER")
message_queue_password = load_from_env("RABBITMQ_DEFAULT_PASS")
control_plane_host = load_from_env("CONTROL_PLANE_HOST")
control_plane_port = load_from_env("CONTROL_PLANE_PORT")
localhost = load_from_env("LOCALHOST")


class HumanRequest(TypedDict):
    prompt: str
    task_id: str


# # human in the loop function
human_input_request_queue: queue.Queue[HumanRequest] = queue.Queue()
human_input_result_queue: queue.Queue[str] = queue.Queue()


async def human_input_fn(prompt: str, task_id: str, **kwargs: Any) -> str:
    logger.info("human input fn invoked.")
    human_input_request_queue.put({"prompt": prompt, "task_id": task_id})
    logger.info("placed new prompt in queue.")

    # poll until human answer is stored
    async def _poll_for_human_input_result() -> str:
        human_input = None
        while human_input is None:
            try:
                human_input = human_input_result_queue.get_nowait()
            except queue.Empty:
                human_input = None
            await asyncio.sleep(0.1)
        logger.info("human input recieved")
        return human_input

    try:
        human_input = await asyncio.wait_for(
            _poll_for_human_input_result(),
            timeout=6000,
        )
        logger.info(f"Recieved human input: {human_input}")
    except (
        asyncio.exceptions.TimeoutError,
        asyncio.TimeoutError,
        TimeoutError,
    ):
        logger.info(f"Timeout reached for tool_call with prompt {prompt}")
        human_input = "Something went wrong."

    return human_input


# create our multi-agent framework components
message_queue = RabbitMQMessageQueue(
    url=f"amqp://{message_queue_username}:{message_queue_password}@{message_queue_host}:{message_queue_port}/"
)
human_service = HumanService(
    message_queue=message_queue,
    description="For human input.",
    fn_input=human_input_fn,
    human_input_prompt="{input_str}",
)
human_component = ServiceComponent.from_service_definition(human_service)
