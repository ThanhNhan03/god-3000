VERSION 4.00
Begin VB.Form frmEmployee 
   Caption         =   "Employee Management (VB4 + COBOL CRUD)"
   ClientHeight    =   5000
   ClientLeft      =   1000
   ClientTop       =   1000
   ClientWidth     =   7000
   Height          =   5400
   Left            =   1000
   ScaleHeight     =   5000
   ScaleWidth      =   7000
   Top             =   1000
   Width           =   7120
   Begin VB.TextBox txtID 
      Height          =   375
      Left            =   2000
      MaxLength       =   5
      TabIndex        =   0
      Top             =   400
      Width           =   1200
   End
   Begin VB.TextBox txtName 
      Height          =   375
      Left            =   2000
      MaxLength       =   30
      TabIndex        =   1
      Top             =   1000
      Width           =   4000
   End
   Begin VB.TextBox txtDept 
      Height          =   375
      Left            =   2000
      MaxLength       =   15
      TabIndex        =   2
      Top             =   1600
      Width           =   2500
   End
   Begin VB.TextBox txtSalary 
      Height          =   375
      Left            =   2000
      MaxLength       =   9
      TabIndex        =   3
      Top             =   2200
      Width           =   1800
   End
   Begin VB.TextBox txtStatus 
      Height          =   375
      Left            =   2000
      MaxLength       =   1
      TabIndex        =   4
      Top             =   2800
      Width           =   500
   End
   Begin VB.CommandButton btnCreate 
      Caption         =   "&Create"
      Height          =   495
      Left            =   400
      TabIndex        =   5
      Top             =   3600
      Width           =   1000
   End
   Begin VB.CommandButton btnRead 
      Caption         =   "&Read"
      Height          =   495
      Left            =   1600
      TabIndex        =   6
      Top             =   3600
      Width           =   1000
   End
   Begin VB.CommandButton btnUpdate 
      Caption         =   "&Update"
      Height          =   495
      Left            =   2800
      TabIndex        =   7
      Top             =   3600
      Width           =   1000
   End
   Begin VB.CommandButton btnDelete 
      Caption         =   "&Delete"
      Height          =   495
      Left            =   4000
      TabIndex        =   8
      Top             =   3600
      Width           =   1000
   End
   Begin VB.CommandButton btnClear 
      Caption         =   "C&lear"
      Height          =   495
      Left            =   5200
      TabIndex        =   9
      Top             =   3600
      Width           =   1000
   End
   Begin VB.Label lblID 
      Caption         =   "Employee ID (5 chars):"
      Height          =   255
      Left            =   300
      TabIndex        =   10
      Top             =   460
      Width           =   1600
   End
   Begin VB.Label lblName 
      Caption         =   "Name (30 chars):"
      Height          =   255
      Left            =   300
      TabIndex        =   11
      Top             =   1060
      Width           =   1600
   End
   Begin VB.Label lblDept 
      Caption         =   "Department (15 chars):"
      Height          =   255
      Left            =   300
      TabIndex        =   12
      Top             =   1660
      Width           =   1600
   End
   Begin VB.Label lblSalary 
      Caption         =   "Salary (e.g. 1500.50):"
      Height          =   255
      Left            =   300
      TabIndex        =   13
      Top             =   2260
      Width           =   1600
   End
   Begin VB.Label lblStatusField 
      Caption         =   "Status (A/D):"
      Height          =   255
      Left            =   300
      TabIndex        =   14
      Top             =   2860
      Width           =   1600
   End
   Begin VB.Label lblResult 
      BorderStyle     =   1  'Fixed Single
      Caption         =   "Ready"
      ForeColor       =   &H00800000&
      Height          =   375
      Left            =   400
      TabIndex        =   15
      Top             =   4300
      Width           =   5800
   End
End
Attribute VB_Name = "frmEmployee"
Attribute VB_Creatable = False
Attribute VB_Exposed = False
Option Explicit

Private Sub ClearFields()
    txtID.Text = ""
    txtName.Text = ""
    txtDept.Text = ""
    txtSalary.Text = ""
    txtStatus.Text = "A"
    lblResult.Caption = "Fields cleared."
    lblResult.ForeColor = &H800000
End Sub

Private Sub SetResult(ByVal StatusCode As String)
    Select Case StatusCode
        Case "00"
            lblResult.Caption = "Success (Status Code 00)"
            lblResult.ForeColor = &H4000& ' Green
        Case "01"
            lblResult.Caption = "Error: Record already exists (Status Code 01)"
            lblResult.ForeColor = &HFF& ' Red
        Case "02"
            lblResult.Caption = "Error: Record not found (Status Code 02)"
            lblResult.ForeColor = &HFF& ' Red
        Case "99"
            lblResult.Caption = "System Error: File Open/Access failure (Status Code 99)"
            lblResult.ForeColor = &HFF& ' Red
        Case Else
            lblResult.Caption = "Unexpected Status Code: " & StatusCode
            lblResult.ForeColor = &HFF& ' Red
    End Select
End Sub

Private Sub btnClear_Click()
    ClearFields
End Sub

Private Sub btnCreate_Click()
    Dim Rec As EmployeeRecord
    Dim Status As String
    
    If Trim$(txtID.Text) = "" Then
        MsgBox "Employee ID is required.", vbExclamation, "Validation Error"
        Exit Sub
    End If
    
    ' Populate record buffer
    Rec.EmpID = txtID.Text
    Rec.EmpName = txtName.Text
    Rec.EmpDept = txtDept.Text
    Rec.EmpSalary = DoubleToCobolSalary(Val(txtSalary.Text))
    Rec.EmpStatus = txtStatus.Text
    
    Status = Space$(2)
    
    ' Call COBOL DLL
    Call EMPCRUD("C", Rec, Status)
    
    Call SetResult(Status)
End Sub

Private Sub btnRead_Click()
    Dim Rec As EmployeeRecord
    Dim Status As String
    
    If Trim$(txtID.Text) = "" Then
        MsgBox "Employee ID is required to read.", vbExclamation, "Validation Error"
        Exit Sub
    End If
    
    Rec.EmpID = txtID.Text
    Status = Space$(2)
    
    ' Call COBOL DLL
    Call EMPCRUD("R", Rec, Status)
    
    Call SetResult(Status)
    
    If Status = "00" Then
        ' Update UI from record buffer
        txtID.Text = TrimFixed(Rec.EmpID)
        txtName.Text = TrimFixed(Rec.EmpName)
        txtDept.Text = TrimFixed(Rec.EmpDept)
        txtSalary.Text = Format$(CobolSalaryToDouble(Rec.EmpSalary), "0.00")
        txtStatus.Text = TrimFixed(Rec.EmpStatus)
    End If
End Sub

Private Sub btnUpdate_Click()
    Dim Rec As EmployeeRecord
    Dim Status As String
    
    If Trim$(txtID.Text) = "" Then
        MsgBox "Employee ID is required.", vbExclamation, "Validation Error"
        Exit Sub
    End If
    
    Rec.EmpID = txtID.Text
    Rec.EmpName = txtName.Text
    Rec.EmpDept = txtDept.Text
    Rec.EmpSalary = DoubleToCobolSalary(Val(txtSalary.Text))
    Rec.EmpStatus = txtStatus.Text
    
    Status = Space$(2)
    
    ' Call COBOL DLL
    Call EMPCRUD("U", Rec, Status)
    
    Call SetResult(Status)
End Sub

Private Sub btnDelete_Click()
    Dim Rec As EmployeeRecord
    Dim Status As String
    
    If Trim$(txtID.Text) = "" Then
        MsgBox "Employee ID is required to delete.", vbExclamation, "Validation Error"
        Exit Sub
    End If
    
    Rec.EmpID = txtID.Text
    Status = Space$(2)
    
    ' Call COBOL DLL
    Call EMPCRUD("D", Rec, Status)
    
    Call SetResult(Status)
    
    If Status = "00" Then
        ClearFields
        lblResult.Caption = "Record deleted successfully."
        lblResult.ForeColor = &H4000&
    End If
End Sub

Private Sub Form_Load()
    ClearFields
End Sub
