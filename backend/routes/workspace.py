import io
import os
import shutil
import zipfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse, Response
from pydantic import BaseModel

router = APIRouter()
WORKSPACE_ROOT = "/Users/lilnhan/Documents/GitHub/god-3000/workspace"

def get_tree(path):
    tree = []
    if not os.path.exists(path):
        return tree
    
    for item in sorted(os.listdir(path)):
        # Skip hidden files like .DS_Store
        if item.startswith('.'):
            continue
            
        full_path = os.path.join(path, item)
        rel_path = os.path.relpath(full_path, WORKSPACE_ROOT)
        # Normalize slashes for FE
        rel_path = rel_path.replace("\\", "/")
        is_dir = os.path.isdir(full_path)
        
        node = {
            "name": item,
            "type": "folder" if is_dir else "file",
            "path": rel_path
        }
        
        if is_dir:
            node["children"] = get_tree(full_path)
            
        tree.append(node)
    return tree

@router.get("/files")
async def get_files():
    return get_tree(WORKSPACE_ROOT)

@router.get("/file")
async def get_file(path: str):
    full_path = os.path.join(WORKSPACE_ROOT, path)
    # Basic security check
    if not os.path.abspath(full_path).startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise HTTPException(status_code=403, detail="Invalid path")
        
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="Path is a directory")
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return PlainTextResponse(f.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

SOURCE_DIR = os.path.join(WORKSPACE_ROOT, "source")
OUTPUT_DIR = os.path.join(WORKSPACE_ROOT, "new")

@router.post("/reset")
async def reset_workspace():
    """
    Clear ONLY the /new/ output folder — source files are preserved.
    This is called before each upload so user can add new files without
    losing their demo/source files.
    """
    try:
        if os.path.exists(WORKSPACE_ROOT):
            for item in os.listdir(WORKSPACE_ROOT):
                if item == "source":
                    continue
                item_path = os.path.join(WORKSPACE_ROOT, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                    
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        return {"message": "Output and loose files cleared. Source folder preserved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-all")
async def reset_all():
    """
    Full wipe of workspace including source files.
    Only use when user explicitly wants a clean slate.
    """
    try:
        if os.path.exists(WORKSPACE_ROOT):
            for item in os.listdir(WORKSPACE_ROOT):
                item_path = os.path.join(WORKSPACE_ROOT, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        
        # Recreate essential empty folders so the UI tree has them
        os.makedirs(os.path.join(WORKSPACE_ROOT, "source"), exist_ok=True)
        os.makedirs(os.path.join(WORKSPACE_ROOT, "new"), exist_ok=True)
        
        return {"message": "Full workspace reset successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateItemReq(BaseModel):
    path: str
    type: str

@router.post("/create")
async def create_item(req: CreateItemReq):
    full_path = os.path.join(WORKSPACE_ROOT, req.path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise HTTPException(status_code=403, detail="Invalid path")
        
    try:
        if req.type == "folder":
            os.makedirs(full_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write("")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SaveFileReq(BaseModel):
    path: str
    content: str

@router.post("/save")
async def save_file(req: SaveFileReq):
    """Save editor content back to the file on disk."""
    full_path = os.path.join(WORKSPACE_ROOT, req.path)
    # Security: must stay within workspace
    if not os.path.abspath(full_path).startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise HTTPException(status_code=403, detail="Invalid path")
    if os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="Path is a directory")
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(req.content)
        return {"status": "ok", "path": req.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_report(path: str):
    """Serve a generated report.html with correct HTML content-type."""
    full_path = os.path.join(WORKSPACE_ROOT, path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise HTTPException(status_code=403, detail="Invalid path")
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download")
async def download_module(module: str):
    """
    Zip the entire output folder for a module and return as a downloadable ZIP.
    GET /api/workspace/download?module=frmInvoice.frm
    """
    module_dir = os.path.join(OUTPUT_DIR, module)
    if not os.path.isdir(module_dir):
        raise HTTPException(status_code=404, detail=f"Module folder not found: {module}")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(module_dir):
            for fname in files:
                full = os.path.join(root, fname)
                # arcname: relative to the module_dir's parent (workspace/new/)
                arcname = os.path.relpath(full, os.path.dirname(module_dir))
                zf.write(full, arcname)

    buf.seek(0)
    safe_name = module.replace(".", "_").replace(" ", "_")
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_project.zip"'},
    )
