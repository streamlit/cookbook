# LlamaAgents Demo With Snowflake/Cybersyn Data Agents

<img width="960" alt="image" src="https://github.com/user-attachments/assets/2d82ac2b-d37f-4b86-9867-69947402c924">

For this demo app, we have a multi-agent system comprised with the following
components:

- A data **Agent** that performs queries over [Cybersyn's Financial & Economic Essentials](https://app.snowflake.com/marketplace/listing/GZTSZAS2KF7/cybersyn-financial-economic-essentials?originTab=provider&providerName=Cybersyn&profileGlobalName=GZTSZAS2KCS) Dataset
- A data **Agent** that performs queries over [Cyberysyn' Government Essentials](https://app.snowflake.com/marketplace/listing/GZTSZAS2KGK/cybersyn-government-essentials?originTab=provider&providerName=Cybersyn&profileGlobalName=GZTSZAS2KCS) Dataset
- A general **Agent** that can answer all general queries
- A **Human (In the Loop) Service** that provides inputs to the two data agents
- A **ControlPlane** that features a router which routes tasks to the most appropriate orchestrator
- A **RabbitMQ MessageQueue** to broker communication between agents, human-in-the-loop, and control-plane

For the frontend, we built a Streamlit App to interact with this multi-agent
system.

## Pre-Requisites

### Poetry

For this app, we use [Poetry](https://python-poetry.org/) as the package's
dependency manager. The `poetry` cli tool is what we'll need to install the package's
virtual environment in order to run our streamlit app.

### Docker

To run this demo, we make use of `Docker`, specifically `docker-compose`. For this
demo, all of the necessary services (with the exception of the message queue)
are packaged in one common Docker image and can be instantianted through their
respective commands (i.e., see `docker-compose.yml`.)

### Credentials

For this app, we use OpenAI as the LLM provider and so an `OPENAI_API_KEY` will
need to be supplied. Moreover, the Cybersyn data is pulled from Snowflake and so
various Snowflake params are also required. See the section "# FILL-IN" in the
`template.env.docker` file. Once, you've filled in the necessary environment
variables, rename the file to `.env.docker`.

Similarly, you need to provide credentials in the `template.env.local`. Once
filled in, rename the file to `.env.local`.

## Running The App

### The backend (multi-agent system)

To start the multi-agent system, use the following command while in the root of
the project directory:

```sh
docker-compose up --build
```

### Streamlit App

Once the services are all running, you can then run the streamlit app. First,
ensure that you have the package's virtual environment active and the environment
variables set. Again, while in the root directory of this project, run the commands
found below:

```sh
poetry shell
poetry install
set -a && source .env.local
```

Next, run the streamlit app:

```sh
streamlit run llamaindex_cookbook/apps/streamlit.py
```
