__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import openai
import os
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from dotenv import load_dotenv

load_dotenv()

uw_info = """
The University of Washington, founded in 1861 in Seattle, is a public research university
with over 45,000 students across three campuses in Seattle, Tacoma, and Bothell.
As the flagship institution of the six public universities in Washington state,
UW encompasses over 500 buildings and 20 million square feet of space,
including one of the largest library systems in the world.
"""

wsu_info = """
Washington State University, commonly known as WSU, founded in 1890, is a public research university in Pullman, Washington.
With multiple campuses across the state, it is the state's second largest institution of higher education.
WSU is known for its programs in veterinary medicine, agriculture, engineering, architecture, and pharmacy.
"""

seattle_info = """
Seattle, a city on Puget Sound in the Pacific Northwest, is surrounded by water, mountains and evergreen forests, and contains thousands of acres of parkland.
It's home to a large tech industry, with Microsoft and Amazon headquartered in its metropolitan area.
The futuristic Space Needle, a legacy of the 1962 World's Fair, is its most iconic landmark.
"""

starbucks_info = """
Starbucks Corporation is an American multinational chain of coffeehouses and roastery reserves headquartered in Seattle, Washington.
As the world's largest coffeehouse chain, Starbucks is seen to be the main representation of the United States' second wave of coffee culture.
"""

newzealand_info = """
New Zealand is an island country located in the southwestern Pacific Ocean. It comprises two main landmasses—the North Island and the South Island—and over 700 smaller islands.
The country is known for its stunning landscapes, ranging from lush forests and mountains to beaches and lakes. New Zealand has a rich cultural heritage, with influences from 
both the indigenous Māori people and European settlers. The capital city is Wellington, while the largest city is Auckland. New Zealand is also famous for its adventure tourism,
including activities like bungee jumping, skiing, and hiking.
"""

embedding_function = OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-ada-002",
)


chroma_client = chromadb.Client()
vector_store = chroma_client.get_or_create_collection(
    name="Washington", embedding_function=embedding_function
)

vector_store.add("uw_info", documents=uw_info)
vector_store.add("wsu_info", documents=wsu_info)
vector_store.add("seattle_info", documents=seattle_info)
vector_store.add("starbucks_info", documents=starbucks_info)
vector_store.add("newzealand_info", documents=newzealand_info)