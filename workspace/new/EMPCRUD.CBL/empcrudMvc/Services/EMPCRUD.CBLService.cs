using empcrudMvc.Models;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace empcrudMvc
{
    public interface IEMPCRUDService
    {
        Task<List<EmployeeViewModel>> GetAllEmployeesAsync();
        Task<EmployeeViewModel> GetEmployeeByIdAsync(string id);
        Task<bool> CreateEmployeeAsync(EmployeeViewModel model);
        Task<bool> UpdateEmployeeAsync(EmployeeViewModel model);
        Task<bool> DeleteEmployeeAsync(string id);
    }

    public class EMPCRUDService : IEMPCRUDService
    {
        private static List<EmployeeViewModel> _employees = new List<EmployeeViewModel>();

        public Task<List<EmployeeViewModel>> GetAllEmployeesAsync()
        {
            return Task.FromResult(_employees);
        }

        public Task<EmployeeViewModel> GetEmployeeByIdAsync(string id)
        {
            var employee = _employees.FirstOrDefault(e => e.EmployeeId == id);
            return Task.FromResult(employee);
        }

        public Task<bool> CreateEmployeeAsync(EmployeeViewModel model)
        {
            if (_employees.Any(e => e.EmployeeId == model.EmployeeId))
                return Task.FromResult(false);

            _employees.Add(model);
            return Task.FromResult(true);
        }

        public Task<bool> UpdateEmployeeAsync(EmployeeViewModel model)
        {
            var employee = _employees.FirstOrDefault(e => e.EmployeeId == model.EmployeeId);
            if (employee == null)
                return Task.FromResult(false);

            employee.EmployeeName = model.EmployeeName;
            employee.Department = model.Department;
            employee.Salary = model.Salary;
            employee.Status = model.Status;

            return Task.FromResult(true);
        }

        public Task<bool> DeleteEmployeeAsync(string id)
        {
            var employee = _employees.FirstOrDefault(e => e.EmployeeId == id);
            if (employee == null)
                return Task.FromResult(false);

            _employees.Remove(employee);
            return Task.FromResult(true);
        }
    }
}