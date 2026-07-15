Attribute VB_Name = "MOD_COBOL"
'================================================================'
' MOD_COBOL.BAS: VB4 Module for COBOL Interop Declarations       '
'================================================================'

Option Explicit

' Define the Employee Record layout matching the COBOL COPYBOOK (EMPREC.CPY)
' The fields are defined with fixed-length strings so they pack contiguously.
Public Type EmployeeRecord
    EmpID As String * 5
    EmpName As String * 30
    EmpDept As String * 15
    EmpSalary As String * 9   ' PIC 9(7)V99, e.g. "000250000" for 2500.00
    EmpStatus As String * 1   ' 'A' for Active, 'D' for Deleted
End Type

' Declaration of the COBOL DLL routine.
' Note: In 32-bit Windows, DLL names are case-sensitive and match the entry point.
' In COBOL, the entry point name is typically the PROGRAM-ID (uppercase).
#If Win32 Then
    Public Declare Sub EMPCRUD Lib "empcrud.dll" Alias "EMPCRUD" ( _
        ByVal Action As String, _
        Rec As EmployeeRecord, _
        ByVal Status As String)
#Else
    ' 16-bit declaration for VB4 16-bit target
    Public Declare Sub EMPCRUD Lib "empcrud.dll" ( _
        ByVal Action As String, _
        Rec As EmployeeRecord, _
        ByVal Status As String)
#End If

' Helper function to format a Double into COBOL 9-digit salary format (PIC 9(7)V99)
' Example: 1250.75 -> "000125075"
Public Function DoubleToCobolSalary(ByVal Amount As Double) As String
    Dim Cents As Double
    ' Scale to cents and round
    Cents = Int(Amount * 100 + 0.5)
    DoubleToCobolSalary = Format$(Cents, "000000000")
End Function

' Helper function to convert COBOL 9-digit salary string to Double
' Example: "000125075" -> 1250.75
Public Function CobolSalaryToDouble(ByVal SalaryStr As String) As Double
    Dim Temp As Double
    Temp = Val(SalaryStr)
    CobolSalaryToDouble = Temp / 100
End Function

' Helper function to trim trailing/leading spaces from fixed-length strings
Public Function TrimFixed(ByVal Text As String) As String
    TrimFixed = Trim$(Text)
End Function
