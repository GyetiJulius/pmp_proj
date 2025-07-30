from langgraph.graph import StateGraph, END
from nodes.schedule_nodes import generate_schedule_node

from nodes.generation_nodes import generate_charter_node, generate_scope_node
from nodes.wbs_nodes import (
    setup_wbs_loop_node,
    prepare_for_next_deliverable_node,
    wbs_generation_agent,
    compile_wbs_node,
    should_continue_wbs_loop,
)
from state import GraphState
from nodes.stakeholder_nodes import generate_stakeholder_analysis_node
from nodes.risk_nodes import generate_risk_register_node
from nodes.communication_nodes import generate_communication_plan_node

def build_graph():
    """Builds and compiles the agentic workflow graph with a correct WBS loop."""
    workflow = StateGraph(GraphState)
    
    # Add all nodes to the graph
    workflow.add_node("generate_charter", generate_charter_node)
    workflow.add_node("generate_scope", generate_scope_node)
    workflow.add_node("setup_wbs_loop", setup_wbs_loop_node)
    workflow.add_node("prepare_for_next_deliverable", prepare_for_next_deliverable_node)
    workflow.add_node("wbs_generation_agent", wbs_generation_agent)
    workflow.add_node("compile_wbs", compile_wbs_node)
    workflow.add_node("generate_risk_register", generate_risk_register_node)
    workflow.add_node("generate_schedule", generate_schedule_node)
    workflow.add_node("generate_stakeholder_analysis", generate_stakeholder_analysis_node)
    workflow.add_node("generate_communication_plan", generate_communication_plan_node)
    
    # Set up the graph flow and edges
    workflow.set_entry_point("generate_charter")
    workflow.add_edge("generate_charter", "generate_scope")
    workflow.add_edge("generate_scope", "setup_wbs_loop")
    
    # THE FIX: The loop is now structured correctly
    # 1. After setup, we go to the conditional check.
    workflow.add_conditional_edges(
        "setup_wbs_loop",
        should_continue_wbs_loop,
        {
            "continue_loop": "prepare_for_next_deliverable",
            "end_loop": "compile_wbs"
        }
    )
    
    # 2. The processing steps run in sequence.
    workflow.add_edge("prepare_for_next_deliverable", "wbs_generation_agent")
    
    # 3. After processing, we go BACK to the conditional check, NOT the setup node.
    # This is the critical change that prevents the infinite loop.
    workflow.add_conditional_edges(
        "wbs_generation_agent",
        should_continue_wbs_loop,
        {
            "continue_loop": "prepare_for_next_deliverable",
            "end_loop": "compile_wbs"
        }
    )
    
    # The rest of the graph
    workflow.add_edge("compile_wbs", "generate_risk_register")
    workflow.add_edge("generate_risk_register", "generate_schedule")
    workflow.add_edge("generate_schedule", "generate_stakeholder_analysis")
    workflow.add_edge("generate_stakeholder_analysis", "generate_communication_plan")
    workflow.add_edge("generate_communication_plan", END)
    
    return workflow.compile()

app_graph = build_graph()