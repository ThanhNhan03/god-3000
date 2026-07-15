IDENTIFICATION DIVISION.
       PROGRAM-ID. SUM-PROGRAM.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  NUM1   PIC 9(3) VALUE 0.
       01  NUM2   PIC 9(3) VALUE 0.
       01  RESULT PIC 9(4) VALUE 0.

       PROCEDURE DIVISION.
           DISPLAY "Enter first number: " WITH NO ADVANCING.
           ACCEPT NUM1.
           
           DISPLAY "Enter second number: " WITH NO ADVANCING.
           ACCEPT NUM2.

           ADD NUM1 TO NUM2 GIVING RESULT.

           DISPLAY "Total Sum: " RESULT.
           
           STOP RUN.