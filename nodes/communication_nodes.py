from ..state import GraphState, CommunicationPlanOutput
from ..config import get_cohere_api_key
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

def generate_communication_plan_node(state: GraphState):
    """Generates a project communication plan based on the stakeholder analysis."""
    print("---NODE: GENERATING COMMUNICATION PLAN---")
    
    # THE FIX: Use dictionary .get() method to safely access nested data.
    documents = state.get("documents", {})
    stakeholder_analysis = documents.get("stakeholder-analysis", {})
    
    if not stakeholder_analysis or not stakeholder_analysis.get("stakeholders"):
        print("---WARNING: No stakeholder analysis found. Skipping communication plan.---")
        current_docs = state.get("documents", {})
        current_docs["communication-plan"] = {"communications": []}
        return {"documents": current_docs}

    parser = JsonOutputParser(pydantic_object=CommunicationPlanOutput)
    llm = ChatCohere(model="command-a-03-2025", api_key=get_cohere_api_key())

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a project communications expert. Based on the provided stakeholder analysis, create a tailored communication plan. The plan should detail what, how, and when to communicate with each stakeholder. Respond with a JSON object that strictly follows this format:\n{format_instructions}"),
        ("user", "Here is the stakeholder analysis:\n\n{stakeholder_data}"),
    ])
    
    chain = prompt | llm | parser

    try:
        stakeholder_data_str = json.dumps(stakeholder_analysis.get("stakeholders", []), indent=2)

        plan_dict = chain.invoke({
            "stakeholder_data": stakeholder_data_str,
            "format_instructions": parser.get_format_instructions(),
        })

        current_docs = state.get("documents", {})
        current_docs["communication-plan"] = plan_dict
        print("---NODE: COMMUNICATION PLAN COMPLETE---")
        return {"documents": current_docs}
        
    except Exception as e:
        print(f"---FATAL ERROR in generate_communication_plan_node: {e}---")
        raise e