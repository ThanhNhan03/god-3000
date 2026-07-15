      *================================================================*
      * EMPCRUD.CBL: COBOL CRUD Engine for Employee Records             *
      *================================================================*
       IDENTIFICATION DIVISION.
       PROGRAM-ID. EMPCRUD.
       
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT EMPLOYEE-FILE ASSIGN TO "employee.dat"
               ORGANIZATION IS INDEXED
               ACCESS MODE IS DYNAMIC
               RECORD KEY IS FE-EMP-ID
               FILE STATUS IS WS-FILE-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  EMPLOYEE-FILE.
       01  EMPLOYEE-FILE-REC.
           05  FE-EMP-ID          PIC X(5).
           05  FE-EMP-NAME        PIC X(30).
           05  FE-EMP-DEPT        PIC X(15).
           05  FE-EMP-SALARY      PIC 9(7)V99.
           05  FE-EMP-STATUS      PIC X(1).

       WORKING-STORAGE SECTION.
       01  WS-FILE-STATUS         PIC X(2).
           88  FS-SUCCESS         VALUE "00".
           88  FS-DUP-KEY         VALUE "22".
           88  FS-NOT-FOUND       VALUE "23".

       LINKAGE SECTION.
       01  LS-ACTION              PIC X(1).
      * COPYBOOK insertion (Defines 01 EMPLOYEE-RECORD)
       COPY "EMPREC.CPY".
       01  LS-STATUS-CODE         PIC X(2).

       PROCEDURE DIVISION USING LS-ACTION EMPLOYEE-RECORD LS-STATUS-CODE.
       MAIN-LOGIC.
           OPEN I-O EMPLOYEE-FILE
      * If file doesn't exist, try to open output first to create it
           IF WS-FILE-STATUS = "35" OR "30"
               OPEN OUTPUT EMPLOYEE-FILE
               CLOSE EMPLOYEE-FILE
               OPEN I-O EMPLOYEE-FILE
           END-IF

           IF WS-FILE-STATUS NOT = "00"
               MOVE "99" TO LS-STATUS-CODE
               GOBACK
           END-IF

           EVALUATE LS-ACTION
               WHEN "C"
                   PERFORM CREATE-RECORD
               WHEN "R"
                   PERFORM READ-RECORD
               WHEN "U"
                   PERFORM UPDATE-RECORD
               WHEN "D"
                   PERFORM DELETE-RECORD
               WHEN OTHER
                   MOVE "90" TO LS-STATUS-CODE
           END-EVALUATE.

           CLOSE EMPLOYEE-FILE.
           GOBACK.

       CREATE-RECORD.
           MOVE EMP-ID OF EMPLOYEE-RECORD TO FE-EMP-ID
           MOVE EMP-NAME OF EMPLOYEE-RECORD TO FE-EMP-NAME
           MOVE EMP-DEPT OF EMPLOYEE-RECORD TO FE-EMP-DEPT
           MOVE EMP-SALARY OF EMPLOYEE-RECORD TO FE-EMP-SALARY
           MOVE EMP-STATUS OF EMPLOYEE-RECORD TO FE-EMP-STATUS
           
           WRITE EMPLOYEE-FILE-REC
           
           EVALUATE WS-FILE-STATUS
               WHEN "00"
                   MOVE "00" TO LS-STATUS-CODE
               WHEN "22"
                   MOVE "01" TO LS-STATUS-CODE  *> Duplicate key
               WHEN OTHER
                   MOVE WS-FILE-STATUS TO LS-STATUS-CODE
           END-EVALUATE.

       READ-RECORD.
           MOVE EMP-ID OF EMPLOYEE-RECORD TO FE-EMP-ID
           
           READ EMPLOYEE-FILE
           
           EVALUATE WS-FILE-STATUS
               WHEN "00"
                   MOVE FE-EMP-ID TO EMP-ID OF EMPLOYEE-RECORD
                   MOVE FE-EMP-NAME TO EMP-NAME OF EMPLOYEE-RECORD
                   MOVE FE-EMP-DEPT TO EMP-DEPT OF EMPLOYEE-RECORD
                   MOVE FE-EMP-SALARY TO EMP-SALARY OF EMPLOYEE-RECORD
                   MOVE FE-EMP-STATUS TO EMP-STATUS OF EMPLOYEE-RECORD
                   MOVE "00" TO LS-STATUS-CODE
               WHEN "23"
                   MOVE "02" TO LS-STATUS-CODE  *> Not found
               WHEN OTHER
                   MOVE WS-FILE-STATUS TO LS-STATUS-CODE
           END-EVALUATE.

       UPDATE-RECORD.
           MOVE EMP-ID OF EMPLOYEE-RECORD TO FE-EMP-ID
           
           *> First check if it exists
           READ EMPLOYEE-FILE
           IF WS-FILE-STATUS = "00"
               MOVE EMP-NAME OF EMPLOYEE-RECORD TO FE-EMP-NAME
               MOVE EMP-DEPT OF EMPLOYEE-RECORD TO FE-EMP-DEPT
               MOVE EMP-SALARY OF EMPLOYEE-RECORD TO FE-EMP-SALARY
               MOVE EMP-STATUS OF EMPLOYEE-RECORD TO FE-EMP-STATUS
               
               REWRITE EMPLOYEE-FILE-REC
               EVALUATE WS-FILE-STATUS
                   WHEN "00"
                       MOVE "00" TO LS-STATUS-CODE
                   WHEN OTHER
                       MOVE WS-FILE-STATUS TO LS-STATUS-CODE
               END-EVALUATE
           ELSE
               IF WS-FILE-STATUS = "23"
                   MOVE "02" TO LS-STATUS-CODE  *> Not found
               ELSE
                   MOVE WS-FILE-STATUS TO LS-STATUS-CODE
               END-IF
           END-IF.

       DELETE-RECORD.
           MOVE EMP-ID OF EMPLOYEE-RECORD TO FE-EMP-ID
           
           *> First check if it exists
           READ EMPLOYEE-FILE
           IF WS-FILE-STATUS = "00"
               DELETE EMPLOYEE-FILE RECORD
               EVALUATE WS-FILE-STATUS
                   WHEN "00"
                       MOVE "00" TO LS-STATUS-CODE
                   WHEN OTHER
                       MOVE WS-FILE-STATUS TO LS-STATUS-CODE
               END-EVALUATE
           ELSE
               IF WS-FILE-STATUS = "23"
                   MOVE "02" TO LS-STATUS-CODE  *> Not found
               ELSE
                   MOVE WS-FILE-STATUS TO LS-STATUS-CODE
               END-IF
           END-IF.
