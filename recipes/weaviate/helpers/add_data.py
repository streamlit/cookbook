import pandas as pd
from pathlib import Path
import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5
from datetime import datetime, timezone
import toml
import os
from weaviate.classes.init import Auth
from tqdm import tqdm
import base64

# Construct the path to the toml file
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
toml_file_path = os.path.join(parent_dir, ".streamlit/secrets.toml")

config = toml.load(toml_file_path)

# Access values from the toml file
weaviate_api_key = config["WEAVIATE_API_KEY"]
weaviate_url = config["WEAVIATE_URL"]
cohere_api_key = config["COHERE_API_KEY"]

# Client for Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers={
        "X-Cohere-Api-Key": cohere_api_key
    }
)

# If you are using a local instance of Weaviate, you can use the following code
# client = weaviate.connect_to_local(headers={"X-Cohere-Api-Key": cohere_apikey})

# Delete any existing MovieDemo Collection to prevent errors
client.collections.delete(["MovieDemo"])

# Create the MovieDemo Collection
movies = client.collections.create(
    name="MovieDemo",
    properties=[
        Property(
            name="title",
            data_type=DataType.TEXT,
        ),
        Property(
            name="overview",
            data_type=DataType.TEXT,
        ),
        Property(
            name="tagline",
            data_type=DataType.TEXT,
        ),
        Property(
            name="movie_id",
            data_type=DataType.INT,
            skip_vectorization=True,
        ),
        Property(
            name="release_year",
            data_type=DataType.INT,
        ),
        Property(
            name="genres",
            data_type=DataType.TEXT_ARRAY,
        ),
        Property(
            name="vote_average",
            data_type=DataType.NUMBER,
        ),
        Property(
            name="vote_count",
            data_type=DataType.INT,
        ),
        Property(
            name="revenue",
            data_type=DataType.INT,
        ),
        Property(
            name="budget",
            data_type=DataType.INT,
        ),
        Property(
            name="poster",
            data_type=DataType.BLOB
        ),
    ],
    vectorizer_config=Configure.Vectorizer.text2vec_cohere(),
    vector_index_config=Configure.VectorIndex.hnsw(
        quantizer=Configure.VectorIndex.Quantizer.bq()
    ),
    generative_config=Configure.Generative.cohere(model="command-r-plus"),
)

# Add objects to the MovieDemo collection from the JSON file and directory of poster images
json_file_path = os.path.join(os.getcwd(), "helpers/data/1950_2024_movies_info.json")
movies_df = pd.read_json(json_file_path)

img_dir = Path(os.path.join(os.getcwd(), "helpers/data/posters"))

dataobj_list = list()

with movies.batch.fixed_size(100) as batch:
    for i, movie_row in tqdm(movies_df.iterrows()):
        try:
            date_object = datetime.strptime(movie_row["release_date"], "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            img_path = (img_dir / f"{movie_row['id']}_poster.jpg")
            with open(img_path, "rb") as file:
                poster_b64 = base64.b64encode(file.read()).decode("utf-8")

            props = {
                k: movie_row[k]
                for k in [
                    "title",
                    "overview",
                    "tagline",
                    "vote_count",
                    "vote_average",
                    "revenue",
                    "budget",
                ]
            }
            props["movie_id"] = movie_row["id"]
            props["release_year"] = date_object.year
            props["genres"] = [genre["name"] for genre in movie_row["genres"]]
            props["poster"] = poster_b64

            batch.add_object(properties=props, uuid=generate_uuid5(movie_row["id"]))
        except Exception as e:
            print(f"Error: {e}")
            movies_df = movies_df.drop(i)
            movies_df.to_json("./data/1950_2024_movies_info.json", orient="records")
            continue

# Close the connection to Weaviate Cloud
client.close()