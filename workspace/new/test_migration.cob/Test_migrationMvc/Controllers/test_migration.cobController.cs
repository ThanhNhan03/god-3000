using Microsoft.AspNetCore.Mvc;
using TestMigration.Models;

namespace TestMigration.Controllers
{
    public class TestMigrationCobController : Controller
    {
        // GET: /TestMigrationCob/Index
        [HttpGet]
        public IActionResult Index()
        {
            return View(new SumViewModel());
        }

        // POST: /TestMigrationCob/Index
        [HttpPost]
        public IActionResult Index(SumViewModel model)
        {
            if (ModelState.IsValid)
            {
                model.Result = model.Num1 + model.Num2;
                ViewBag.Message = $"Total Sum: {model.Result}";
            }
            else
            {
                ViewBag.Message = "Invalid input. Please try again.";
            }

            return View(model);
        }
    }
}