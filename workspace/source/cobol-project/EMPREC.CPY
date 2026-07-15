      *================================================================*
      * EMPREC.CPY: Employee Record Layout for VB4 - COBOL Interop     *
      *================================================================*
       01  EMPLOYEE-RECORD.
           05  EMP-ID          PIC X(5).
           05  EMP-NAME        PIC X(30).
           05  EMP-DEPT        PIC X(15).
           05  EMP-SALARY      PIC 9(7)V99.
           05  EMP-STATUS      PIC X(1).
      *
      * Field lengths and details:
      * EMP-ID: 5 characters, alphanumeric. Key field.
      * EMP-NAME: 30 characters, alphanumeric.
      * EMP-DEPT: 15 characters, alphanumeric.
      * EMP-SALARY: 9 digits, numeric zoned decimal, 2 decimal places
      *             Equivalent to 9 byte numeric string with implicit dot.
      * EMP-STATUS: 1 character. 'A' for Active, 'D' for Deleted.
