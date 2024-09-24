from llama_index.core.prompts import PromptTemplate

PREDICTION_PROMPT_TEMPLATE = PromptTemplate(
    """You are a bot that is very good at solving puzzles. Below is a list of input and output pairs with a pattern.
Identify the pattern in the training examples and predict the output for the provided TEST INPUT.

EXAMPLES:
{examples}

TEST INPUT:
{test_input}

OUTPUT FORMAT:
{{
    "output":
}}

Return your response in JSON format given above. DO NOT RETURN markdown code.
"""
)


REFLECTION_PROMPT_TEMPLATE = PromptTemplate(
    """You are a bot that is very good at solving puzzles. Below is a list of input and output pairs that share a
common pattern. The TEST INPUT also shares this common pattern, and you've previously predicted the output for it.
Your task now is critique the latest prediction on why it might not fit the pattern inherent in the example input/output pairs.

EXAMPLES:
{examples}

TEST INPUT:
{test_input}

PAST ATTEMPTS:
{past_attempts}

OUTPUT FORMAT:
{{
    "critique": ...
}}

Return your response in JSON format given above. DO NOT RETURN markdown code."""
)

CORRECTION_PROMPT_TEMPLATE = PromptTemplate(
    """You are a bot that is very good at solving puzzles. Below is a list of input and output pairs that share a
common pattern. The TEST INPUT also shares this common pattern, and you've previously predicted the output for it.
The predicted output was found to be incorrect and a critique has been articulated offering a potential
reason as to why it may have been a flawed prediction.

Your task now to create a new prediction that corrects from the previous attempts. Use
the last attempt and critique.

EXAMPLES:
{examples}

TEST INPUT:
{test_input}

PAST ATTEMPTS:
{past_attempts}

OUTPUT FORMAT:
{{
    "prediction": ...
}}

Return your response in JSON format given above. DO NOT RETURN markdown code."""
)
