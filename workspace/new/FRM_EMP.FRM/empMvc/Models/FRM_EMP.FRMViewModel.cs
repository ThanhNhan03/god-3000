using System.ComponentModel.DataAnnotations;

namespace empMvc
{
    public class FRM_EMPViewModel
    {
        [Required]
        [MaxLength(5)]
        [Display(Name = "Employee ID (5 chars):")]
        public string ID { get; set; }

        [MaxLength(30)]
        [Display(Name = "Name (30 chars):")]
        public string Name { get; set; }

        [MaxLength(15)]
        [Display(Name = "Department (15 chars):")]
        public string Dept { get; set; }

        [Range(0, double.MaxValue)]
        [Display(Name = "Salary (Up to 9 digits):")]
        public decimal? Salary { get; set; }

        [MaxLength(1)]
        [Display(Name = "Status (Active/In-Active):")]
        public string Status { get; set; }
    }
}