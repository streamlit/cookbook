# How to run the demo app (Optional: Add what kind of app it is/the tech the app is built with)
## Overview
This is a recipe for a [TODO: Add the kind of app it is]. TODO: Add one sentence describing what the app does.

Other ways to explore this recipe:
* [Deployed app](TODO: URL of deployed app)
* [Blog post](TODO: URL of blog post)
* [Video](TODO: URL of video)

## Prerequisites
* Python >=3.8, !=3.9.7
* TODO: List additional prerequisites 

## Environment setup
### Local setup
1. Clone the Cookbook repo: `git clone https://github.com/streamlit/cookbook.git`
2. From the Cookbook root directory, change directory into the recipe: `cd recipes/TODO: Add recipe directory`
3. Add secrets to the `.streamlit/secrets_template.toml` file
4. Update the filename from `secrets_template.toml` to `secrets.toml`: `mv .streamlit/secrets_template.toml .streamlit/secrets.toml`
  
    (To learn more about secrets handling in Streamlit, refer to the documentation [here](https://docs.streamlit.io/develop/concepts/connections/secrets-management).)
5. Create a virtual environment: `python -m venv TODO: Add name of virtual environment`
6. Activate the virtual environment: `source TODO: Add name of virtual environment/bin/activate`  
7. Install the dependencies: `pip install -r requirements.txt`

### GitHub Codespaces setup
1. Create a new codespace by selecting the `Codespaces` option from the `Code` button
2. Once the codespace has been generated, add your secrets to the `recipes/TODO: Add recipe directory/.streamlit/secrets_template.toml` file
3. Update the filename from `secrets_template.toml` to `secrets.toml`
  
    (To learn more about secrets handling in Streamlit, refer to the documentation [here](https://docs.streamlit.io/develop/concepts/connections/secrets-management).)
4. From the Cookbook root directory, change directory into the recipe: `cd recipes/TODO: Add recipe directory`
5. Install the dependencies: `pip install -r requirements.txt`
