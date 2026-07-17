using cobolSampleProjectMvc.Models;
using System;

namespace cobolSampleProjectMvc
{
    public class CobolSampleProjectService
    {
        public double? Calculate(CobolCalculationViewModel model)
        {
            double result = 0;

            switch (model.Operation.ToLower())
            {
                case "add":
                    result = model.FirstNumber + model.SecondNumber;
                    break;
                case "subtract":
                    result = model.FirstNumber - model.SecondNumber;
                    break;
                case "multiply":
                    result = model.FirstNumber * model.SecondNumber;
                    break;
                case "divide":
                    if (model.SecondNumber == 0)
                    {
                        model.ErrorCode = 1; // Error code for division by zero
                        throw new DivideByZeroException("Cannot divide by zero.");
                    }

                    result = model.FirstNumber / model.SecondNumber;
                    model.ErrorCode = 0; // Success
                    break;
                default:
                    throw new InvalidOperationException("Invalid operation type.");
            }

            return result;
        }

        public string GetHelloMessage(string clientName)
        {
            if (string.IsNullOrWhiteSpace(clientName))
            {
                throw new ArgumentException("Client name cannot be empty.");
            }

            return $"COBOL: Hello received for name: {clientName}";
        }
    }
}