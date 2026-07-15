using empMvc.Models;

namespace empMvc
{
    public class FRM_EMPService
    {
        // Optional: Mock implementation to interact with a database or external API

        public FRM_EMPViewModel GetEmployee(string id)
        {
            // For demonstration purposes
            return new FRM_EMPViewModel
            {
                ID = id,
                Name = "John Doe",
                Dept = "IT",
                Salary = 50000.00m,
                Status = "A"
            };
        }
    }
}