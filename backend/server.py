# backend/server.py
import os
import json
import asyncio
from fastapi import FastAPI, Response, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.samples import SAMPLE_FILES, MODULE_RUNS

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Ensure workspace and frontend directories exist
os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(os.path.join(WORKSPACE_DIR, "source"), exist_ok=True)
os.makedirs(os.path.join(WORKSPACE_DIR, "output"), exist_ok=True)

# State to store active simulation status and custom files
class SimulationState:
    def __init__(self):
        self.is_running = False
        self.current_event_queue = asyncio.Queue()

sim_state = SimulationState()

def initialize_workspace():
    # Write initial legacy files to source directory
    for path, content in SAMPLE_FILES.items():
        if path.startswith("source/"):
            full_path = os.path.join(WORKSPACE_DIR, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    # Clear output directory on start
    output_dir = os.path.join(WORKSPACE_DIR, "output")
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        if os.path.isfile(file_path):
            os.unlink(file_path)

initialize_workspace()

# API to list workspace files recursively
@app.get("/api/workspace/files")
def list_workspace_files():
    files_tree = []
    
    def scan_dir(base_path, parent_rel=""):
        items = []
        for name in os.listdir(base_path):
            full_path = os.path.join(base_path, name)
            rel_path = os.path.join(parent_rel, name).replace("\\", "/")
            if os.path.isdir(full_path):
                items.append({
                    "name": name,
                    "type": "directory",
                    "path": rel_path,
                    "children": scan_dir(full_path, rel_path)
                })
            else:
                items.append({
                    "name": name,
                    "type": "file",
                    "path": rel_path
                })
        return sorted(items, key=lambda x: (x["type"] == "file", x["name"]))

    if os.path.exists(WORKSPACE_DIR):
        files_tree = scan_dir(WORKSPACE_DIR)
    
    return files_tree

class FileContentRequest(BaseModel):
    path: str

@app.get("/api/workspace/file")
def get_file(path: str):
    full_path = os.path.join(WORKSPACE_DIR, path)
    if not os.path.exists(full_path) or os.path.isdir(full_path):
        return {"content": "", "error": "File not found"}
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        return {"content": "", "error": str(e)}

class SaveFileRequest(BaseModel):
    path: str
    content: str

@app.post("/api/workspace/save")
def save_file(req: SaveFileRequest):
    full_path = os.path.join(WORKSPACE_DIR, req.path)
    # Don't let users write outside workspace
    if not os.path.abspath(full_path).startswith(WORKSPACE_DIR):
        return {"success": False, "error": "Access denied"}
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/workspace/reset")
def reset_workspace():
    initialize_workspace()
    return {"status": "success"}

# SSE stream logic simulating Orchestrator and Workers
async def sse_generator():
    # Wait list of events to stream
    events = []
    
    # helper to format SSE message
    def make_event(event_type, **kwargs):
        payload = {"type": event_type}
        payload.update(kwargs)
        return f"data: {json.dumps(payload)}\n\n"

    # Stage 1: Orchestrator initialization
    events.append(make_event("text_delta", content="### Orchestrator Agent\nInitializing migration process... Ingesting workspace files from `/workspace/source`.\n"))
    events.append(make_event("thinking_delta", content="Scanning filesystem structure...\nResolving active file paths:\n- `source/frmInvoice.frm`\n- `source/INVOICE.cbl`\n- `source/frmCustomer.frm`\n- `source/billing_proc.cbl`\n"))
    await asyncio.sleep(1.0)
    
    # Initialize dashboard list
    events.append(make_event("module_status", module="frmCustomer.frm", status="pending", retry_count=0))
    events.append(make_event("module_status", module="frmInvoice.frm", status="pending", retry_count=0))
    events.append(make_event("module_status", module="billing_proc.cbl", status="pending", retry_count=0))
    
    # Discovery phase
    events.append(make_event("thinking_delta", content="Invoking `discovery_worker` to map references and dependency tree...\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("text_delta", content="### Discovery Phase Complete\nDetected 3 key migration modules:\n\n1. **frmCustomer.frm** (Low complexity)\n   - VB Form dealing with local profile operations.\n   - No COBOL dependencies.\n2. **frmInvoice.frm** (Medium-High complexity)\n   - Intersects with **INVOICE.cbl** via linkage section.\n   - Relies on packed-decimal (`COMP-3`) precision computation.\n3. **billing_proc.cbl** (High complexity)\n   - Large standalone COBOL routine dealing with REDEFINES records.\n\n*Proposed order of migration: Customer Profile -> Invoice Calculation -> Billing Process*\n\n"))
    await asyncio.sleep(1.0)

    # --- MODULE 1: Customer Module ---
    events.append(make_event("module_status", module="frmCustomer.frm", status="converting", retry_count=0))
    events.append(make_event("thinking_delta", content="[conversion_worker] Parsing `frmCustomer.frm` controls and events...\nGenerating .NET MVC structures: `CustomerController.cs`, `CustomerViewModel.cs`.\nMapping UI event handlers to controller actions.\n"))
    await asyncio.sleep(2.0)
    
    # Write Customer Controller files to real filesystem so user can view
    cust_ctrl = """using Microsoft.AspNetCore.Mvc;

namespace LegacyMigration.Controllers
{
    public class CustomerController : Controller
    {
        [HttpGet]
        public IActionResult Index()
        {
            return View(new CustomerViewModel());
        }

        [HttpPost]
        public IActionResult Save(CustomerViewModel model)
        {
            if (ModelState.IsValid)
            {
                // Simulated DB write
                model.Message = "Customer data successfully saved!";
                model.IsSuccess = true;
            }
            return View("Index", model);
        }
    }
}
"""
    cust_vm = """namespace LegacyMigration.Controllers
{
    public class CustomerViewModel
    {
        public string CustomerId { get; set; }
        public string Name { get; set; }
        public string Message { get; set; }
        public bool IsSuccess { get; set; }
    }
}
"""
    # Write physical files
    with open(os.path.join(WORKSPACE_DIR, "output", "CustomerController.cs"), "w", encoding="utf-8") as f:
        f.write(cust_ctrl)
    with open(os.path.join(WORKSPACE_DIR, "output", "CustomerViewModel.cs"), "w", encoding="utf-8") as f:
        f.write(cust_vm)
        
    events.append(make_event("file_update", path="output/CustomerController.cs", content=cust_ctrl))
    events.append(make_event("file_update", path="output/CustomerViewModel.cs", content=cust_vm))
    events.append(make_event("text_delta", content="**[Conversion Worker]** Generated MVC controller and model structures for Customer Profile.\n"))
    
    events.append(make_event("module_status", module="frmCustomer.frm", status="validating", retry_count=0))
    events.append(make_event("thinking_delta", content="[test_gen_worker] Generating xUnit validation scenarios from original VB logic...\n[build_validate_worker] Launching build container...\nRunning `dotnet restore`...\nRunning `dotnet build`...\nRunning `dotnet test`...\n"))
    await asyncio.sleep(2.0)
    
    events.append(make_event("build_result", module="frmCustomer.frm", status="success"))
    events.append(make_event("test_result", module="frmCustomer.frm", test_name="Test_Load_Customer_Profile", status="pass"))
    events.append(make_event("test_result", module="frmCustomer.frm", test_name="Test_Save_Customer_Profile", status="pass"))
    events.append(make_event("confidence_score", module="frmCustomer.frm", score=0.98))
    events.append(make_event("module_status", module="frmCustomer.frm", status="done", retry_count=0))
    events.append(make_event("text_delta", content="**[Build Validate Worker]** customer_profile build succeeded. All 2 tests passed. Confidence Score: **98%**.\n\n"))
    await asyncio.sleep(1.0)

    # --- MODULE 2: Invoice Module (with 2 failure retries) ---
    events.append(make_event("module_status", module="frmInvoice.frm", status="converting", retry_count=0))
    events.append(make_event("thinking_delta", content="[conversion_worker] Analyzing `frmInvoice.frm` interop dependencies...\nLinking to COBOL layout `INVOICE.cbl`.\nGenerating controller actions and viewModel bindings.\n"))
    await asyncio.sleep(2.0)
    
    # Write Initial Invoice files
    with open(os.path.join(WORKSPACE_DIR, "output", "InvoiceController.cs"), "w", encoding="utf-8") as f:
        f.write(SAMPLE_FILES["output/InvoiceController.cs"])
    with open(os.path.join(WORKSPACE_DIR, "output", "InvoiceViewModel.cs"), "w", encoding="utf-8") as f:
        f.write(SAMPLE_FILES["output/InvoiceViewModel.cs"])
    with open(os.path.join(WORKSPACE_DIR, "output", "InvoiceTests.cs"), "w", encoding="utf-8") as f:
        f.write(SAMPLE_FILES["output/InvoiceTests.cs"])

    events.append(make_event("file_update", path="output/InvoiceController.cs", content=SAMPLE_FILES["output/InvoiceController.cs"]))
    events.append(make_event("file_update", path="output/InvoiceViewModel.cs", content=SAMPLE_FILES["output/InvoiceViewModel.cs"]))
    events.append(make_event("file_update", path="output/InvoiceTests.cs", content=SAMPLE_FILES["output/InvoiceTests.cs"]))
    events.append(make_event("text_delta", content="**[Conversion Worker]** Generated MVC layout and test cases for Invoice module. Proceeding to build validation.\n"))
    
    events.append(make_event("module_status", module="frmInvoice.frm", status="validating", retry_count=0))
    events.append(make_event("thinking_delta", content="[build_validate_worker] Sandbox run starting...\nExecuting compile compiler checks...\n"))
    await asyncio.sleep(1.5)
    
    # Emit Build Fail (CS0246)
    events.append(make_event("build_result", module="frmInvoice.frm", status="fail", errors=[
        "InvoiceController.cs(11,26): error CS0246: The type or namespace name 'ICobolInterop' could not be found (are you missing a using directive or an assembly reference?)"
    ]))
    events.append(make_event("thinking_delta", content="[qa_review_worker] Build failed. Initiating post-mortem parsing...\nAnalyzing error context code symbols...\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("diff_report", module="frmInvoice.frm", category="compile", summary="Missing ICobolInterop interface mapping in C# workspace."))
    
    # Retry 1
    events.append(make_event("module_status", module="frmInvoice.frm", status="converting", retry_count=1))
    events.append(make_event("thinking_delta", content="[conversion_worker] Incorporating QA review recommendations (adding ICobolInterop interface).\nGenerating interface specification file `ICobolInterop.cs`.\n"))
    await asyncio.sleep(1.5)
    
    icobol_interop_code = """namespace LegacyMigration.Controllers
{
    public interface ICobolInterop
    {
        decimal CalculateInvoiceVAT(decimal subtotal, decimal vatRate);
    }
}
"""
    with open(os.path.join(WORKSPACE_DIR, "output", "ICobolInterop.cs"), "w", encoding="utf-8") as f:
        f.write(icobol_interop_code)
    events.append(make_event("file_update", path="output/ICobolInterop.cs", content=icobol_interop_code))
    
    events.append(make_event("module_status", module="frmInvoice.frm", status="validating", retry_count=1))
    events.append(make_event("thinking_delta", content="[build_validate_worker] Re-triggering compilation...\nBuilding assembly...\nRunning test cases...\n"))
    await asyncio.sleep(1.5)
    
    events.append(make_event("build_result", module="frmInvoice.frm", status="success"))
    events.append(make_event("test_result", module="frmInvoice.frm", test_name="Test_VAT_Calculation_Success", status="fail", message="Assert.Equal() Failure. Expected: 1650.00, Actual: 1500.00"))
    
    events.append(make_event("thinking_delta", content="[qa_review_worker] Tests failed. Performing structural and behavioral analysis...\nComparing runtime outputs: VB double returned 1650.00, but converted decimal returns 1500.00.\nFound math calculation logic error in custom interop helper (VAT computation omitted).\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("diff_report", module="frmInvoice.frm", category="logic", summary="VAT calculation logic is missing the multiplication operand in the generated interop code."))
    
    # Retry 2
    events.append(make_event("module_status", module="frmInvoice.frm", status="converting", retry_count=2))
    events.append(make_event("thinking_delta", content="[conversion_worker] Refining math definitions in `CobolInterop.cs`...\nApplying packed decimal scale parameters.\n"))
    await asyncio.sleep(1.5)
    
    cobol_interop_code = """namespace LegacyMigration.Controllers
{
    public class CobolInterop : ICobolInterop
    {
        public decimal CalculateInvoiceVAT(decimal subtotal, decimal vatRate)
        {
            // Replicating COMP-3 packed decimal logic with exact rounding
            decimal vatAmount = decimal.Round(subtotal * vatRate, 2, System.MidpointRounding.AwayFromZero);
            return subtotal + vatAmount;
        }
    }
}
"""
    with open(os.path.join(WORKSPACE_DIR, "output", "CobolInterop.cs"), "w", encoding="utf-8") as f:
        f.write(cobol_interop_code)
    events.append(make_event("file_update", path="output/CobolInterop.cs", content=cobol_interop_code))
    
    events.append(make_event("module_status", module="frmInvoice.frm", status="validating", retry_count=2))
    events.append(make_event("thinking_delta", content="[build_validate_worker] Re-compiling and executing tests...\n"))
    await asyncio.sleep(1.5)
    
    events.append(make_event("build_result", module="frmInvoice.frm", status="success"))
    events.append(make_event("test_result", module="frmInvoice.frm", test_name="Test_VAT_Calculation_Success", status="pass"))
    events.append(make_event("confidence_score", module="frmInvoice.frm", score=0.94))
    events.append(make_event("module_status", module="frmInvoice.frm", status="done", retry_count=2))
    events.append(make_event("text_delta", content="**[Build Validate Worker]** Invoice module compiled successfully and passed all calculations. Confidence Score: **94%** (after 2 retries).\n\n"))
    await asyncio.sleep(1.0)

    # --- MODULE 3: Billing Process (Escalated after max retries) ---
    events.append(make_event("module_status", module="billing_proc.cbl", status="converting", retry_count=0))
    events.append(make_event("thinking_delta", content="[conversion_worker] Translating COBOL batch process: `billing_proc.cbl`...\nDetecting complex COBOL structures: REDEFINES, 88-level status checks.\n"))
    await asyncio.sleep(2.0)
    
    billing_proc_code = """using System;
using System.Runtime.InteropServices;

namespace LegacyMigration.Batch
{
    // High-performance interop struct
    [StructLayout(LayoutKind.Sequential, Pack=1)]
    public class BillingProcessor
    {
        // Simplistic conversion lacking memory overlays
        public string RecordType { get; set; }
        public decimal Amount { get; set; }
    }
}
"""
    with open(os.path.join(WORKSPACE_DIR, "output", "BillingProcessor.cs"), "w", encoding="utf-8") as f:
        f.write(billing_proc_code)
    events.append(make_event("file_update", path="output/BillingProcessor.cs", content=billing_proc_code))
    events.append(make_event("text_delta", content="**[Conversion Worker]** Generated class mapping for Billing Processor. Running validation.\n"))
    
    # Retry 0 Build Fail
    events.append(make_event("module_status", module="billing_proc.cbl", status="validating", retry_count=0))
    events.append(make_event("thinking_delta", content="[build_validate_worker] Compiling batch modules...\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("build_result", module="billing_proc.cbl", status="fail", errors=[
        "BillingProcessor.cs(44,18): error CS0103: The name 'REDEFINES_BillingBlock' does not exist in the current context."
    ]))
    events.append(make_event("thinking_delta", content="[qa_review_worker] Compile failure. Analyzing REDEFINES usage pattern...\n"))
    await asyncio.sleep(1.0)
    events.append(make_event("diff_report", module="billing_proc.cbl", category="compile", summary="COBOL REDEFINES fields mapped incorrectly. Variables do not overlap in memory."))
    
    # Retry 1 Build Fail
    events.append(make_event("module_status", module="billing_proc.cbl", status="converting", retry_count=1))
    events.append(make_event("thinking_delta", content="[conversion_worker] Restructuring fields with explicit byte offsets...\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("module_status", module="billing_proc.cbl", status="validating", retry_count=1))
    events.append(make_event("thinking_delta", content="[build_validate_worker] Compiling layout updates...\n"))
    await asyncio.sleep(1.0)
    events.append(make_event("build_result", module="billing_proc.cbl", status="fail", errors=[
        "BillingProcessor.cs(12,2): error CS0579: Duplicate 'StructLayout' attribute found."
    ]))
    events.append(make_event("thinking_delta", content="[qa_review_worker] Duplicate StructLayout tags added during offset compilation.\n"))
    await asyncio.sleep(1.0)
    events.append(make_event("diff_report", module="billing_proc.cbl", category="compile", summary="Duplicate StructLayout attributes declared on structured data models."))

    # Retry 2 Test Fail
    events.append(make_event("module_status", module="billing_proc.cbl", status="converting", retry_count=2))
    events.append(make_event("thinking_delta", content="[conversion_worker] Fixing compile attributes and setting 88-level enums...\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("module_status", module="billing_proc.cbl", status="validating", retry_count=2))
    events.append(make_event("thinking_delta", content="[build_validate_worker] Compiling and running batch validation suite...\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("build_result", module="billing_proc.cbl", status="success"))
    events.append(make_event("test_result", module="billing_proc.cbl", test_name="Test_Compute_Billing_Cycle", status="fail", message="Value precision loss when mapping COBOL conditionals. Expected true, got false."))
    events.append(make_event("thinking_delta", content="[qa_review_worker] Calculation mismatch under test. Conditional 88-level fields missed evaluating code 'E'.\n"))
    await asyncio.sleep(1.0)
    events.append(make_event("diff_report", module="billing_proc.cbl", category="edge_case", summary="Missing state value evaluation mapping in translated 88-level checks."))

    # Retry 3 -> Escalated
    events.append(make_event("module_status", module="billing_proc.cbl", status="converting", retry_count=3))
    events.append(make_event("thinking_delta", content="[conversion_worker] Adjusting conditional loops and EBCDIC parsing helpers...\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("module_status", module="billing_proc.cbl", status="validating", retry_count=3))
    events.append(make_event("thinking_delta", content="[build_validate_worker] Running final validation block...\n"))
    await asyncio.sleep(1.5)
    events.append(make_event("build_result", module="billing_proc.cbl", status="success"))
    events.append(make_event("test_result", module="billing_proc.cbl", test_name="Test_Compute_Billing_Cycle", status="fail", message="EBCDIC character set conversion failed mapping numeric sign characters."))
    
    events.append(make_event("thinking_delta", content="[qa_review_worker] Max retry limit reached (3/3). Interop cannot resolve binary EBCDIC byte representation without manual data format review.\n"))
    await asyncio.sleep(1.0)
    events.append(make_event("diff_report", module="billing_proc.cbl", category="edge_case", summary="EBCDIC character set translation error. Max retries exceeded."))
    events.append(make_event("module_status", module="billing_proc.cbl", status="escalated", retry_count=3))
    events.append(make_event("text_delta", content="### Pipeline Escalate\n**Warning**: Module `billing_proc.cbl` failed build & test validation after 3 retry cycles.\nReason: EBCDIC character set conversion failed mapping numeric sign characters. Escalated to developer dashboard checkpoint.\n\n"))
    await asyncio.sleep(1.0)

    # Done
    events.append(make_event("text_delta", content="### Pipeline Completed\n- Converted Modules: **2 / 3 successfully**\n- Escalated Modules: **1 (Manual review required)**\n- Overall Success Rate: **66.6%**\n\nPlease check the **Validation Dashboard** tab for detailed failure traces, logs, and QA feedback for `billing_proc.cbl`.\n"))
    events.append(make_event("done"))

# SSE API Endpoint
@app.get("/api/agent/stream")
def sse_stream(request: Request):
    return StreamingResponse(sse_generator(), media_type="text/event-stream")

# Serve the static files of the frontend UI
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
