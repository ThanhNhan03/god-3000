using System.ComponentModel.DataAnnotations;

namespace cobolSampleProjectMvc
{
    public class CobolCalculationViewModel
    {
        [Required(ErrorMessage = "First number is required.")]
        public double FirstNumber { get; set; }

        [Required(ErrorMessage = "Second number is required.")]
        public double SecondNumber { get; set; }

        public string Operation { get; set; } // "Add", "Subtract", "Multiply", "Divide"

        public double? Result { get; set; } // Nullable to handle operations where no result is defined

        public int? ErrorCode { get; set; } // Nullable for division error codes
    }
}