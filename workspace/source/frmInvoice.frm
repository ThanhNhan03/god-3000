VERSION 4.00
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
