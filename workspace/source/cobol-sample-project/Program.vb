Imports System
Imports System.Runtime.InteropServices
Imports System.Text

Module Program
    ' Legacy DLL entry points
    <DllImport("CobolLib.dll", CallingConvention:=CallingConvention.Cdecl, EntryPoint:="ADDNUMS")>
    Private Sub AddNums(ByRef a As Integer, ByRef b As Integer, ByRef result As Integer)
    End Sub

    <DllImport("CobolLib.dll", CallingConvention:=CallingConvention.Cdecl, EntryPoint:="SAYHELLO")>
    Private Sub SayHello(ByVal name As StringBuilder)
    End Sub

    ' Calculator DLL entry points using Double (COMP-2)
    <DllImport("CobolLib.dll", CallingConvention:=CallingConvention.Cdecl, EntryPoint:="ADDNUMS_DBL")>
    Private Sub AddNumsDbl(ByRef a As Double, ByRef b As Double, ByRef result As Double)
    End Sub

    <DllImport("CobolLib.dll", CallingConvention:=CallingConvention.Cdecl, EntryPoint:="SUBNUMS_DBL")>
    Private Sub SubNumsDbl(ByRef a As Double, ByRef b As Double, ByRef result As Double)
    End Sub

    <DllImport("CobolLib.dll", CallingConvention:=CallingConvention.Cdecl, EntryPoint:="MULNUMS_DBL")>
    Private Sub MulNumsDbl(ByRef a As Double, ByRef b As Double, ByRef result As Double)
    End Sub

    <DllImport("CobolLib.dll", CallingConvention:=CallingConvention.Cdecl, EntryPoint:="DIVNUMS_DBL")>
    Private Sub DivNumsDbl(ByRef a As Double, ByRef b As Double, ByRef result As Double, ByRef errCode As Integer)
    End Sub

    Sub Main()
        Dim exitApp As Boolean = False
        
        While Not exitApp
            Console.Clear()
            Console.WriteLine("==============================================")
            Console.WriteLine("        VB.NET & COBOL Calculator             ")
            Console.WriteLine("==============================================")
            Console.WriteLine("1. Add (+)")
            Console.WriteLine("2. Subtract (-)")
            Console.WriteLine("3. Multiply (*)")
            Console.WriteLine("4. Divide (/)")
            Console.WriteLine("5. Run Legacy P/Invoke Tests")
            Console.WriteLine("6. Exit")
            Console.WriteLine("==============================================")
            Console.Write("Choose an option (1-6): ")
            
            Dim choice As String = Console.ReadLine()
            If choice = "6" Then
                exitApp = True
                Continue While
            End If

            If choice = "5" Then
                RunLegacyTests()
                Console.WriteLine("Press Enter to return to menu...")
                Console.ReadLine()
                Continue While
            End If

            If choice <> "1" AndAlso choice <> "2" AndAlso choice <> "3" AndAlso choice <> "4" Then
                Console.WriteLine("Invalid option. Press Enter to retry...")
                Console.ReadLine()
                Continue While
            End If

            ' Input operands
            Dim valA As Double = 0
            Dim valB As Double = 0
            
            Console.Write("Enter first number: ")
            If Not Double.TryParse(Console.ReadLine(), valA) Then
                Console.WriteLine("Invalid number. Press Enter to retry...")
                Console.ReadLine()
                Continue While
            End If

            Console.Write("Enter second number: ")
            If Not Double.TryParse(Console.ReadLine(), valB) Then
                Console.WriteLine("Invalid number. Press Enter to retry...")
                Console.ReadLine()
                Continue While
            End If

            Dim result As Double = 0
            Dim errCode As Integer = 0

            Select Case choice
                Case "1"
                    AddNumsDbl(valA, valB, result)
                    Console.WriteLine($"Result: {valA} + {valB} = {result}")
                Case "2"
                    SubNumsDbl(valA, valB, result)
                    Console.WriteLine($"Result: {valA} - {valB} = {result}")
                Case "3"
                    MulNumsDbl(valA, valB, result)
                    Console.WriteLine($"Result: {valA} * {valB} = {result}")
                Case "4"
                    DivNumsDbl(valA, valB, result, errCode)
                    If errCode <> 0 Then
                        Console.WriteLine("Error: Division by zero is not allowed in COBOL!")
                    Else
                        Console.WriteLine($"Result: {valA} / {valB} = {result}")
                    End If
            End Select

            Console.WriteLine()
            Console.WriteLine("Press Enter to return to menu...")
            Console.ReadLine()
        End While
    End Sub

    Sub RunLegacyTests()
        Console.WriteLine()
        Console.WriteLine("--- Running Legacy COBOL P/Invoke Tests ---")
        Dim legacyA As Integer = 42
        Dim legacyB As Integer = 100
        Dim legacyResult As Integer = 0
        AddNums(legacyA, legacyB, legacyResult)
        Console.WriteLine($"VB.NET: 42 + 100 (Int32) via COBOL = {legacyResult}")

        Dim nameBuilder As New StringBuilder("Alice", 20)
        If nameBuilder.Length < 20 Then
            nameBuilder.Append(" "c, 20 - nameBuilder.Length)
        End If
        SayHello(nameBuilder)
        Console.WriteLine("------------------------------------------")
    End Sub
End Module

