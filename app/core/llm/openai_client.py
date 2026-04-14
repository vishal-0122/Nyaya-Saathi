
import os
from dataclasses import dataclass

from openai import OpenAI
from langsmith.wrappers import wrap_openai


@dataclass
class LLMResponse:
	content: str


class OpenAIInvokeAdapter:
	"""Adapter to preserve llm.invoke(...) interface used by graph nodes."""

	def __init__(self, client: OpenAI, model: str, temperature: float):
		self.client = client
		self.model = model
		self.temperature = temperature

	def invoke(self, prompt: str):
		completion = self.client.chat.completions.create(
			model=self.model,
			messages=[{"role": "user", "content": prompt}],
			temperature=self.temperature,
		)
		content = ""
		if completion.choices and completion.choices[0].message:
			content = completion.choices[0].message.content or ""
		return LLMResponse(content=content)

def get_llm():
	"""
	Returns an invoke-compatible LLM client backed by wrapped OpenAI SDK.
	Using wrap_openai enables automatic LangSmith tracing for OpenAI calls.
	"""
	api_key = os.getenv("OPENAI_API_KEY")
	model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
	temperature = float(os.getenv("OPENAI_TEMPERATURE", "0"))

	raw_client = OpenAI(api_key=api_key)
	wrapped_client = wrap_openai(raw_client)
	return OpenAIInvokeAdapter(
		client=wrapped_client,
		model=model_name,
		temperature=temperature,
	)
