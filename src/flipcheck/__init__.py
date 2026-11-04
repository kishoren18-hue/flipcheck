"""flipcheck: does your model give the same answer when you only change the wording?"""

from .backends import Anthropic, Command, OpenAICompatible, make_backend
from .core import QuestionResult, Summary, evaluate_question, run, summarize
from .paraphrase import llm_paraphrases, rule_paraphrases

__version__ = "0.1.0"
