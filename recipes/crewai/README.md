## CrewAI Framework

CrewAI simplifies the orchestration of role-playing AI agents. In VacAIgent, these agents collaboratively decide on cities and craft a complete itinerary for your trip based on specified preferences, all accessible via a streamlined Streamlit user interface.

## Running the Application

- **Configure Environment**: Set up the environment variables for [Browseless](https://www.browserless.io/), [Serper](https://serper.dev/), and [OpenAI](https://openai.com/). Add your keys to `.streamlit/secrets.toml` file.

- **Install Dependencies**: Execute `pip install -r requirements.txt` in your terminal.
- **Launch the App**: Run `streamlit run streamlit_app.py` to start the Streamlit interface.

★ **Disclaimer**: The application uses GPT-4 by default. Ensure you have access to OpenAI's API and be aware of the associated costs.

## Details & Explanation

- **Components**:
  - `./trip_tasks.py`: Contains task prompts for the agents.
  - `./trip_agents.py`: Manages the creation of agents.
  - `./tools directory`: Houses tool classes used by agents.
  - `./streamlit_app.py`: The heart of the Streamlit app.

## Using GPT-4o mini

To switch from GPT-4 to GPT-4o-mini, pass the llm argument in the agent constructor:

```python
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model='gpt-4o-mini') # See more OpenAI models at https://platform.openai.com/docs/models/

class TripAgents:
    # ... existing methods

    def local_expert(self):
        return Agent(
            role='Local Expert',
            goal='Provide insights about the selected city',
            tools=[SearchTools.search_internet, BrowserTools.scrape_and_summarize_website],
            llm=llm,
            verbose=True
        )

```

## Using Local Models with Ollama

For enhanced privacy and customization, you can integrate local models like Ollama:

### Setting Up Ollama

- **Installation**: Follow Ollama's guide for installation.
- **Configuration**: Customize the model as per your requirements.

### Integrating Ollama with CrewAI

Pass the Ollama model to agents in the CrewAI framework:

```python
from langchain.llms import Ollama

ollama_model = Ollama(model="agent")

class TripAgents:
    # ... existing methods

    def local_expert(self):
        return Agent(
            role='Local Expert',
            tools=[SearchTools.search_internet, BrowserTools.scrape_and_summarize_website],
            llm=ollama_model,
            verbose=True
        )

```

