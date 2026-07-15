# backend/samples.py

SAMPLE_FILES = {
    "source/frmInvoice.frm": """VERSION 4.00
Begin VB.Form frmInvoice
   Caption         =   "Invoice Generation"
   ClientHeight    =   6500
   ClientWidth     =   9000
   Begin VB.CommandButton cmdCalculate
      Caption         =   "Calculate Total"
      Height          =   495
      Left            =   3600
      Top             =   5280
      Width           =   1815
   End
   Begin VB.TextBox txtVAT
      Text            =   "10.0"
      Height          =   375
      Left            =   2400
      Top             =   4560
      Width           =   1215
   End
   Begin VB.TextBox txtSubtotal
      Text            =   "1500.00"
      Height          =   375
      Left            =   2400
      Top             =   3960
      Width           =   1215
   End
End
Attribute VB_Name = "frmInvoice"

Private Sub cmdCalculate_Click()
    Dim subtotal As Double
    Dim vatRate As Double
    Dim total As Double
    
    subtotal = CDbl(txtSubtotal.Text)
    vatRate = CDbl(txtVAT.Text) / 100
    
    ' Call COBOL Interop layer to calculate packed decimal VAT
    Dim cobolResult As String
    cobolResult = CalculateInvoiceVAT_COBOL(subtotal, vatRate)
    
    MsgBox "Invoice total calculated successfully! Result: " & cobolResult
End Sub
""",

    "source/INVOICE.cbl": """       IDENTIFICATION DIVISION.
       PROGRAM-ID. INVOICE.
       AUTHOR. LEGACY-DEV.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-INVOICE-DATA.
           05  WS-SUBTOTAL      PIC S9(7)V99 COMP-3.
           05  WS-VAT-RATE      PIC S9(2)V99 COMP-3.
           05  WS-TOTAL         PIC S9(7)V99 COMP-3.
           05  WS-VAT-AMOUNT    PIC S9(5)V99 COMP-3.
           
       LINKAGE SECTION.
       01  LS-SUBTOTAL-IN     PIC X(10).
       01  LS-VAT-RATE-IN     PIC X(5).
       01  LS-TOTAL-OUT       PIC X(12).

       PROCEDURE DIVISION USING LS-SUBTOTAL-IN LS-VAT-RATE-IN LS-TOTAL-OUT.
       MAIN-LOGIC.
           COMPUTE WS-SUBTOTAL = FUNCTION NUMVAL(LS-SUBTOTAL-IN)
           COMPUTE WS-VAT-RATE = FUNCTION NUMVAL(LS-VAT-RATE-IN)
           
           COMPUTE WS-VAT-AMOUNT = WS-SUBTOTAL * WS-VAT-RATE
           COMPUTE WS-TOTAL = WS-SUBTOTAL + WS-VAT-AMOUNT
           
           MOVE WS-TOTAL TO LS-TOTAL-OUT.
           GOBACK.
""",

    "output/InvoiceController.cs": """using Microsoft.AspNetCore.Mvc;
using System;

namespace LegacyMigration.Controllers
{
    public class InvoiceController : Controller
    {
        private readonly ICobolInterop _cobolInterop;

        public InvoiceController(ICobolInterop cobolInterop)
        {
            _cobolInterop = cobolInterop;
        }

        [HttpGet]
        public IActionResult Index()
        {
            return View(new InvoiceViewModel());
        }

        [HttpPost]
        public IActionResult Calculate(InvoiceViewModel model)
        {
            try
            {
                decimal subtotal = model.Subtotal;
                decimal vatRate = model.VatRate / 100m;
                
                decimal total = _cobolInterop.CalculateInvoiceVAT(subtotal, vatRate);
                
                model.Total = total;
                model.Success = true;
                model.Message = $"Calculation complete: Total = {total:C2}";
            }
            catch (Exception ex)
            {
                model.Success = false;
                model.Message = $"Error: {ex.Message}";
            }
            return View("Index", model);
        }
    }
}
""",

    "output/InvoiceViewModel.cs": """namespace LegacyMigration.Controllers
{
    public class InvoiceViewModel
    {
        public decimal Subtotal { get; set; } = 1500.00m;
        public decimal VatRate { get; set; } = 10.0m;
        public decimal Total { get; set; }
        public bool Success { get; set; }
        public string Message { get; set; }
    }
}
""",

    "output/InvoiceTests.cs": """using Xunit;
using LegacyMigration.Controllers;
using Moq;

namespace LegacyMigration.Tests
{
    public class InvoiceTests
    {
        [Fact]
        public void Test_VAT_Calculation_Success()
        {
            var mockInterop = new Mock<ICobolInterop>();
            mockInterop.Setup(x => x.CalculateInvoiceVAT(1500.00m, 0.10m)).Returns(1650.00m);
            var controller = new InvoiceController(mockInterop.Object);
            var model = new InvoiceViewModel { Subtotal = 1500.00m, VatRate = 10.0m };

            var result = controller.Calculate(model) as Microsoft.AspNetCore.Mvc.ViewResult;
            var resultModel = result?.Model as InvoiceViewModel;

            Assert.NotNull(resultModel);
            Assert.True(resultModel.Success);
            Assert.Equal(1650.00m, resultModel.Total);
        }
    }
}
"""
}

MODULE_RUNS = {
    "frmInvoice.frm": [
        {
            "retry": 0,
            "stage": "build",
            "status": "fail",
            "build_log": """Microsoft (R) Build Engine version 17.8.3+195e7f5a3 for .NET
Copyright (C) Microsoft Corporation. All rights reserved.

e:\\workspace\\output\\InvoiceController.cs(11,26): error CS0246: The type or namespace name 'ICobolInterop' could not be found (are you missing a using directive or an assembly reference?) [e:\\workspace\\output\\LegacyMigration.csproj]
e:\\workspace\\output\\InvoiceController.cs(13,42): error CS0246: The type or namespace name 'ICobolInterop' could not be found [e:\\workspace\\output\\LegacyMigration.csproj]

Build FAILED.
    2 Error(s)
    0 Warning(s)
""",
            "test_log": "No test runs executed due to build compilation failure.",
            "qa_review": """### QA REVIEW - RETRY 0
**Error Category**: Compile Error
**Analysis**:
The controller refers to `ICobolInterop` interface, but this interface has not been declared or generated in the interop/helper package. This causes compile errors CS0246.
**Action Plan**:
Generate `ICobolInterop` and `CobolInterop` implementations inside the interop directory, adding dependency injection registration in Program.cs.
"""
        },
        {
            "retry": 1,
            "stage": "test",
            "status": "fail",
            "build_log": """Microsoft (R) Build Engine version 17.8.3+195e7f5a3 for .NET
Copyright (C) Microsoft Corporation. All rights reserved.
  Restore completed in 84.2 ms for e:\\workspace\\output\\LegacyMigration.csproj.
  LegacyMigration -> e:\\workspace\\output\\bin\\Debug\\net8.0\\LegacyMigration.dll
Build Succeeded.
    0 Error(s)
    0 Warning(s)
""",
            "test_log": """Passed!  - Failed: 1, Passed: 0, Skipped: 0, Total: 1, Duration: 42 ms - LegacyMigration.Tests.dll

[FAIL] LegacyMigration.Tests.InvoiceTests.Test_VAT_Calculation_Success
  Error Message:
   Assert.Equal() Failure
Expected: 1650.00
Actual:   1500.00
  Stack Trace:
     at LegacyMigration.Tests.InvoiceTests.Test_VAT_Calculation_Success() in e:\\workspace\\output\\InvoiceTests.cs:line 24
""",
            "qa_review": """### QA REVIEW - RETRY 1
**Error Category**: Logic / Calculation Precision Error
**Analysis**:
The unit test failed because the calculated total is `1500.00` instead of `1650.00`.
Looking at the generated interop code, the calculation logic is:
`decimal total = subtotal;` (it failed to compute the VAT amount `subtotal * vatRate`).
This is likely a COMP-3 parsing translation error where the LLM omitted the math.
**Action Plan**:
Update the `CobolInterop` implementation to compute the total correctly as `subtotal + (subtotal * vatRate)` following the COBOL calculation standard.
"""
        },
        {
            "retry": 2,
            "stage": "test",
            "status": "success",
            "build_log": """Microsoft (R) Build Engine version 17.8.3+195e7f5a3 for .NET
Copyright (C) Microsoft Corporation. All rights reserved.
  LegacyMigration -> e:\\workspace\\output\\bin\\Debug\\net8.0\\LegacyMigration.dll
Build Succeeded.
    0 Error(s)
    0 Warning(s)
""",
            "test_log": """Passed!  - Failed: 0, Passed: 1, Skipped: 0, Total: 1, Duration: 23 ms - LegacyMigration.Tests.dll
xUnit Test Executions:
  - Test_VAT_Calculation_Success: PASSED (23 ms)
""",
            "qa_review": """### QA REVIEW - RETRY 2
**Status**: All Tests Passed.
**Confidence Score**: 0.94 (based on 2 retries, 100% logic coverage, handles COMP-3 decimal rounding precision safely).
"""
        }
    ],

    "frmCustomer.frm": [
        {
            "retry": 0,
            "stage": "test",
            "status": "success",
            "build_log": """Microsoft (R) Build Engine version 17.8.3+195e7f5a3 for .NET
Copyright (C) Microsoft Corporation. All rights reserved.
  Restore completed in 32.5 ms for e:\\workspace\\output\\LegacyMigration.csproj.
  LegacyMigration -> e:\\workspace\\output\\bin\\Debug\\net8.0\\LegacyMigration.dll
Build Succeeded.
    0 Error(s)
    0 Warning(s)
""",
            "test_log": """Passed!  - Failed: 0, Passed: 2, Skipped: 0, Total: 2, Duration: 35 ms - LegacyMigration.Tests.dll
xUnit Test Executions:
  - Test_Load_Customer_Profile: PASSED (15 ms)
  - Test_Save_Customer_Profile: PASSED (20 ms)
""",
            "qa_review": """### QA REVIEW - RETRY 0
**Status**: All Tests Passed on Initial Conversion.
**Confidence Score**: 0.98 (based on 0 retries, standard CRUD module, low structural complexity).
"""
        }
    ],

    "billing_proc.cbl": [
        {
            "retry": 0,
            "stage": "build",
            "status": "fail",
            "build_log": """Microsoft (R) Build Engine version 17.8.3+195e7f5a3 for .NET
e:\\workspace\\output\\BillingProcessor.cs(44,18): error CS0103: The name 'REDEFINES_BillingBlock' does not exist in the current context.

Build FAILED.
    1 Error(s)
""",
            "test_log": "No test runs executed due to compile failure.",
            "qa_review": """### QA REVIEW - RETRY 0
**Error Category**: Redefines Mapping Error
**Analysis**:
COBOL REDEFINES construct mapping failed in C#. The field definitions overlap in memory, which cannot be represented directly in C# using normal classes without explicit FieldOffset attributes or Union structures.
**Action Plan**:
Use `StructLayout(LayoutKind.Explicit)` to declare overlapping variables.
"""
        },
        {
            "retry": 1,
            "stage": "build",
            "status": "fail",
            "build_log": """Microsoft (R) Build Engine version 17.8.3+195e7f5a3 for .NET
e:\\workspace\\output\\BillingProcessor.cs(12,2): error CS0579: Duplicate 'StructLayout' attribute.

Build FAILED.
    1 Error(s)
""",
            "test_log": "No test runs executed.",
            "qa_review": """### QA REVIEW - RETRY 1
**Error Category**: Attribute Compilation Error
**Analysis**:
LLM appended duplicate StructLayout attributes to the class definition.
**Action Plan**:
Refactor structures, ensuring StructLayout is defined once on the struct layout helper.
"""
        },
        {
            "retry": 2,
            "stage": "test",
            "status": "fail",
            "build_log": """Build Succeeded. 0 Errors.""",
            "test_log": """Passed!  - Failed: 1, Passed: 0, Skipped: 0, Total: 1 - BillingProcessor.Tests.dll

[FAIL] BillingTests.Test_Compute_Billing_Cycle
  Error Message:
   Numeric precision loss detected when handling 88-level status checks.
Expected: true
Actual:   false
""",
            "qa_review": """### QA REVIEW - RETRY 2
**Error Category**: Logic / Edge-Case Error
**Analysis**:
88-level conditional variables in COBOL (`88 VALID-STATUS VALUE 'A', 'B', 'E'`) were converted to C# enum checks but missed checking state 'E'.
**Action Plan**:
Extend the validation logic helper to include all enum states matching value 'E'.
"""
        },
        {
            "retry": 3,
            "stage": "test",
            "status": "fail",
            "build_log": "Build Succeeded.",
            "test_log": "[FAIL] BillingTests.Test_Compute_Billing_Cycle - Failed processing EBCDIC records.",
            "qa_review": """### QA REVIEW - RETRY 3 (MAX REACHED)
**Error Category**: Data EBCDIC / Binary Incompatibility
**Analysis**:
Max retry threshold reached. The EBCDIC to UTF-8 interop layer fails to correctly unpack the custom COBOL packed-decimal representation of high-precision balances under heavy concurrent loads. Needs manual review of interop marshalling definitions.
**Action Plan**:
Escalating module to human developer intervention checkpoint.
"""
        }
    ]
}
