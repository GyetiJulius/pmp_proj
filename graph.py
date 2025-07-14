from langgraph.graph import StateGraph, END
from .state import GraphState

from .nodes.generation_nodes import generate_charter_node, generate_scope_node
from .nodes.wbs_nodes import (
    setup_wbs_loop_node,
    prepare_for_next_deliverable_node,
    wbs_generation_agent,
    compile_wbs_node,
    should_continue_wbs_loop, # Import the decision function
)
from .nodes.risk_nodes import generate_risk_register_node
from .nodes.schedule_nodes import generate_schedule_node

def build_graph():
    """Builds and compiles the agentic workflow graph."""
    workflow = StateGraph(GraphState)
    
    workflow.add_node("generate_charter", generate_charter_node)
    workflow.add_node("generate_scope", generate_scope_node)
    workflow.add_node("setup_wbs_loop", setup_wbs_loop_node)
    workflow.add_node("prepare_for_next_deliverable", prepare_for_next_deliverable_node)
    workflow.add_node("wbs_generation_agent", wbs_generation_agent)
    workflow.add_node("compile_wbs", compile_wbs_node)
    workflow.add_node("generate_risk_register", generate_risk_register_node)
    workflow.add_node("generate_schedule", generate_schedule_node)
    
    workflow.set_entry_point("generate_charter")
    workflow.add_edge("generate_charter", "generate_scope")
    workflow.add_edge("generate_scope", "setup_wbs_loop")
    
    # THE FIX: Corrected graph routing logic for the WBS loop
    workflow.add_conditional_edges(
        "setup_wbs_loop",
        should_continue_wbs_loop,
        {"continue_loop": "prepare_for_next_deliverable", "end_loop": "compile_wbs"}
    )
    
    workflow.add_edge("prepare_for_next_deliverable", "wbs_generation_agent")
    # After an agent runs, go back to the decision point
    workflow.add_conditional_edges(
        "wbs_generation_agent", # <-- The agent decides when to loop again
        should_continue_wbs_loop,
        {"continue_loop": "prepare_for_next_deliverable", "end_loop": "compile_wbs"}
    )
    
    # THE CRITICAL FIX: Remove the direct edge from compile_wbs to END 
    # Instead, connect compile_wbs to generate_risk_register
    workflow.add_edge("compile_wbs", "generate_risk_register")
    workflow.add_edge("generate_risk_register", "generate_schedule") # Connect risk to schedule
    workflow.add_edge("generate_schedule", END) # Connect schedule to the end
    
    return workflow.compile()

# Compile the graph for the application to use
app_graph = build_graph()