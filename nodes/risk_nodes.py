import json
import time
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate

from state import GraphState
from config import get_cohere_api_key, get_tavily_api_key

def generate_risk_register_node(state: GraphState):
    """
    Generates a comprehensive risk register based on the project scope and WBS.
    """
    print("---NODE: GENERATING RISK REGISTER---")
    
    # FIX: Get project data from the nested 'project_input' dictionary
    project_input = state.get("project_input", {})
    project_name = project_input.get("project_title", "Project")
    project_description = project_input.get("project_description", "")
    
    # Extract deliverables from WBS for risk analysis
    wbs_data = state["documents"].get("wbs", {})
    wbs_items = wbs_data.get("wbs_items", [])
    deliverables = [item.get("task_name", "") for item in wbs_items]
    
    # Research common project risks
    print("---STEP 1: Researching common project risks---")
    try:
        search_tool = TavilySearchResults(max_results=3, api_key=get_tavily_api_key())
        search_query = f"common project risks and mitigation strategies for {project_name}"
        research_results = "\n\n".join(search_tool.invoke(search_query))
    except Exception as e:
        print(f"---WARNING: Risk research failed. Error: {e}")
        research_results = "Research unavailable."
    
    # Generate the risk register
    print("---STEP 2: Generating risk register---")
    llm = ChatCohere(
        model="command-a-03-2025",
        api_key=get_cohere_api_key()
    )
    
    risk_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a PMP-certified project manager with expertise in risk management.
Your task is to create a comprehensive risk register for the project based on its description, deliverables, and research.

For each risk:
1. Provide a specific risk description (not generic)
2. Assess probability as High, Medium, or Low
3. Assess impact as High, Medium, or Low
4. Recommend a response strategy (Avoid, Transfer, Mitigate, or Accept)
5. Assign an owner (typically Project Manager, Technical Lead, or Stakeholder)

Generate at least 5 project-specific risks covering different categories:
- Technical risks
- Schedule risks
- Resource risks
- Scope risks
- Stakeholder risks
- External risks

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:

RISK 1:
Description: [Detailed risk description]
Probability: [High/Medium/Low]
Impact: [High/Medium/Low]
Response Strategy: [Strategy with brief explanation]
Owner: [Role responsible]

RISK 2:
Description: [Detailed risk description]
Probability: [High/Medium/Low]
Impact: [High/Medium/Low]
Response Strategy: [Strategy with brief explanation]
Owner: [Role responsible]

... and so on for at least 5 risks."""),
        
        ("user", """Create a risk register for the following project:

PROJECT NAME:
{project_name}

PROJECT DESCRIPTION:
{description}

KEY DELIVERABLES:
{deliverables}

RESEARCH ON COMMON RISKS:
{research}""")
    ])
    
    try:
        chain = risk_prompt | llm
        risk_text_response = chain.invoke({
            "project_name": project_name,
            "description": project_description,
            "deliverables": "\n".join([f"- {d}" for d in deliverables]),
            "research": research_results
        })
        
        risk_text = risk_text_response.content
        print(f"---INFO: Raw risk text generated---")
        
        # Parse the risk text into structured format
        risk_items = parse_risk_text(risk_text) # This will now call the robust parser
        
        # Create the risk register document and add to documents
        current_docs = state["documents"]
        current_docs["risk-register"] = {"risks": risk_items}
        
        print("---NODE: RISK REGISTER GENERATION COMPLETE---")
        return {"documents": current_docs}
        
    except Exception as e:
        print(f"---ERROR: Risk generation failed: {str(e)}. Using fallback.---")
        # Create a fallback risk register
        fallback_risks = [
            {
                "risk_description": "Project scope may expand beyond initial requirements, leading to schedule delays.",
                "probability": "Medium",
                "impact": "High",
                "response_strategy": "Mitigate: Implement strict change control process.",
                "owner": "Project Manager"
            },
            {
                "risk_description": "Technical challenges in implementation may arise.",
                "probability": "High",
                "impact": "Medium", 
                "response_strategy": "Mitigate: Conduct early prototyping and testing.",
                "owner": "Technical Lead"
            }
        ]
        
        risk_register = {"risks": fallback_risks}
        current_docs = state["documents"]
        current_docs["risk-register"] = risk_register # FIX: Use hyphenated key
        
        print("---NODE: RISK REGISTER FALLBACK COMPLETE---")
        return {"documents": current_docs}

def parse_risk_text(risk_text):
    """
    A robust parser for AI-generated risk register text.
    It handles variations in formatting and structure.
    """
    print("---PARSER: Parsing risk text---")
    risks = []
    
    # Split the entire text into chunks, where each chunk represents one risk
    # This is robust against extra newlines between risks.
    risk_chunks = risk_text.strip().split("RISK ")
    
    for chunk in risk_chunks:
        if not chunk.strip():
            continue

        current_risk = {}
        # Process each line within the chunk
        for line in chunk.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Use 'if/elif' to find the first match for a keyword on a line
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if 'description' in key:
                    current_risk["risk_description"] = value
                elif 'probability' in key:
                    current_risk["probability"] = value
                elif 'impact' in key:
                    current_risk["impact"] = value
                elif 'response strategy' in key:
                    current_risk["response_strategy"] = value
                elif 'owner' in key:
                    current_risk["owner"] = value

        # Add the completed risk to our list if it's valid
        if "risk_description" in current_risk:
            risks.append(current_risk)
    
    # If parsing failed, return a minimal set of risks
    if not risks:
        print("---WARNING: Could not parse risks, creating fallback---")
        risks = [
            {
                "risk_description": "Project scope may expand beyond initial requirements.",
                "probability": "Medium",
                "impact": "High",
                "response_strategy": "Mitigate: Implement strict change control process.",
                "owner": "Project Manager"
            }
        ]
    
    print(f"---PARSER: Parsed {len(risks)} risks successfully---")
    return risks
