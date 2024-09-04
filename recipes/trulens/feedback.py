__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import numpy as np
from trulens.core import Feedback
from trulens.core import Select
from trulens.providers.openai import OpenAI as OpenAIProvider

from dotenv import load_dotenv

load_dotenv()

provider = OpenAIProvider(model_engine="gpt-4o-mini")

# Define a groundedness feedback function
f_groundedness = (
    Feedback(
        provider.groundedness_measure_with_cot_reasons, name="Groundedness"
    )
    .on(Select.RecordCalls.retrieve.rets.collect())
    .on_output()
)
# Question/answer relevance between overall question and answer.
f_answer_relevance = (
    Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
    .on_input()
    .on_output()
)

# Context relevance between question and each context chunk.
f_context_relevance = (
    Feedback(
        provider.context_relevance_with_cot_reasons, name="Context Relevance"
    )
    .on_input()
    .on(Select.RecordCalls.retrieve.rets[:])
    .aggregate(np.mean)  # choose a different aggregation method if you wish
)

feedbacks = [f_groundedness, f_answer_relevance, f_context_relevance]

# note: feedback function used for guardrail must only return a score, not also reasons
f_guardrail = Feedback(
    provider.context_relevance, name="Context Relevance"
)
