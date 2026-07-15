// EmployeeController.cs
using Microsoft.AspNetCore.Mvc;
using cobolProjectMvc.Models;
using cobolProjectMvc.Services;

namespace cobolProjectMvc
{
    public class EmployeeController : Controller
    {
        private readonly IEmployeeService _employeeService;

        public EmployeeController(IEmployeeService employeeService)
        {
            _employeeService = employeeService;
        }

        public IActionResult Index()
        {
            return View();
        }

        [HttpPost]
        public IActionResult Create(EmployeeViewModel model)
        {
            if (ModelState.IsValid)
            {
                var result = _employeeService.CreateEmployee(model);
                if (result)
                    ViewBag.Message = "Employee created successfully.";
                else
                    ViewBag.Message = "Failed to create employee.";
            }
            return View("Index", model);
        }

        [HttpPost]
        public IActionResult Read(string id)
        {
            var employee = _employeeService.GetEmployeeById(id);
            if (employee != null)
                return View("Index", employee);

            ViewBag.Message = "Employee not found.";
            return View("Index");
        }

        [HttpPost]
        public IActionResult Update(EmployeeViewModel model)
        {
            if (ModelState.IsValid)
            {
                var result = _employeeService.UpdateEmployee(model);
                if (result)
                    ViewBag.Message = "Employee updated successfully.";
                else
                    ViewBag.Message = "Failed to update employee.";
            }
            return View("Index", model);
        }

        [HttpPost]
        public IActionResult Delete(string id)
        {
            var result = _employeeService.DeleteEmployee(id);
            if (result)
                ViewBag.Message = "Employee deleted successfully.";
            else
                ViewBag.Message = "Failed to delete employee.";

            return View("Index");
        }
    }
}
