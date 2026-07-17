       IDENTIFICATION DIVISION.
       PROGRAM-ID. CobolLib.

       ENVIRONMENT DIVISION.
       DATA DIVISION.
       LINKAGE SECTION.
       
       * Parameters for ADDNUMS
       01  NUM-A       PIC S9(9) COMP-5.
       01  NUM-B       PIC S9(9) COMP-5.
       01  SUM-RESULT  PIC S9(9) COMP-5.

       * Parameters for SAYHELLO
       * Note: Visual Basic StringBuilder passes a reference to its character array.
       01  CLIENT-NAME PIC X(20).

       * Calculator Parameters (Double Precision Float & Int32 error code)
       01  CALC-A       COMP-2.
       01  CALC-B       COMP-2.
       01  CALC-RESULT  COMP-2.
       01  ERR-CODE     PIC S9(9) COMP-5.

       PROCEDURE DIVISION.
           GOBACK.

       ENTRY "ADDNUMS" USING NUM-A NUM-B SUM-RESULT.
           ADD NUM-A TO NUM-B GIVING SUM-RESULT.
           GOBACK.

       ENTRY "SAYHELLO" USING CLIENT-NAME.
           DISPLAY "COBOL: Hello received for name: " CLIENT-NAME.
           GOBACK.

       ENTRY "ADDNUMS_DBL" USING CALC-A CALC-B CALC-RESULT.
           ADD CALC-A TO CALC-B GIVING CALC-RESULT.
           GOBACK.

       ENTRY "SUBNUMS_DBL" USING CALC-A CALC-B CALC-RESULT.
           SUBTRACT CALC-B FROM CALC-A GIVING CALC-RESULT.
           GOBACK.

       ENTRY "MULNUMS_DBL" USING CALC-A CALC-B CALC-RESULT.
           MULTIPLY CALC-A BY CALC-B GIVING CALC-RESULT.
           GOBACK.

       ENTRY "DIVNUMS_DBL" USING CALC-A CALC-B CALC-RESULT ERR-CODE.
           IF CALC-B = 0
               MOVE 1 TO ERR-CODE
           ELSE
               MOVE 0 TO ERR-CODE
               DIVIDE CALC-A BY CALC-B GIVING CALC-RESULT
           END-IF.
           GOBACK.

