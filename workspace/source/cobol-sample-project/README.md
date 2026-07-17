# Visual Basic .NET & COBOL Integration Sample Project

This sample project demonstrates how to compile a COBOL module into a Dynamic Link Library (`.dll`) using GnuCOBOL and call its subroutines from a Visual Basic .NET (VB.NET) console application.

## Prerequisites

1. **.NET 10.0 SDK** (already installed on this machine).
2. **GnuCOBOL (cobc)**.
   - GnuCOBOL is needed to compile the COBOL module (`CobolLib.cob`) into a `.dll`.
   - If not installed, you can download it from:
     - [GnuCOBOL All-in-One Installer for Windows](https://superbol.eu) (Recommended)
     - [SourceForge GnuCOBOL](https://sourceforge.net/projects/open-cobol/)
   - After installation, ensure that the `bin` directory containing `cobc.exe` is added to your environment `PATH`.

## Project Structure

- `CobolLib.cob`: COBOL library containing entry points (`ADDNUMS`, `SAYHELLO`).
- `Program.vb`: VB.NET entry point importing and calling the COBOL subroutines using Platform Invoke (P/Invoke).
- `CobolSample.vbproj`: VB.NET project configuration targeting .NET 10.0.
- `build_and_run.ps1`: Automation script to compile, copy dependency DLLs, and run.

---

## How It Works

### 1. The COBOL Code (`CobolLib.cob`)
COBOL parameters are passed **by reference** (by memory address) rather than by value:
- `COMP-5` represents native machine binary integers.
- `PIC X(20)` defines a fixed 20-character string.

### 2. The VB.NET Code (`Program.vb`)
P/Invoke imports the C-linkage subroutines using the `DllImport` attribute:
- Parameters are passed `ByRef` to match COBOL's default pass-by-reference mechanism.
- Strings are passed via `System.Text.StringBuilder` because COBOL operates on fixed-length, mutable byte arrays.

```vb
<DllImport("CobolLib.dll", CallingConvention:=CallingConvention.Cdecl, EntryPoint:="ADDNUMS")>
Private Sub AddNums(ByRef a As Integer, ByRef b As Integer, ByRef result As Integer)
End Sub
```

---

## Build and Run

To compile and run the project automatically, run the helper PowerShell script in the root directory:

```powershell
.\build_and_run.ps1
```

If GnuCOBOL is installed, the output will resemble:

```text
==============================================
VB.NET & COBOL Integration Sample Project
==============================================

VB.NET: Calling COBOL to add 42 and 100...
VB.NET: Result received from COBOL = 142

VB.NET: Calling COBOL with string parameter...
COBOL: Hello received for name: Alice               
VB.NET: Finished calling COBOL.

==============================================
```
