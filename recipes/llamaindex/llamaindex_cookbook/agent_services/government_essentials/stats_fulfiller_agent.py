import asyncio
import json
import logging
from typing import Any, Dict, List

import uvicorn
from llama_agents import AgentService, ServiceComponent
from llama_agents.message_queues.rabbitmq import RabbitMQMessageQueue
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine, text

from llamaindex_cookbook.utils import load_from_env

logger = logging.getLogger(__name__)


message_queue_host = load_from_env("RABBITMQ_HOST")
message_queue_port = load_from_env("RABBITMQ_NODE_PORT")
message_queue_username = load_from_env("RABBITMQ_DEFAULT_USER")
message_queue_password = load_from_env("RABBITMQ_DEFAULT_PASS")
control_plane_host = load_from_env("CONTROL_PLANE_HOST")
control_plane_port = load_from_env("CONTROL_PLANE_PORT")
agent_host = load_from_env("STATS_FULFILLER_AGENT_HOST")
agent_port = load_from_env("STATS_FULFILLER_AGENT_PORT")
snowflake_user = load_from_env("SNOWFLAKE_USERNAME")
snowflake_password = load_from_env("SNOWFLAKE_PASSWORD")
snowflake_account = load_from_env("SNOWFLAKE_ACCOUNT")
snowflake_role = load_from_env("SNOWFLAKE_ROLE")
localhost = load_from_env("LOCALHOST")


# create agent server
message_queue = RabbitMQMessageQueue(
    url=f"amqp://{message_queue_username}:{message_queue_password}@{message_queue_host}:{message_queue_port}/"
)

AGENT_SYSTEM_PROMPT = """
Query the database to return timeseries data of user-specified geographic/demographic statistic.

Use the tool to return the time series data as a JSON with the folowing format:

{{
    [
        {{
            "variable": ...,
            "date": ...,
            "value": ...
        }},
        {{
            "variable": ...,
            "date": ...,
            "value": ...
        }},
        ...
    ]
}}

Don't return the output as markdown code. Don't modify the tool output. Return
strictly the tool ouput.
"""


SQL_QUERY_TEMPLATE = """
SELECT
    ts.date as date,
    ts.variable_name,
    ts.value as value
FROM cybersyn.datacommons_timeseries AS ts
JOIN cybersyn.geography_index AS geo ON (ts.geo_id = geo.geo_id)
WHERE geo.geo_name = '{city}'
  AND geo.level IN ('City')
  AND ts.variable_name ILIKE '{stats_variable}%'
  AND date >= '2015-01-01'
ORDER BY date;
"""


def get_time_series_of_statistic_variable(
    city: str, stats_variable: str
) -> str:
    """Create a time series of a specified stats variable."""
    query = SQL_QUERY_TEMPLATE.format(city=city, stats_variable=stats_variable)
    url = URL(
        account=snowflake_account,
        user=snowflake_user,
        password=snowflake_password,
        database="GOVERNMENT_ESSENTIALS",
        schema="CYBERSYN",
        warehouse="COMPUTE_WH",
        role=snowflake_role,
    )

    engine = create_engine(url)
    try:
        connection = engine.connect()
        results = connection.execute(text(query))
    except Exception:
        logger.debug("Failed to execute query")
        raise
    finally:
        connection.close()

    # process
    results = [
        {"variable": str(el[1]), "date": str(el[0]), "value": str(el[2])}
        for el in results
    ]
    results_str = json.dumps(results, indent=4)

    return results_str


def perform_date_value_aggregation(json_str: str) -> List[Dict[str, Any]]:
    """Perform value aggregation on the time series data."""
    timeseries_data = json.loads(json_str)
    variable = timeseries_data[0]["variable"]

    new_time_series_data: Dict[str, List[float]] = {}
    for el in timeseries_data:
        date = el["date"]
        value = el["value"]
        if date in new_time_series_data:
            new_time_series_data[date].append(float(value))
        else:
            new_time_series_data[date] = [float(value)]

    reduced_time_series_data = [
        {
            "variable": variable,
            "date": date,
            "value": sum(values) / len(values),
        }
        for date, values in new_time_series_data.items()
    ]

    return reduced_time_series_data


stats_fulfiller_tool = FunctionTool.from_defaults(
    fn=get_time_series_of_statistic_variable, return_direct=True
)
agent = OpenAIAgent.from_tools(
    [stats_fulfiller_tool],
    system_prompt=AGENT_SYSTEM_PROMPT,
    llm=OpenAI(model="gpt-4o-mini"),
    verbose=True,
)

agent_server = AgentService(
    agent=agent,
    message_queue=message_queue,
    description="Gets the stats data for a given statistical variable",
    service_name="stats_fulfiller_agent",
    host=agent_host,
    port=int(agent_port) if agent_port else None,
)
agent_component = ServiceComponent.from_service_definition(agent_server)

app = agent_server._app


# launch
async def launch() -> None:
    # register to message queue
    start_consuming_callable = await agent_server.register_to_message_queue()
    _ = asyncio.create_task(start_consuming_callable())

    # register to control plane
    await agent_server.register_to_control_plane(
        control_plane_url=(
            f"http://{control_plane_host}:{control_plane_port}"
            if control_plane_port
            else f"http://{control_plane_host}"
        )
    )

    cfg = uvicorn.Config(
        agent_server._app,
        host=localhost,
        port=agent_server.port,
    )
    server = uvicorn.Server(cfg)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(launch())
