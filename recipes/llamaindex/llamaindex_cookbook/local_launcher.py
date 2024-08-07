from llama_agents import ServerLauncher

from llamaindex_cookbook.additional_services.human_in_the_loop import (
    human_service,
)
from llamaindex_cookbook.agent_services.funny_agent import agent_server
from llamaindex_cookbook.core_services.control_plane import control_plane
from llamaindex_cookbook.core_services.message_queue import message_queue

# launch it
launcher = ServerLauncher(
    [agent_server, human_service],
    control_plane,
    message_queue,
)


if __name__ == "__main__":
    launcher.launch_servers()
