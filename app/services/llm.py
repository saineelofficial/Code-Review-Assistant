from langchain_community.llms import Ollama
import os

# Model name can be overridden from env in the workflow step
MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:7b-instruct")

_llm = Ollama(model=MODEL)

def review_with_llm(prompt: str) -> str:
    """Single-call wrapper around local Ollama LLM."""
    return _llm.invoke(prompt)
