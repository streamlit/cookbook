import weaviate
from weaviate.classes.query import Filter
from weaviate.classes.init import Auth
import toml
import os


config = toml.load("/Users/lacosta/Desktop/PROJECTS/cookbook/recipes/weaviate/.streamlit/secrets.toml")

# Access values from the TOML file
weaviate_api_key = config["WEAVIATE_API_KEY"]
weaviate_url = config["WEAVIATE_URL"]
cohere_api_key = config["COHERE_API_KEY"]

weaviate_url = config["WEAVIATE_URL"]
weaviate_apikey = config["WEAVIATE_API_KEY"]  # WCS_DEMO_ADMIN_KEY or WCS_DEMO_RO_KEY
cohere_apikey = config["COHERE_API_KEY"]


client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_apikey),
    headers={
        "X-Cohere-Api-Key": cohere_apikey
    }
)

# # If you are using a local instance of Weaviate, you can use the following code
# client = weaviate.connect_to_local(
#     headers={
#         "X-Cohere-Api-Key": cohere_apikey
#     }
# )

movies = client.collections.get("MovieDemo")

print(movies.aggregate.over_all(total_count=True))

r = movies.query.fetch_objects(limit=1, return_properties=["poster"])
print(r.objects[0].properties["poster"])

client.close()
