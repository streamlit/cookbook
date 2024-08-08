import logging
import queue
from typing import Any

from llama_agents import CallableMessageConsumer, QueueMessage
from llama_agents.message_consumers.base import (
    BaseMessageQueueConsumer,
    StartConsumingCallable,
)
from llama_agents.message_queues.base import BaseMessageQueue
from llama_agents.types import ActionTypes, TaskResult

logger = logging.getLogger(__name__)


class FinalTaskConsumer:
    def __init__(
        self,
        message_queue: BaseMessageQueue,
        completed_tasks_queue: queue.Queue,
    ):
        self.message_queue = message_queue
        self.completed_tasks_queue = completed_tasks_queue
        self.name: str = "human"

    async def _process_completed_task_messages(
        self, message: QueueMessage, **kwargs: Any
    ) -> None:
        """Consumer of completed tasks.

        By default control plane sends to message consumer of type "human".
        The process message logic contained here simply puts the TaskResult into
        a queue that is continuosly via a gr.Timer().
        """
        if message.action == ActionTypes.COMPLETED_TASK:
            task_res = TaskResult(**message.data)
            self.completed_tasks_queue.put(task_res)
            logger.info("Added task result to queue")

    def as_consumer(self, remote: bool = False) -> BaseMessageQueueConsumer:
        del remote

        return CallableMessageConsumer(
            message_type=self.name,
            handler=self._process_completed_task_messages,
        )

    async def register_to_message_queue(self) -> StartConsumingCallable:
        """Register to the message queue."""
        return await self.message_queue.register_consumer(self.as_consumer())
