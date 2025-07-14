import uuid
from fastapi import FastAPI, HTTPException, Path, Body # FIX: Import Body
from fastapi.responses import Response, JSONResponse
from enum import Enum

from .state import ProjectInput, PROJECT_DB
from .graph import app_graph
# Import the new generator functions
from . import docx_generator

app = FastAPI(
    title="AI PMP Documentation Assistant API",
    version="2.1.0",
    description="Create a project to generate all documents, then preview or download them individually."
)

# Add the new document types to the Enum
class DocumentType(str, Enum):
    charter = "charter"
    scope = "scope"
    wbs = "wbs"
    risk_register = "risk-register"
    stakeholder_analysis = "stakeholder-analysis"
    communication_plan = "communication-plan"

# Add the new mappings to the dictionary
DOC_GENERATOR_MAP = {
    DocumentType.charter: docx_generator.generate_charter_docx,
    DocumentType.scope: docx_generator.generate_scope_docx,
    DocumentType.wbs: docx_generator.generate_wbs_docx,
    DocumentType.risk_register: docx_generator.generate_risk_register_docx,
    DocumentType.stakeholder_analysis: docx_generator.generate_stakeholder_analysis_docx,
    DocumentType.communication_plan: docx_generator.generate_communication_plan_docx,
}


@app.post("/projects", status_code=201, tags=["Project"])
def create_project(project_input: ProjectInput = Body(...)):
    """
    Creates a new project by accepting a JSON body, generates all documents, and returns a project ID.
    """
    project_id = str(uuid.uuid4())
    initial_state = {
        "project_id": project_id,
        # THE FIX: Use .model_dump(exclude_unset=False) to ensure all fields are present
        "project_input": project_input.model_dump(exclude_unset=False),
        "documents": {},
    }
    
    try:
        final_state = app_graph.invoke(initial_state)
        PROJECT_DB[project_id] = final_state
        return {"project_id": project_id, "message": "Project created successfully."}
    except Exception as e:
        # It's helpful to print the error to the console for debugging
        print(f"--- GRAPH EXECUTION FAILED ---: {e}")
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

@app.get("/projects/{project_id}/download/{doc_type}", tags=["Documents"])
def download_document(
    project_id: str = Path(..., description="The ID of the project."),
    doc_type: DocumentType = Path(..., description="The document type to download.")
):
    """
    Generates a .docx file on-demand from pre-generated data and returns it for download.
    """
    project_data = PROJECT_DB.get(project_id)
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    doc_key = doc_type.value
    document_content = project_data.get("documents", {}).get(doc_key)
    
    if not document_content:
        raise HTTPException(status_code=404, detail=f"Document '{doc_key}' not found for this project.")
        
    # Get the correct generator function from our map
    generator_func = DOC_GENERATOR_MAP.get(doc_type)
    if not generator_func:
        raise HTTPException(status_code=501, detail=f"No document generator available for '{doc_key}'.")

    try:
        # FIX: Access project_name from the nested project_input dictionary
        project_name = project_data.get("project_input", {}).get("project_title", "Project")

        # Generate the document in memory
        docx_bytes_io = generator_func(
            project_name=project_name,
            data=document_content
        )
        
        filename = f"{doc_key.replace('-', '_').title()}_{project_id}.docx"
        
        return Response(
            content=docx_bytes_io.getvalue(),
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")

@app.get("/projects/{project_id}/schedule", tags=["Data"])
def get_project_schedule(
    project_id: str = Path(..., description="The ID of the project.")
):
    """
    Retrieves the generated project schedule data, suitable for a Gantt chart.
    """
    project_data = PROJECT_DB.get(project_id)
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    schedule_content = project_data.get("documents", {}).get("schedule")
    if not schedule_content:
        raise HTTPException(status_code=404, detail="Schedule data not found for this project.")
        
    return JSONResponse(content=schedule_content)

