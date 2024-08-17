# How to run the demo Replicate Streamlit chatbot app
This is a demo of a Replicate Streamlit chatbot app. The app uses a single API to access 3 different LLMs and adjust parameters such as temperature and top-p.

For a walkthrough of the demo and to hear from Replicate founding designer Zeke Sikelianos, check out the video [here](https://youtu.be/zsQ7EN10zj8).

## Prerequisites
* Python
* A [Replicate API token](https://replicate.com/signin?next=/account/api-tokens)
    (Please note that a payment method is required to access features beyond the free trial limits.)

## Environment setup
### Local setup
1. Clone the Cookbook repo: `git clone https://github.com/streamlit/cookbook.git`
2. From the Cookbook root directory, change directory into the Replicate recipe: `cd recipes/replicate`
3. Add your Replicate API token to the `.streamlit/secrets_template.toml` file
4. Update the filename from `secrets_template.toml` to `secrets.toml`: `mv .streamlit/secrets_template.toml .streamlit/secrets.toml`
  
    (To learn more about secrets handling in Streamlit, refer to the documentation [here](https://docs.streamlit.io/develop/concepts/connections/secrets-management).)
5. Create a virtual environment: `python -m venv replicatevenv`
6. Activate the virtual environment: `source replicatevenv/bin/activate`  
7. Install the dependencies: `pip install -r requirements.txt`

### GitHub Codespaces setup
1. Create a new codespace by selecting the `Codespaces` option from the `Code` button
2. Once the codespace has been generated, add your Replicate API token to the `recipes/replicate/.streamlit/secrets_template.toml` file
3. Update the filename from `secrets_template.toml` to `secrets.toml`
  
    (To learn more about secrets handling in Streamlit, refer to the documentation [here](https://docs.streamlit.io/develop/concepts/connections/secrets-management).)
4. From the Cookbook root directory, change directory into the Replicate recipe: `cd recipes/replicate`
5. Install the dependencies: `pip install -r requirements.txt`
