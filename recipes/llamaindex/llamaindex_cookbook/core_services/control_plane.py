import asyncio

import uvicorn
from llama_agents import (
    ControlPlaneServer,
    OrchestratorRouter,
    PipelineOrchestrator,
)
from llama_agents.message_queues.rabbitmq import RabbitMQMessageQueue
from llama_index.core.query_pipeline import QueryPipeline
from llama_index.core.selectors import PydanticSingleSelector
from llama_index.llms.openai import OpenAI

from llamaindex_cookbook.additional_services.human_in_the_loop import (
    human_component,
)
from llamaindex_cookbook.agent_services import (
    funny_agent_component,
    funny_agent_server,
    goods_getter_agent_component,
    stats_fulfiller_agent_component,
    stats_getter_agent_component,
    time_series_getter_agent_component,
)
from llamaindex_cookbook.utils import load_from_env

message_queue_host = load_from_env("RABBITMQ_HOST")
message_queue_port = load_from_env("RABBITMQ_NODE_PORT")
message_queue_username = load_from_env("RABBITMQ_DEFAULT_USER")
message_queue_password = load_from_env("RABBITMQ_DEFAULT_PASS")
control_plane_host = load_from_env("CONTROL_PLANE_HOST")
control_plane_port = load_from_env("CONTROL_PLANE_PORT")
localhost = load_from_env("LOCALHOST")


# setup message queue
message_queue = RabbitMQMessageQueue(
    url=f"amqp://{message_queue_username}:{message_queue_password}@{message_queue_host}:{message_queue_port}/"
)

# historical prices of a good pipeline
timeseries_task_pipeline = QueryPipeline(
    chain=[
        goods_getter_agent_component,
        human_component,
        time_series_getter_agent_component,
    ],
)
timeseries_pipeline_orchestrator = PipelineOrchestrator(
    timeseries_task_pipeline
)
timeseries_task_pipeline_desc = """Only used for getting historical price
(timeseries) data for a specified good from the database.
"""

# government statistics pipeline
city_stats_pipeline = QueryPipeline(
    chain=[
        stats_getter_agent_component,
        human_component,
        stats_fulfiller_agent_component,
    ],
)
city_stats_pipeline_orchestrator = PipelineOrchestrator(city_stats_pipeline)
city_stats_pipeline_desc = """Only used for getting geographic and demographic
statistics for a specified city.
"""

# general pipeline
general_pipeline = QueryPipeline(chain=[funny_agent_component])
general_pipeline_orchestrator = PipelineOrchestrator(general_pipeline)

pipeline_orchestrator = OrchestratorRouter(
    selector=PydanticSingleSelector.from_defaults(llm=OpenAI("gpt-4o-mini")),
    orchestrators=[
        timeseries_pipeline_orchestrator,
        city_stats_pipeline_orchestrator,
        general_pipeline_orchestrator,
    ],
    choices=[
        timeseries_task_pipeline_desc,
        city_stats_pipeline_desc,
        funny_agent_server.description,
    ],
)

# setup control plane
control_plane = ControlPlaneServer(
    message_queue=message_queue,
    orchestrator=pipeline_orchestrator,
    host=control_plane_host,
    port=int(control_plane_port) if control_plane_port else None,
)


app = control_plane.app


# launch
async def launch() -> None:
    # register to message queue and start consuming
    start_consuming_callable = await control_plane.register_to_message_queue()
    _ = asyncio.create_task(start_consuming_callable())

    cfg = uvicorn.Config(
        control_plane.app,
        host=localhost,
        port=control_plane.port,
    )
    server = uvicorn.Server(cfg)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(launch())
