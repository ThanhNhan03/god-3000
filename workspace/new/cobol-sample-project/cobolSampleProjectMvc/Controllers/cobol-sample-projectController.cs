using Microsoft.AspNetCore.Mvc;
using cobolSampleProjectMvc.Models;
using cobolSampleProjectMvc.Services;

namespace cobolSampleProjectMvc
{
    public class CobolSampleProjectController : Controller
    {
        private readonly CobolSampleProjectService _service;

        public CobolSampleProjectController(CobolSampleProjectService service)
        {
            _service = service;
        }

        [HttpGet]
        public IActionResult Index()
        {
            return View();
        }

        [HttpPost]
        public IActionResult PerformCalculation(CobolCalculationViewModel model)
        {
            if (!ModelState.IsValid)
            {
                return View("Index", model);
            }

            try
            {
                model.Result = _service.Calculate(model);
                return View("Index", model);
            }
            catch (Exception ex)
            {
                ModelState.AddModelError("", $"Error: {ex.Message}");
                return View("Index", model);
            }
        }

        [HttpPost]
        public IActionResult SayHello(string clientName)
        {
            string message = _service.GetHelloMessage(clientName);
            TempData["message"] = message;
            return RedirectToAction(nameof(Index));
        }
    }
}