from pydantic import BaseModel
from typing import List, Optional

class Element(BaseModel):
    id: int
    tag: str
    idAttr: Optional[str] = None  # Explicitly allow None
    ariaLabel: Optional[str] = None
    innerText: Optional[str] = None
    selector: str
    
class StrippedElement(BaseModel):
    id: int
    tag: str
    idAttr: Optional[str] = None  # Explicitly allow None
    ariaLabel: Optional[str] = None
    innerText: Optional[str] = None
    
class TaskOutcome(BaseModel):
    Nr: int
    Task: str
    Outcome: str


class TaskList(BaseModel):
    tasks: List[TaskOutcome]
