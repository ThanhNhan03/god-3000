from llm_client import generate_response
import json

async def convert_module(module_data: dict, error_context: dict = None):
    """
    Calls LLM to convert the module.
    """
    prompt = f"""
    Convert the following VB module and associated COBOL to .NET MVC.
    Module Info: {json.dumps(module_data)}
    Error Context (if any): {json.dumps(error_context) if error_context else 'None'}
    
    Please provide the output as a JSON list of files with 'path' and 'content'.
    """
    
    system = "You are an expert legacy code migration assistant. Return valid JSON only matching the schema."
    
    # Simulate API call for speed, or call the real thing:
    # response = await generate_response(prompt, system)
    # return response.content[0].text
    
    # Stub response
    return {
        "files": [
            {"path": f"Controllers/{module_data.get('form', 'Default')}Controller.cs", "content": "// Generated C# Controller"},
            {"path": f"Views/{module_data.get('form', 'Default')}/Index.cshtml", "content": "<!-- Generated View -->"}
        ]
    }
