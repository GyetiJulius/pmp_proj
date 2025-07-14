from ..state import GraphState, StakeholderAnalysisOutput
from ..config import get_cohere_api_key
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

def generate_stakeholder_analysis_node(state: GraphState):
    """Generates a detailed stakeholder analysis."""
    print("---NODE: GENERATING STAKEHOLDER ANALYSIS---")
    
    charter_data = state.get("documents", {}).get("charter", {})
    stakeholder_names = charter_data.get("stakeholders")

    if not stakeholder_names:
        print("---WARNING: No stakeholders found in charter. Skipping analysis.---")
        # Create an empty analysis to avoid downstream errors
        current_docs = state.get("documents", {})
        current_docs["stakeholder-analysis"] = {"stakeholders": []}
        return {"documents": current_docs}

    parser = JsonOutputParser(pydantic_object=StakeholderAnalysisOutput)
    llm = ChatCohere(model="command-r-plus", api_key=get_cohere_api_key())

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior project manager specializing in stakeholder relations. For the given list of stakeholders, create a detailed analysis. For each stakeholder, you must infer their likely role, interest, influence level, and a suitable engagement strategy. Respond with a JSON object that strictly follows this format:\n{format_instructions}"),
        ("user", "Analyze the following stakeholders for the project '{project_title}':\n\n- {stakeholders_list}"),
    ])
    
    chain = prompt | llm | parser

    try:
        analysis_dict = chain.invoke({
            "project_title": charter_data.get("project_title", "the project"),
            "stakeholders_list": "\n- ".join(stakeholder_names),
            "format_instructions": parser.get_format_instructions(),
        })

        current_docs = state.get("documents", {})
        current_docs["stakeholder-analysis"] = analysis_dict
        print("---NODE: STAKEHOLDER ANALYSIS COMPLETE---")
        return {"documents": current_docs}
        
    except Exception as e:
        print(f"---FATAL ERROR in generate_stakeholder_analysis_node: {e}---")
        raise e