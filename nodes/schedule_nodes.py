from datetime import date, timedelta
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from pydantic.v1 import BaseModel, Field
from typing import List
from langchain_core.output_parsers import JsonOutputParser # Import the parser

from ..state import GraphState, GanttTask, ScheduleOutput
from ..config import get_cohere_api_key

# --- Pydantic model for the AI's duration estimation output ---
class TaskDuration(BaseModel):
    task_name: str = Field(description="The name of the task.")
    estimated_duration_days: int = Field(description="The expert estimation of how many business days this task will take.")

class DurationEstimationOutput(BaseModel):
    durations: List[TaskDuration]

# --- Helper function to flatten the WBS ---
def flatten_wbs(wbs_items, prefix=""):
    """Recursively flattens the WBS into a simple list of tasks with IDs."""
    flat_list = []
    for i, item in enumerate(wbs_items, 1):
        task_id = f"{prefix}{i}"
        flat_list.append({"id": task_id, "name": item["task_name"]})
        if item.get("sub_tasks"):
            flat_list.extend(flatten_wbs(item["sub_tasks"], prefix=f"{task_id}."))
    return flat_list

def generate_schedule_node(state: GraphState):
    """Generates a project schedule with estimated durations for Gantt charts."""
    print("---NODE: GENERATING PROJECT SCHEDULE---")
    
    wbs_data = state.get("documents", {}).get("wbs", {})
    if not wbs_data.get("wbs_items"):
        print("---WARNING: WBS data not found. Skipping schedule generation.---")
        return state

    # 1. Flatten the WBS into a task list
    tasks_to_estimate = flatten_wbs(wbs_data["wbs_items"])
    task_names_only = [task["name"] for task in tasks_to_estimate]

    # 2. Use an AI agent to estimate durations
    print("---STEP 1: Estimating task durations with AI---")
    # THE FIX: Use the robust JsonOutputParser method
    parser = JsonOutputParser(pydantic_object=DurationEstimationOutput)
    llm = ChatCohere(
        model="command-a-03-2025",
        api_key=get_cohere_api_key()
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior project scheduler. Provide realistic duration estimates in BUSINESS DAYS for a list of project tasks. Respond with a JSON object that strictly follows this format:\n{format_instructions}"),
        ("user", "Please provide duration estimates for the following tasks:\n\n{tasks}"),
    ])
    chain = prompt | llm | parser
    
    duration_map = {}
    try:
        estimation_result = chain.invoke({
            "tasks": "\n".join(f"- {name}" for name in task_names_only),
            "format_instructions": parser.get_format_instructions(),
        })
        # The parser returns a dict, so we can process it directly
        duration_map = {item['task_name']: item['estimated_duration_days'] for item in estimation_result['durations']}
    except Exception as e:
        print(f"---ERROR: AI duration estimation failed: {e}. Using fallback.---")
        duration_map = {name: 3 for name in task_names_only} # Fallback to 3 days per task

    # 3. Calculate start and end dates
    print("---STEP 2: Calculating schedule dates---")
    schedule_tasks = []
    current_date = date.today()
    project_start_date = current_date

    for task in tasks_to_estimate:
        duration = duration_map.get(task["name"], 3) # Default to 3 days if not found
        start_date = current_date
        end_date = start_date + timedelta(days=duration - 1) # Duration of 1 day means start and end are same day
        
        schedule_tasks.append(GanttTask(
            id=task["id"],
            name=task["name"],
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            duration_days=duration
        ))
        
        # Next task starts on the next business day
        current_date = end_date + timedelta(days=1)
    
    project_end_date = current_date - timedelta(days=1)

    # 4. Save the schedule to the state
    schedule_output = ScheduleOutput(
        tasks=schedule_tasks,
        project_start_date=project_start_date.strftime("%Y-%m-%d"),
        project_end_date=project_end_date.strftime("%Y-%m-%d")
    )

    current_docs = state["documents"]
    current_docs["schedule"] = schedule_output.dict()
    
    print("---NODE: SCHEDULE GENERATION COMPLETE---")
    return {"documents": current_docs}