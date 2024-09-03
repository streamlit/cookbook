import weaviate
from weaviate.classes.query import Filter
from weaviate.classes.init import Auth
import toml
import os


# Construct the path to the toml file
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
toml_file_path = os.path.join(parent_dir, ".streamlit/secrets.toml")

config = toml.load(toml_file_path)

# Access values from the TOML file
weaviate_api_key = config["WEAVIATE_API_KEY"]
weaviate_url = config["WEAVIATE_URL"]
cohere_api_key = config["COHERE_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers={
        "X-Cohere-Api-Key": cohere_api_key
    }
)

# # If you are using a local instance of Weaviate, you can use the following code
# client = weaviate.connect_to_local(
#     headers={
#         "X-Cohere-Api-Key": cohere_api_key
#     }
# )

movies = client.collections.get("MovieDemo")

print(movies.aggregate.over_all(total_count=True))

r = movies.query.fetch_objects(limit=1, return_properties=["title"])
print(r.objects[0].properties["title"])

client.close()