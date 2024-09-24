from llama_index.core.workflow import Event


class FormatTaskEvent(Event):
    ...


class PredictionEvent(Event):
    ...


class EvaluationEvent(Event):
    passing: bool


class CorrectionEvent(Event):
    ...
