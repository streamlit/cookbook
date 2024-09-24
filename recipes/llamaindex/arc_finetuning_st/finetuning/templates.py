SYSTEM_MESSAGE = """You are a bot that is very good at solving puzzles. You will work with the user who will present you a new puzzle to solve it.
The puzzle consists of a list of EXAMPLES, each containing an INPUT/OUTPUT pair describing a pattern which is shared amongst all examples.
The user will also provide a TEST INPUT for which you are to produce a predicted OUTPUT that follows the common pattern of all the examples.

Your task is collaborate with the user in order to solve the problem.
"""

USER_TASK_TEMPLATE = """Here is a new task to solve:
EXAMPLES:
{examples}

TEST INPUT:
{test_input}
"""

# attempt.prediction
ASSISTANT_TEMPLATE = """
PREDICTED OUTPUT:
{predicted_output}

RATIONALE:
{rationale}
"""

# attempt.critique
USER_CRITIQUE_TEMPLATE = """
{critique}
"""
