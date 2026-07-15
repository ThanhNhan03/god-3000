using Microsoft.AspNetCore.Mvc;
using empMvc.Models;

namespace empMvc
{
    public class FRM_EMPController : Controller
    {
        // GET: /FRM_EMP/
        public IActionResult Index()
        {
            return View(new FRM_EMPViewModel());
        }

        // POST: Create Employee
        [HttpPost]
        public IActionResult Create(FRM_EMPViewModel model)
        {
            if (ModelState.IsValid)
            {
                TempData["Message"] = "Employee Created Successfully!";
                return RedirectToAction("Index");
            }
            return View("Index", model);
        }

        // POST: Read Employee (mock fetching)
        [HttpPost]
        public IActionResult Read(FRM_EMPViewModel model)
        {
            model.Name = "John Doe"; // Example data
            model.Dept = "IT";
            model.Salary = 50000.00m;
            model.Status = "A";

            TempData["Message"] = "Employee Retrieved Successfully!";
            return View("Index", model);
        }

        // POST: Update Employee
        [HttpPost]
        public IActionResult Update(FRM_EMPViewModel model)
        {
            if (ModelState.IsValid)
            {
                TempData["Message"] = "Employee Updated Successfully!";
                return RedirectToAction("Index");
            }
            return View("Index", model);
        }

        // POST: Delete Employee
        [HttpPost]
        public IActionResult Delete(FRM_EMPViewModel model)
        {
            TempData["Message"] = "Employee Deleted Successfully!";
            return RedirectToAction("Index");
        }

        // POST: Clear Form
        [HttpPost]
        public IActionResult Clear()
        {
            TempData["Message"] = "Form Cleared!";
            return RedirectToAction("Index", new FRM_EMPViewModel());
        }
    }
}