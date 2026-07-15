using empcrudMvc.Models;
using empcrudMvc.Services;
using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;

namespace empcrudMvc
{
    public class EMPCRUDController : Controller
    {
        private readonly IEMPCRUDService _service;

        public EMPCRUDController(IEMPCRUDService service)
        {
            _service = service;
        }

        public async Task<IActionResult> Index()
        {
            var employees = await _service.GetAllEmployeesAsync();
            return View(employees);
        }

        public IActionResult Create()
        {
            return View();
        }

        [HttpPost]
        public async Task<IActionResult> Create(EmployeeViewModel model)
        {
            if (ModelState.IsValid)
            {
                var result = await _service.CreateEmployeeAsync(model);
                if (result)
                    return RedirectToAction("Index");
                ModelState.AddModelError("Error", "Failed to create employee. Possible duplicate ID.");
            }
            return View(model);
        }

        public async Task<IActionResult> Edit(string id)
        {
            var employee = await _service.GetEmployeeByIdAsync(id);
            if (employee == null)
                return NotFound();

            return View(employee);
        }

        [HttpPost]
        public async Task<IActionResult> Edit(EmployeeViewModel model)
        {
            if (ModelState.IsValid)
            {
                var result = await _service.UpdateEmployeeAsync(model);
                if (result)
                    return RedirectToAction("Index");
                ModelState.AddModelError("Error", "Failed to update employee.");
            }
            return View(model);
        }

        public async Task<IActionResult> Delete(string id)
        {
            var employee = await _service.GetEmployeeByIdAsync(id);
            if (employee == null)
                return NotFound();

            return View(employee);
        }

        [HttpPost, ActionName("Delete")]
        public async Task<IActionResult> ConfirmDelete(string id)
        {
            var result = await _service.DeleteEmployeeAsync(id);
            if (result)
                return RedirectToAction("Index");
            return BadRequest("Failed to delete employee.");
        }
    }
}