from pydantic import BaseModel
from typing import List

from pydantic import BaseModel, root_validator, validator
from typing import List

class LegalResponse(BaseModel):
	laws: List[str]
	explanation: str
	possible_scenarios: List[str]
	actions: str

	@validator('possible_scenarios')
	def at_least_two_scenarios(cls, v):
		if not isinstance(v, list) or len(v) < 2:
			raise ValueError('possible_scenarios must be a list with at least 2 items')
		return v
from pydantic import BaseModel
from typing import List, Optional

class LawInfo(BaseModel):
	title: str
	section: Optional[str] = None
	text: str

class CaseInfo(BaseModel):
	title: str
	citation: Optional[str] = None
	summary: str

class QueryResponse(BaseModel):
	relevant_laws: List[LawInfo]
	explanation: str
	possible_scenarios: List[str]
	recent_cases: List[CaseInfo]
	suggested_actions: List[str]
	disclaimer: str
