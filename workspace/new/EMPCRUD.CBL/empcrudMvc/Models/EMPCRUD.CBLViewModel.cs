using System.ComponentModel.DataAnnotations;

namespace empcrudMvc
{
    public class EmployeeViewModel
    {
        [Required]
        [StringLength(5)]
        public string EmployeeId { get; set; }

        [Required]
        [StringLength(30)]
        public string EmployeeName { get; set; }

        [Required]
        [StringLength(15)]
        public string Department { get; set; }

        [Required]
        [Range(0, 9999999.99)]
        public decimal Salary { get; set; }

        [Required]
        [StringLength(1)]
        public string Status { get; set; }
    }
}