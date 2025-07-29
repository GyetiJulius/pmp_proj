# THE DEFINITIVE FIX: Apply the gevent patch at the very top of the application entrypoint.
# This ensures it is active in the Uvicorn child process spawned by the reloader.
import gevent.monkey
gevent.monkey.patch_all()
# done

import uuid
from fastapi import FastAPI, HTTPException, Path, Body, status, BackgroundTasks
from fastapi.responses import Response
from enum import Enum

from state import ProjectInput
from redis_client import get_project_state, set_project_state
import docx_generator
from graph import app_graph # Import the graph

app = FastAPI(
    title="PMP Documentation Assistant API",
    description="An API to generate comprehensive PMP documents using an AI-powered agentic workflow.",
    version="1.0.0",
)

# --- This is the background task logic, moved from Celery ---
def run_project_graph(project_id: str, initial_state: dict):
    """
    This function runs in the background after the API response is sent.
    """
    try:
        print(f"---[BACKGROUND TASK] Starting graph for project_id: {project_id}---")
        
        final_state = app_graph.invoke(initial_state)
        final_state['status'] = 'COMPLETE'
        set_project_state(project_id, final_state)
        
        print(f"---[BACKGROUND TASK] Finished graph for project_id: {project_id}---")
        
    except Exception as e:
        print(f"---[BACKGROUND TASK] ERROR for project_id: {project_id}. Error: {e}---")
        error_state = get_project_state(project_id) or {}
        error_state['status'] = 'FAILED'
        error_state['error_message'] = str(e)
        set_project_state(project_id, error_state)

class DocumentType(str, Enum):
    charter = "charter"
    scope = "scope"
    wbs = "wbs"
    risk_register = "risk-register"
    stakeholder_analysis = "stakeholder-analysis"
    communication_plan = "communication-plan"

DOC_GENERATOR_MAP = {
    DocumentType.charter: docx_generator.generate_charter_docx,
    DocumentType.scope: docx_generator.generate_scope_docx,
    DocumentType.wbs: docx_generator.generate_wbs_docx,
    DocumentType.risk_register: docx_generator.generate_risk_register_docx,
    DocumentType.stakeholder_analysis: docx_generator.generate_stakeholder_analysis_docx,
    DocumentType.communication_plan: docx_generator.generate_communication_plan_docx,
}

@app.post("/projects", status_code=status.HTTP_202_ACCEPTED, tags=["Project"])
def create_project(project_input: ProjectInput, background_tasks: BackgroundTasks):
    """
    Accepts project parameters and starts the document generation process in the background.
    """
    project_id = str(uuid.uuid4())
    initial_state = {
        "project_id": project_id,
        "project_input": project_input.model_dump(exclude_unset=False),
        "documents": {},
        "status": "PENDING"
    }
    
    set_project_state(project_id, initial_state)
    
    # Add the graph execution to the background tasks
    background_tasks.add_task(run_project_graph, project_id, initial_state)
    
    return {
        "project_id": project_id, 
        "message": "Project generation has been started."
    }

@app.get("/projects/{project_id}/status", tags=["Project"])
def get_project_status(project_id: str):
    """
    Checks the status of a project generation task.
    """
    project_data = get_project_state(project_id)
    if not project_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return {
        "project_id": project_id,
        "status": project_data.get("status", "UNKNOWN"),
        "error": project_data.get("error_message")
    }

@app.get("/projects/{project_id}/download/{doc_type}", tags=["Documents"])
def download_document(project_id: str, doc_type: DocumentType):
    """
    Downloads a generated document for a completed project.
    """
    project_data = get_project_state(project_id)
    
    if not project_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        
    if project_data.get("status") != "COMPLETE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Project generation is not complete. Current status: {project_data.get('status', 'UNKNOWN')}"
        )

    doc_key = doc_type.value
    if doc_key not in project_data.get("documents", {}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{doc_key}' not found for this project.")

    doc_data = project_data["documents"][doc_key]
    generator_func = DOC_GENERATOR_MAP[doc_type]
    
    try:
        doc_io = generator_func(data=doc_data, project_name=project_data["project_input"]["project_title"])
        return Response(
            content=doc_io.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={project_id}_{doc_key}.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating document: {str(e)}")

