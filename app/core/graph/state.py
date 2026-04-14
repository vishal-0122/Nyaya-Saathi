from typing import List, Optional

# Option 1: Simple Python class
class GraphState:
	def __init__(self, query: str, plan: Optional[str] = None, docs: Optional[List[str]] = None, answer: Optional[str] = None):
		self.query = query
		self.plan = plan
		self.docs = docs
		self.answer = answer

