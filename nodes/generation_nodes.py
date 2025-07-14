import json
from ..state import GraphState, CharterOutput, ScopeOutput
from ..config import get_cohere_api_key
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a world-class PMP-certified project manager... Respond with a JSON object that strictly follows this format:\n{format_instructions}"),
            ("user", "Project Title: {title}\nProject Description: {description}"),
        ])
        
        chain = prompt | llm | parser
        
        charter_dict = chain.invoke({
            "title": project_input.get('project_title', 'Untitled Project'),
            "description": project_input.get('project_description', 'No description'),
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
    charter_data = state.get("documents", {}).get("charter", {})
    parser = JsonOutputParser(pydantic_object=ScopeOutput)
    
    llm = ChatCohere(model="command-a-03-2025",
        api_key=get_cohere_api_key())
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior project analyst. Generate a complete Project Scope Statement. You MUST include a 'deliverables' list with at least 3 items. Respond with a JSON object that strictly follows this format:\n{format_instructions}"),
        ("user", "Project Title: {title}\nObjectives: {objectives}"),
    ])
    
    chain = prompt | llm | parser

    # THE FIX: Implement a retry loop to ensure deliverables are generated
    max_retries = 3
    for i in range(max_retries):
        print(f"---Attempt {i + 1} to generate scope...---")
        scope_dict = chain.invoke({
            "title": charter_data.get('project_title', 'Untitled Project'),
            "objectives": ", ".join(charter_data.get('objectives', [])),
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