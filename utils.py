import os
from docxtpl import DocxTemplate

def create_docx_file(project_input: dict, doc_type: str, generated_data: dict):
    """Creates a .docx file on demand from a template and context."""
    print(f"---ONDEMAND: CREATING {doc_type.upper()} DOCX---")
    
    # Use os.path.dirname(__file__) to get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, 'templates', f"{doc_type}_template.docx")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    doc = DocxTemplate(template_path)
    context = {"project_title": project_input.get('project_title'), **generated_data}
    doc.render(context)
    
    output_dir = os.path.join(script_dir, "generated_docs")
    os.makedirs(output_dir, exist_ok=True)
    
    file_name = f"{project_input.get('project_title', 'project').replace(' ', '_')}_{doc_type.capitalize()}.docx"
    file_path = os.path.join(output_dir, file_name)
    
    doc.save(file_path)
    return file_path