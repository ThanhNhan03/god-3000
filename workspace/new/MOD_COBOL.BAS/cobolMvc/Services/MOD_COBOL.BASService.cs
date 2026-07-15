using cobolMvc.Models;

namespace cobolMvc
{
    public class EmployeeService
    {
        private readonly List<EmployeeRecordViewModel> _employees = new();

        public List<EmployeeRecordViewModel> GetAllEmployees()
        {
            return _employees;
        }

        public EmployeeRecordViewModel GetEmployeeById(string id)
        {
            return _employees.FirstOrDefault(e => e.EmpID == id);
        }

        public void AddEmployee(EmployeeRecordViewModel employee)
        {
            _employees.Add(employee);
        }

        public void UpdateEmployee(EmployeeRecordViewModel updatedEmployee)
        {
            var original = _employees.FirstOrDefault(e => e.EmpID == updatedEmployee.EmpID);
            if (original != null)
            {
                original.EmpName = updatedEmployee.EmpName;
                original.EmpDept = updatedEmployee.EmpDept;
                original.EmpSalary = updatedEmployee.EmpSalary;
                original.EmpStatus = updatedEmployee.EmpStatus;
            }
        }

        public void DeleteEmployee(string id)
        {
            var employee = _employees.FirstOrDefault(e => e.EmpID == id);
            if (employee != null)
            {
                _employees.Remove(employee);
            }
        }

        public string DoubleToCobolSalary(double amount)
        {
            return amount.ToString("000000000");
        }

        public double CobolSalaryToDouble(string salaryStr)
        {
            return double.Parse(salaryStr) / 100;
        }

        public string TrimFixed(string text)
        {
            return text.Trim();
        }
    }
}