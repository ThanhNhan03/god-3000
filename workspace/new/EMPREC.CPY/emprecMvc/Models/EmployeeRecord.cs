namespace emprecMvc
{
    public class EmployeeRecord
    {
        public string EmployeeId { get; set; } // EMP-ID
        public string EmployeeName { get; set; } // EMP-NAME
        public string Department { get; set; } // EMP-DEPT
        public decimal Salary { get; set; } // EMP-SALARY
        public char Status { get; set; } // EMP-STATUS
    }

    public class EmployeeRecordViewModel
    {
        public string EmployeeId { get; set; }
        public string EmployeeName { get; set; }
        public string Department { get; set; }
        public decimal Salary { get; set; }
        public char Status { get; set; }
    }
}