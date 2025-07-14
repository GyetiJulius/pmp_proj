from datetime import date, timedelta
from typing import List, Dict, Any, Optional, TypedDict
# FIX: Import both Pydantic V2 and V1 models to resolve incompatibility
from pydantic import BaseModel as V2BaseModel
from pydantic.v1 import BaseModel as V1BaseModel, Field

# --- Pydantic V2 model for the API endpoint ---
class ProjectInput(V2BaseModel):
    project_title: str
    project_description: str
    objectives: Optional[List[str]] = None
    stakeholders: Optional[List[str]] = None
    budget: Optional[float] = None
    timeline_weeks: Optional[int] = None

# --- In-memory "database" to store project data ---
PROJECT_DB: Dict[str, "GraphState"] = {}

# --- Pydantic V1 Models for internal LangChain use ---
class CharterOutput(V1BaseModel):
    project_title: str = Field(description="The official title of the project.")
    project_description: str = Field(description="A brief summary of the project.")
    objectives: List[str] = Field(description="A list of 3-5 key project objectives.")
    requirements: List[str] = Field(description="A list of high-level project requirements.")
    stakeholders: List[str] = Field(description="A list of key stakeholders.")
    budget: float = Field(description="The estimated project budget.")
    timeline_weeks: int = Field(description="The estimated project timeline in weeks.")

class ScopeOutput(V1BaseModel):
    description: str = Field(description="A detailed description of the project's scope.")
    deliverables: List[str] = Field(description="A list of key project deliverables.")
    acceptance_criteria: List[str] = Field(description="Criteria for accepting the project deliverables.")
    exclusions: List[str] = Field(description="What is explicitly out of scope for the project.")
    constraints: List[str] = Field(description="Project constraints (e.g., budget, time, resources).")
    assumptions: List[str] = Field(description="Project assumptions made during planning.")

class WBSItem(V1BaseModel):
    task_name: str = Field(description="The name of the work package or task.")
    sub_tasks: list['WBSItem'] = Field(default_factory=list, description="A list of sub-tasks for this item.")

class WBSOutput(V1BaseModel):
    wbs_items: List[WBSItem] = Field(description="The root items of the Work Breakdown Structure.")

class RiskItem(V1BaseModel):
    risk_description: str
    probability: str
    impact: str
    response_strategy: str
    owner: str = Field(default="Project Manager")

class RiskRegister(V1BaseModel):
    risks: List[RiskItem]

class GanttTask(V1BaseModel):
    id: str = Field(description="A unique identifier for the task, e.g., '1.1'.")
    name: str = Field(description="The name of the task.")
    start: str = Field(description="The start date of the task in YYYY-MM-DD format.")
    end: str = Field(description="The end date of the task in YYYY-MM-DD format.")
    duration_days: int = Field(description="The estimated duration of the task in days.")

class ScheduleOutput(V1BaseModel):
    tasks: List[GanttTask]
    project_start_date: str = Field(description="The calculated start date of the entire project.")
    project_end_date: str = Field(description="The calculated end date of the entire project.")

# --- Pydantic Models for Stakeholder Analysis ---
class StakeholderItem(V1BaseModel):
    name: str = Field(description="The name of the stakeholder or stakeholder group.")
    role: str = Field(description="Their role in the project (e.g., Project Sponsor, End User).")
    interest: str = Field(description="A brief description of their primary interest or concern in the project.")
    influence: str = Field(description="Their level of influence on the project (e.g., High, Medium, Low).")
    engagement_strategy: str = Field(description="The strategy for engaging with this stakeholder (e.g., Manage Closely, Keep Informed).")

class StakeholderAnalysisOutput(V1BaseModel):
    """The complete stakeholder analysis document."""
    stakeholders: List[StakeholderItem]

# --- Pydantic Models for Communication Plan ---
class CommunicationItem(V1BaseModel):
    stakeholder: str = Field(description="The stakeholder or group to be communicated with.")
    information: str = Field(description="The type of information to be communicated (e.g., Project Status Update, Risk Alerts).")
    method: str = Field(description="The method of communication (e.g., Email, Weekly Meeting, Dashboard).")
    frequency: str = Field(description="How often the communication will occur (e.g., Weekly, Monthly, As Needed).")
    owner: str = Field(description="The person responsible for the communication (e.g., Project Manager, Tech Lead).")

class CommunicationPlanOutput(V1BaseModel):
    """The complete project communication plan."""
    communications: List[CommunicationItem]

# --- Main Graph State ---
class GraphState(TypedDict):
    project_id: str
    project_input: Dict[str, Any]
    documents: Dict[str, Any]
    deliverables_to_process: Optional[List[str]]
    current_deliverable: Optional[str]
    wbs_accumulator: List[Dict[str, Any]]

# --- Pydantic Models for LLM Outputs ---
# --- Pydantic model for the AI's duration estimation output ---
class TaskDuration(V1BaseModel):
    task_name: str = Field(description="The name of the task.")
    estimated_duration_days: int = Field(description="The expert estimation of how many business days this task will take.")
    stakeholders: List[str]
class DurationEstimationOutput(V1BaseModel):
    durations: List[TaskDuration]