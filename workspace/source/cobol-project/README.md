# VB4 + COBOL CRUD Sample Project

This repository contains a legacy Visual Basic 4 (VB4) and COBOL integration project, designed to manage basic CRUD (Create, Read, Update, Delete) operations for Employee records. This serves as a realistic input source for legacy migration pipelines, conforming to the structure of migration challenges such as those in [requirment-hackathon.md](file:///c:/Users/ll/Documents/my-project/cobol-project/requirment-hackathon.md).

## Project Structure

- **[EMP_MGR.VBP](file:///c:/Users/ll/Documents/my-project/cobol-project/EMP_MGR.VBP)**: Visual Basic 4 Project file that links the forms and modules together.
- **[FRM_EMP.FRM](file:///c:/Users/ll/Documents/my-project/cobol-project/FRM_EMP.FRM)**: The user interface form containing input text boxes, CRUD action command buttons, status logs, and UI event handlers.
- **[MOD_COBOL.BAS](file:///c:/Users/ll/Documents/my-project/cobol-project/MOD_COBOL.BAS)**: Visual Basic module declaring DLL functions (`EMPCRUD`) and containing conversion helpers for mapping data formats.
- **[EMPREC.CPY](file:///c:/Users/ll/Documents/my-project/cobol-project/EMPREC.CPY)**: COBOL Copybook representing the data buffer structure shared between the VB4 UI and COBOL backend.
- **[EMPCRUD.CBL](file:///c:/Users/ll/Documents/my-project/cobol-project/EMPCRUD.CBL)**: The core COBOL business logic program handling file-based indexed storage operations on `employee.dat`.

---

## Interop and Data Mapping

### 1. Data Structure Alignment
The communication between VB4 and COBOL relies on a fixed-width byte alignment mapped using the following structures:

**COBOL Copybook (`EMPREC.CPY`)**:
```cobol
       01  EMPLOYEE-RECORD.
           05  EMP-ID          PIC X(5).
           05  EMP-NAME        PIC X(30).
           05  EMP-DEPT        PIC X(15).
           05  EMP-SALARY      PIC 9(7)V99.
           05  EMP-STATUS      PIC X(1).
```

**VB4 User-Defined Type (`MOD_COBOL.BAS`)**:
```vb
Public Type EmployeeRecord
    EmpID As String * 5
    EmpName As String * 30
    EmpDept As String * 15
    EmpSalary As String * 9   ' PIC 9(7)V99 (e.g., "000250000" = 2500.00)
    EmpStatus As String * 1
End Type
```

### 2. Calling Convention
In VB4, the DLL routine is declared and invoked via Standard Call (`stdcall`):
```vb
Public Declare Sub EMPCRUD Lib "empcrud.dll" Alias "EMPCRUD" ( _
    ByVal Action As String, _
    Rec As EmployeeRecord, _
    ByVal Status As String)
```
- `Action`: Passed by value as a 1-character string (`"C"`, `"R"`, `"U"`, `"D"`).
- `Rec`: Passed by reference as a contiguous fixed-length structure mapping `EMPLOYEE-RECORD`.
- `Status`: Passed by value as a 2-character buffer (pre-allocated in VB) to retrieve return codes from COBOL:
  - `"00"`: Success
  - `"01"`: Record already exists (duplicate key)
  - `"02"`: Record not found
  - `"99"`: File system access error

---

## Legacy Build & Compilation Setup

### 1. Compiling the COBOL DLL
In a Windows development environment with Micro Focus COBOL or NetExpress:
```cmd
cobol EMPCRUD.CBL DLL OUT(EMPCRUD.dll)
```
Alternatively, if compiling with GnuCOBOL for Windows (MinGW):
```cmd
cobc -m -o empcrud.dll EMPCRUD.CBL
```

### 2. VB4 Build
- Open Visual Basic 4.
- Load `EMP_MGR.VBP`.
- Compile the project via `File -> Make EMP_MGR.exe`.
- Ensure `empcrud.dll` is located in the same directory as `EMP_MGR.exe` or placed in `C:\Windows\System32` (or `SysWOW64`).
