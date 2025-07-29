import json
import time
import re
from langchain_tavily import TavilySearch
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from state import GraphState, WBSOutput
from config import get_cohere_api_key

# --- Keep the existing prep functions ---
def prepare_for_next_deliverable_node(state: GraphState):
    """Pops the next deliverable from the list and sets it as current."""
    deliverables = list(state["deliverables_to_process"])
    next_deliverable = deliverables.pop(0)
    print(f"---NODE: PREPARING FOR '{next_deliverable}'---")
    return {
        "current_deliverable": next_deliverable,
        "deliverables_to_process": deliverables, 
    }

def setup_wbs_loop_node(state: GraphState):
    """Initializes the state for the WBS generation loop."""
    print("---NODE: SETTING UP WBS LOOP---")
    scope_data = state["documents"].get("scope")
    if not scope_data or not scope_data.get("deliverables"):
        raise ValueError("Scope with deliverables must be generated before WBS.")
    return {
        "deliverables_to_process": scope_data["deliverables"], 
        "wbs_accumulator": [] # Initialize the accumulator
    }

def should_continue_wbs_loop(state: GraphState):
    """Determines if the WBS generation loop should continue."""
    if state.get("deliverables_to_process"):
        print("---DECISION: Continue WBS Loop---")
        return "continue_loop"
    else:
        print("---DECISION: End WBS Loop---")
        return "end_loop"

# --- IMPROVED AI-POWERED WBS GENERATOR ---
def wbs_generation_agent(state: GraphState):
    """The agent that generates the WBS for a single deliverable using a robust JSON parser."""
    print(f"---NODE: WBS AGENT FOR DELIVERABLE: {state['current_deliverable']}---")
    
    # THE FIX: Define the JSON parser
    parser = JsonOutputParser(pydantic_object=WBSOutput)
    
    # THE FIX: Instantiate the LLM without the buggy .with_structured_output
    llm = ChatCohere(
        model="command-a-03-2025",
        api_key=get_cohere_api_key(),
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a master project planner. Generate a WBS with 2-4 main tasks for the given deliverable. Each task can have sub-tasks. Respond with a JSON object that strictly follows this format:\n{format_instructions}"),
        ("user", "Deliverable: '{deliverable}'"),
    ])
    
    # THE FIX: The chain now correctly uses the defined parser
    chain = prompt | llm | parser
    
    try:
        wbs_dict = chain.invoke({
            "deliverable": state["current_deliverable"],
            "format_instructions": parser.get_format_instructions(),
        })

        current_accumulator = state.get("wbs_accumulator", [])
        if wbs_dict.get("wbs_items"):
            current_accumulator.extend(wbs_dict["wbs_items"])
        
        return {"wbs_accumulator": current_accumulator}
    except Exception as e:
        print(f"---FATAL ERROR in wbs_generation_agent: {e}---")
        raise e

def compile_wbs_node(state: GraphState):
    """Compiles the generated WBS items into the final document structure."""
    print("---NODE: COMPILING FINAL WBS---")
    final_wbs_doc = {"wbs_items": state["wbs_accumulator"]}
    current_docs = state["documents"]
    current_docs["wbs"] = final_wbs_doc
    return {"documents": current_docs}