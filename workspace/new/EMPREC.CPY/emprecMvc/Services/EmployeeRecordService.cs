using emprecMvc.Models;
using System.Collections.Generic;
using System.Linq;

namespace emprecMvc
{
    public class EmployeeRecordService
    {
        private readonly List<EmployeeRecord> _employeeRecords = new();

        public IEnumerable<EmployeeRecord> GetAllEmployeeRecords()
        {
            return _employeeRecords;
        }

        public EmployeeRecord GetEmployeeRecordById(string id)
        {
            return _employeeRecords.FirstOrDefault(e => e.EmployeeId == id);
        }

        public void AddEmployeeRecord(EmployeeRecordViewModel model)
        {
            var newRecord = new EmployeeRecord
            {
                EmployeeId = model.EmployeeId,
                EmployeeName = model.EmployeeName,
                Department = model.Department,
                Salary = model.Salary,
                Status = model.Status
            };
            _employeeRecords.Add(newRecord);
        }

        public void UpdateEmployeeRecord(string id, EmployeeRecordViewModel model)
        {
            var record = GetEmployeeRecordById(id);
            if (record != null)
            {
                record.EmployeeName = model.EmployeeName;
                record.Department = model.Department;
                record.Salary = model.Salary;
                record.Status = model.Status;
            }
        }

        public void DeleteEmployeeRecord(string id)
        {
            var record = GetEmployeeRecordById(id);
            if (record != null)
            {
                _employeeRecords.Remove(record);
            }
        }
    }
}