import asyncio

import uvicorn
from llama_agents import AgentService, ServiceComponent
from llama_agents.message_queues.rabbitmq import RabbitMQMessageQueue
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine, text

from llamaindex_cookbook.utils import load_from_env

message_queue_host = load_from_env("RABBITMQ_HOST")
message_queue_port = load_from_env("RABBITMQ_NODE_PORT")
message_queue_username = load_from_env("RABBITMQ_DEFAULT_USER")
message_queue_password = load_from_env("RABBITMQ_DEFAULT_PASS")
control_plane_host = load_from_env("CONTROL_PLANE_HOST")
control_plane_port = load_from_env("CONTROL_PLANE_PORT")
agent_host = load_from_env("STATS_GETTER_AGENT_HOST")
agent_port = load_from_env("STATS_GETTER_AGENT_PORT")
snowflake_user = load_from_env("SNOWFLAKE_USERNAME")
snowflake_password = load_from_env("SNOWFLAKE_PASSWORD")
snowflake_account = load_from_env("SNOWFLAKE_ACCOUNT")
snowflake_role = load_from_env("SNOWFLAKE_ROLE")
localhost = load_from_env("LOCALHOST")


# create agent server
message_queue = RabbitMQMessageQueue(
    url=f"amqp://{message_queue_username}:{message_queue_password}@{message_queue_host}:{message_queue_port}/"
)

SQL_QUERY_TEMPLATE = """
SELECT DISTINCT
       ts.variable_name
FROM cybersyn.datacommons_timeseries AS ts
JOIN cybersyn.geography_index AS geo ON (ts.geo_id = geo.geo_id)
WHERE geo.geo_name = '{city}'
  AND geo.level IN ('City')
  AND date >= '2015-01-01';
"""

AGENT_SYSTEM_PROMPT = """
For a given query about a geographic and population statistic, your job is to first
find the statistical variables that exists in the database.

Return the list of the three most relevant statistical variables that exist in the
database and that potentially match the object of the users query.

Output your list in the following format:

1. <variable-1> for <specified-city>,
2. <variable-2> for <specified-city>,
3. <variable-3> for <specified-city>

Be sure to use the exact variable names that were retrieved from the database tool!
"""


def get_list_of_statistical_variables(city: str, query: str) -> str:
    """Returns a list of statistical variables that closely resemble the query.

    The list of statistical vars is represented as a string separated by '\n'.
    """
    query = SQL_QUERY_TEMPLATE.format(city=city)
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
    finally:
        connection.close()

    # process
    results = [f"{ix+1}. {str(el[0])}" for ix, el in enumerate(results)]
    results_str = "List of statistical variables that exist in the database are provided below. Please select one.:\n\n"
    results_str += "\n".join(results)

    return results_str


statistics_getter_tool = FunctionTool.from_defaults(
    fn=get_list_of_statistical_variables
)
agent = OpenAIAgent.from_tools(
    [statistics_getter_tool],
    system_prompt=AGENT_SYSTEM_PROMPT,
    llm=OpenAI(model="gpt-4o-mini"),
    verbose=True,
)

agent_server = AgentService(
    agent=agent,
    message_queue=message_queue,
    description="Retrieves the statistical variables that exist in the database that match the user's query.",
    service_name="stats_getter_agent",
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
