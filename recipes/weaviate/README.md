# How to run the demo app
This is a recipe for a movie recommendation app. The app uses [Weaviate](https://weaviate.io/) to create a vector database of movie titles and [Streamlit](https://streamlit.io/) to create a recommendation chatbot.

Other ways to explore this recipe:
* [Deployed app](https://weaviate-movie-magic.streamlit.app/)
* [Video](https://youtu.be/SQD-aWlhqvM?si=t54W53G1gWnTAiwx)
* [Blog post](https://blog.streamlit.io/how-to-recommendation-app-vector-database-weaviate/)

## Prerequisites
* Python >=3.8, !=3.9.7
* [A Weaviate API key and URL](https://auth.wcs.api.weaviate.io/auth/realms/SeMI/login-actions/registration?client_id=wcs-frontend&tab_id=5bw6GQTdWU0)
* [A Cohere API key](https://dashboard.cohere.com/welcome/register)    

## Environment setup
### Local setup

#### Create a virtual environment
1. Clone the Cookbook repo: `git clone https://github.com/streamlit/cookbook.git`
2. From the Cookbook root directory, change directory into the recipe: `cd recipes/weaviate`
3. Add secrets to the `.streamlit/secrets_template.toml` file
4. Update the filename from `secrets_template.toml` to `secrets.toml`: `mv .streamlit/secrets_template.toml .streamlit/secrets.toml`
  
    (To learn more about secrets handling in Streamlit, refer to the documentation [here](https://docs.streamlit.io/develop/concepts/connections/secrets-management).)
5. Create a virtual environment: `python3 -m venv weaviatevenv`
6. Activate the virtual environment: `source weaviatevenv/bin/activate`  
7. Install the dependencies: `pip install -r requirements.txt`

#### Add data to your Weaviate Cloud
1. Create a Weaviate Cloud [Collection](https://weaviate.io/developers/weaviate/config-refs/schema#introduction) and add data to it: `python3 helpers/add_data.py`
2. (Optional) Verify the data: `python3 helpers/verify_data.py`
3. (Optional) Use the Weaviate Cloud UI to [query the Collection](https://weaviate.io/developers/weaviate/connections/connect-query#example-query):
    ```
    { Get {MovieDemo (limit: 3
    where: { path: ["release_year"],
    operator: Equal,
    valueInt: 1985}) {
    budget
    movie_id
    overview
    release_year
    revenue
    tagline
    title
    vote_average
    vote_count
    }}}
    ```

#### Run the app
1. Run the app with: `streamlit run demo_app.py`
2. The app should spin up in a new browser tab
    
    (Please note that this version of the demo app does not feature the poster images so it will look different from the [deployed app](https://weaviate-movie-magic.streamlit.app/).) 
