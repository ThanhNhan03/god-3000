using System.ComponentModel.DataAnnotations;

namespace cobolMvc
{
    public class EmployeeRecordViewModel
    {
        [Required]
        [StringLength(5, ErrorMessage = "Employee ID must be 5 characters.")]
        public string EmpID { get; set; }

        [Required]
        [StringLength(30, ErrorMessage = "Employee Name must not exceed 30 characters.")]
        public string EmpName { get; set; }

        [Required]
        [StringLength(15, ErrorMessage = "Department Name must not exceed 15 characters.")]
        public string EmpDept { get; set; }

        [Required]
        [Range(0, double.MaxValue, ErrorMessage = "Salary must be a non-negative number.")]
        public double EmpSalary { get; set; }

        [Required]
        [StringLength(1, ErrorMessage = "Status must be a single character ('A' or 'D').")]
        public string EmpStatus { get; set; }
    }
}