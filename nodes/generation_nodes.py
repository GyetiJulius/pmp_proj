import json
from state import GraphState, CharterOutput, ScopeOutput
from config import get_cohere_api_key
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

def generate_charter_node(state: GraphState):
    """Generates charter data using a robust JSON parser."""
    print("---NODE: GENERATING CHARTER---")
    
    try:
        project_input = state["project_input"]
        parser = JsonOutputParser(pydantic_object=CharterOutput)
        llm = ChatCohere(model="command-a-03-2025", api_key=get_cohere_api_key())
        
        # THE FIX: Create a detailed context string from all the new input fields.
        # This provides the AI with much more information to generate a better charter.
        project_details = f"""
        Project Title: {project_input.get('project_title')}
        Project Type: {project_input.get('project_type')}
        Project Description: {project_input.get('project_description')}
        Project Duration: {project_input.get('project_duration')}
        Budget Range: {project_input.get('budget_range')}
        Team Size: {project_input.get('team_size')}
        Key Stakeholders: {', '.join(project_input.get('key_stakeholders', []))}
        Project Objectives: {', '.join(project_input.get('project_objectives', []))}
        Constraints: {project_input.get('constraints')}
        Assumptions: {project_input.get('assumptions')}
        """
        
        # THE FIX: Update the prompt to use the new detailed context.
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a world-class PMP-certified project manager. Generate a comprehensive Project Charter based on the user's detailed input. You MUST include sections for objectives, scope, stakeholders, and a high-level timeline. Respond with a JSON object that strictly follows this format:\n{format_instructions}"),
            ("user", "Here is the project information:\n\n{details}"),
        ])
        
        chain = prompt | llm | parser
        
        # THE FIX: Invoke the chain with the new 'details' variable.
        charter_dict = chain.invoke({
            "details": project_details,
            "format_instructions": parser.get_format_instructions(),
        })

        current_docs = state.get("documents", {})
        current_docs["charter"] = charter_dict
        return {"documents": current_docs}

    except Exception as e:
        print(f"---FATAL ERROR in generate_charter_node: {e}---")
        raise e

def generate_scope_node(state: GraphState):
    """Generates scope data using a robust JSON parser with a retry mechanism."""
    print("---NODE: GENERATING SCOPE---")
    
    # THE FIX: Get the original project_input for the most accurate information.
    project_input = state["project_input"]
    charter_data = state.get("documents", {}).get("charter", {})
    parser = JsonOutputParser(pydantic_object=ScopeOutput)
    
    llm = ChatCohere(model="command-a-03-2025",
        api_key=get_cohere_api_key())
    
    # THE FIX: Create a detailed context for the scope statement.
    scope_context = f"""
    Project Title: {project_input.get('project_title')}
    Project Description: {project_input.get('project_description')}
    Project Objectives from Charter: {', '.join(charter_data.get('objectives', []))}
    User-defined Objectives: {', '.join(project_input.get('project_objectives', []))}
    Constraints: {project_input.get('constraints')}
    Assumptions: {project_input.get('assumptions')}
    """
    
    # THE FIX: Update the prompt to use the new detailed context.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior project analyst. Generate a complete Project Scope Statement based on the provided details. You MUST include a 'deliverables' list with at least 3 items, a section for 'in_scope' items, and a section for 'out_of_scope' items. Respond with a JSON object that strictly follows this format:\n{format_instructions}"),
        ("user", "Please generate the scope statement based on this information:\n\n{context}"),
    ])
    
    chain = prompt | llm | parser

    # THE FIX: Implement a retry loop to ensure deliverables are generated
    max_retries = 3
    for i in range(max_retries):
        print(f"---Attempt {i + 1} to generate scope...---")
        # THE FIX: Invoke the chain with the new 'context' variable.
        scope_dict = chain.invoke({
            "context": scope_context,
            "format_instructions": parser.get_format_instructions(),
        })
        
        # Check if the critical 'deliverables' key is present and not empty
        if scope_dict.get("deliverables"):
            print("---Successfully generated scope with deliverables.---")
            current_docs = state.get("documents", {})
            current_docs["scope"] = scope_dict
            return {"documents": current_docs}
        
        print(f"---WARNING: Attempt {i + 1} failed. 'deliverables' key is missing. Retrying...---")

    # If all retries fail, raise an error.
    raise ValueError("Failed to generate a valid scope statement with deliverables after multiple attempts.")