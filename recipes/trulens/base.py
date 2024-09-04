__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from openai import OpenAI
import numpy as np

from trulens.core import TruSession
from trulens.core.guardrails.base import context_filter
from trulens.apps.custom import instrument
from trulens.apps.custom import TruCustomApp
from trulens.providers.openai import OpenAI as OpenAIProvider
from trulens.core import Feedback
from trulens.core import Select
from trulens.core.guardrails.base import context_filter

from feedback import feedbacks, f_guardrail
from vector_store import vector_store

from dotenv import load_dotenv

load_dotenv()

oai_client = OpenAI()

tru = TruSession()

class RAG_from_scratch:
    @instrument
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        results = vector_store.query(query_texts=query, n_results=4)
        # Flatten the list of lists into a single list
        return [doc for sublist in results["documents"] for doc in sublist]

    @instrument
    def generate_completion(self, query: str, context_str: list) -> str:
        """
        Generate answer from context.
        """
        completion = (
            oai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"We have provided context information below. \n"
                        f"---------------------\n"
                        f"{context_str}"
                        f"\n---------------------\n"
                        f"First, say hello and that you're happy to help. \n"
                        f"\n---------------------\n"
                        f"Then, given this information, please answer the question: {query}",
                    }
                ],
            )
            .choices[0]
            .message.content
        )
        return completion

    @instrument
    def query(self, query: str) -> str:
        context_str = self.retrieve(query)
        completion = self.generate_completion(query, context_str)
        return completion

class filtered_RAG_from_scratch:
    @instrument
    @context_filter(f_guardrail, 0.75, keyword_for_prompt="query")
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        results = vector_store.query(query_texts=query, n_results=4)
        return [doc for sublist in results["documents"] for doc in sublist]

    @instrument
    def generate_completion(self, query: str, context_str: list) -> str:
        """
        Generate answer from context.
        """
        completion = (
            oai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"We have provided context information below. \n"
                        f"---------------------\n"
                        f"{context_str}"
                        f"\n---------------------\n"
                        f"Given this information, please answer the question: {query}",
                    }
                ],
            )
            .choices[0]
            .message.content
        )
        return completion

    @instrument
    def query(self, query: str) -> str:
        context_str = self.retrieve(query=query)
        completion = self.generate_completion(
            query=query, context_str=context_str
        )
        return completion


filtered_rag = filtered_RAG_from_scratch()

rag = RAG_from_scratch()

tru_rag = TruCustomApp(
    rag,
    app_name="RAG",
    app_version="v1",
    feedbacks=feedbacks,
)

filtered_tru_rag = TruCustomApp(
    filtered_rag,
    app_name="RAG",
    app_version="v2",
    feedbacks=feedbacks,
)