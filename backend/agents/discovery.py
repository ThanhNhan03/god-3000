import os

def discover_modules(workspace_path: str):
    """
    Simulates Discovery Worker analyzing VB and COBOL files.
    """
    modules = []
    
    # Fake logic: just list files in directory
    try:
        files = os.listdir(workspace_path)
    except FileNotFoundError:
        files = []
        
    cobol_files = [f for f in files if f.endswith(('.cbl', '.cpy'))]
    vb_files = [f for f in files if f.endswith(('.frm', '.bas', '.cls'))]
    
    # Bundle them into a fake module
    if vb_files:
        modules.append({
            "form": vb_files[0],
            "cobol_programs": cobol_files,
            "complexity_score": 0.8
        })
        
    return {
        "modules": modules,
        "migration_order": [m["form"] for m in modules]
    }
