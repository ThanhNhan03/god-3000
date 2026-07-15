using Microsoft.AspNetCore.Mvc;
using cobolMvc.Models;
using cobolMvc.Services;

namespace cobolMvc
{
    public class MOD_COBOLController : Controller
    {
        private readonly EmployeeService _employeeService;

        public MOD_COBOLController(EmployeeService employeeService)
        {
            _employeeService = employeeService;
        }

        public IActionResult Index()
        {
            var employees = _employeeService.GetAllEmployees();
            return View(employees);
        }

        [HttpPost]
        public IActionResult AddEmployee(EmployeeRecordViewModel viewModel)
        {
            if (ModelState.IsValid)
            {
                _employeeService.AddEmployee(viewModel);
                return RedirectToAction("Index");
            }
            return View(viewModel);
        }

        public IActionResult EditEmployee(string id)
        {
            var employee = _employeeService.GetEmployeeById(id);
            return View(employee);
        }

        [HttpPost]
        public IActionResult EditEmployee(EmployeeRecordViewModel viewModel)
        {
            if (ModelState.IsValid)
            {
                _employeeService.UpdateEmployee(viewModel);
                return RedirectToAction("Index");
            }
            return View(viewModel);
        }

        public IActionResult DeleteEmployee(string id)
        {
            _employeeService.DeleteEmployee(id);
            return RedirectToAction("Index");
        }
    }
}