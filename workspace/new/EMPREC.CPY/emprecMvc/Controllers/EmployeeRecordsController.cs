using emprecMvc.Models;
using emprecMvc.Services;
using Microsoft.AspNetCore.Mvc;
using System.Linq;

namespace emprecMvc
{
    public class EmployeeRecordsController : Controller
    {
        private readonly EmployeeRecordService _service;

        public EmployeeRecordsController(EmployeeRecordService service)
        {
            _service = service;
        }

        // GET: EmployeeRecords/Index
        public IActionResult Index()
        {
            var employeeRecords = _service.GetAllEmployeeRecords();
            return View(employeeRecords);
        }

        // GET: EmployeeRecords/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: EmployeeRecords/Create
        [HttpPost]
        [ValidateAntiForgeryToken]
        public IActionResult Create(EmployeeRecordViewModel model)
        {
            if (ModelState.IsValid)
            {
                _service.AddEmployeeRecord(model);
                return RedirectToAction("Index");
            }
            return View(model);
        }

        // GET: EmployeeRecords/Edit/{id}
        public IActionResult Edit(string id)
        {
            var record = _service.GetEmployeeRecordById(id);
            if (record == null)
                return NotFound();

            return View(record);
        }

        // POST: EmployeeRecords/Edit/{id}
        [HttpPost]
        [ValidateAntiForgeryToken]
        public IActionResult Edit(string id, EmployeeRecordViewModel model)
        {
            if (ModelState.IsValid)
            {
                _service.UpdateEmployeeRecord(id, model);
                return RedirectToAction("Index");
            }
            return View(model);
        }

        // GET: EmployeeRecords/Delete/{id}
        public IActionResult Delete(string id)
        {
            var record = _service.GetEmployeeRecordById(id);
            if (record == null)
                return NotFound();

            return View(record);
        }

        // POST: EmployeeRecords/Delete/{id}
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public IActionResult DeleteConfirmed(string id)
        {
            _service.DeleteEmployeeRecord(id);
            return RedirectToAction("Index");
        }
    }
}