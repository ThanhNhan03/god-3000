// EmployeeViewModel.cs
using System.ComponentModel.DataAnnotations;

namespace cobolProjectMvc
{
    public class EmployeeViewModel
    {
        [Required]
        [StringLength(5)]
        public string EmpID { get; set; }

        [Required]
        [StringLength(30)]
        public string EmpName { get; set; }

        [StringLength(15)]
        public string EmpDept { get; set; }

        [Required]
        [Range(0, 9999999.99)]
        public double EmpSalary { get; set; }

        [Required]
        [StringLength(1)]
        public string EmpStatus { get; set; }
    }
}
