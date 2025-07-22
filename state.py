from datetime import date, timedelta
from typing import Any, TypedDict, List, Dict, Optional
from pydantic import BaseModel, Field

# --- THE CHANGE IS HERE ---
# Updated the ProjectInput model to include the new fields from the frontend.
# I've made fields optional where appropriate to provide flexibility.
class ProjectInput(BaseModel):
    """Defines the structure for the initial project creation request."""
    project_title: str = Field(..., description="The official name of the project.")
    project_description: str = Field(..., description="A detailed description of the project's purpose and goals.")
    project_type: str = Field(..., description="The category or type of the project (e.g., Software Development, Construction).")
    
    # Existing fields, now made optional for flexibility
    key_stakeholders: Optional[List[str]] = Field(None, description="A list of key individuals or groups involved in the project.")
    project_objectives: Optional[List[str]] = Field(None, description="Specific, measurable objectives the project aims to achieve.")

    # New optional fields
    project_duration: Optional[str] = Field(None, description="The estimated duration of the project, e.g., '6 months'.")
    budget_range: Optional[str] = Field(None, description="The estimated budget range, e.g., '$100,000 - $250,000'.")
    team_size: Optional[str] = Field(None, description="The estimated size of the project team, e.g., '8-12 members'.")
    constraints: Optional[str] = Field(None, description="Known limitations, restrictions, or challenges.")
    assumptions: Optional[str] = Field(None, description="Assumptions being made about resources, timelines, etc.")

class CharterOutput(BaseModel):
    project_title: str = Field(description="The official title of the project.")
    project_description: str = Field(description="A brief summary of the project.")
    objectives: List[str] = Field(description="A list of 3-5 key project objectives.")
    requirements: List[str] = Field(description="A list of high-level project requirements.")
    stakeholders: List[str] = Field(description="A list of key stakeholders.")
    budget: float = Field(description="The estimated project budget.")
    timeline_weeks: int = Field(description="The estimated project timeline in weeks.")

class ScopeOutput(BaseModel):
    description: str = Field(description="A detailed description of the project's scope.")
    deliverables: List[str] = Field(description="A list of key project deliverables.")
    acceptance_criteria: List[str] = Field(description="Criteria for accepting the project deliverables.")
    exclusions: List[str] = Field(description="What is explicitly out of scope for the project.")
    constraints: List[str] = Field(description="Project constraints (e.g., budget, time, resources).")
    assumptions: List[str] = Field(description="Project assumptions made during planning.")

class WBSItem(BaseModel):
    task_name: str = Field(description="The name of the work package or task.")
    sub_tasks: list['WBSItem'] = Field(default_factory=list, description="A list of sub-tasks for this item.")

class WBSOutput(BaseModel):
    wbs_items: List[WBSItem] = Field(description="The root items of the Work Breakdown Structure.")

class RiskItem(BaseModel):
    risk_description: str
    probability: str
    impact: str
    response_strategy: str
    owner: str = Field(default="Project Manager")

class RiskRegister(BaseModel):
    risks: List[RiskItem]

class GanttTask(BaseModel):
    id: str = Field(description="A unique identifier for the task, e.g., '1.1'.")
    name: str = Field(description="The name of the task.")
    start: str = Field(description="The start date of the task in YYYY-MM-DD format.")
    end: str = Field(description="The end date of the task in YYYY-MM-DD format.")
    duration_days: int = Field(description="The estimated duration of the task in days.")

class ScheduleOutput(BaseModel):
    tasks: List[GanttTask]
    project_start_date: str = Field(description="The calculated start date of the entire project.")
    project_end_date: str = Field(description="The calculated end date of the entire project.")

# --- Pydantic Models for Stakeholder Analysis ---
class StakeholderItem(BaseModel):
    name: str = Field(description="The name of the stakeholder or stakeholder group.")
    role: str = Field(description="Their role in the project (e.g., Project Sponsor, End User).")
    interest: str = Field(description="A brief description of their primary interest or concern in the project.")
    influence: str = Field(description="Their level of influence on the project (e.g., High, Medium, Low).")
    engagement_strategy: str = Field(description="The strategy for engaging with this stakeholder (e.g., Manage Closely, Keep Informed).")

class StakeholderAnalysisOutput(BaseModel):
    """The complete stakeholder analysis document."""
    stakeholders: List[StakeholderItem]

# --- Pydantic Models for Communication Plan ---
class CommunicationItem(BaseModel):
    stakeholder: str = Field(description="The stakeholder or group to be communicated with.")
    information: str = Field(description="The type of information to be communicated (e.g., Project Status Update, Risk Alerts).")
    method: str = Field(description="The method of communication (e.g., Email, Weekly Meeting, Dashboard).")
    frequency: str = Field(description="How often the communication will occur (e.g., Weekly, Monthly, As Needed).")
    owner: str = Field(description="The person responsible for the communication (e.g., Project Manager, Tech Lead).")

class CommunicationPlanOutput(BaseModel):
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
class TaskDuration(BaseModel):
    task_name: str = Field(description="The name of the task.")
    estimated_duration_days: int = Field(description="The expert estimation of how many business days this task will take.")
    stakeholders: List[str]
class DurationEstimationOutput(BaseModel):
    durations: List[TaskDuration]