"""
ASP.NET MVC Scaffold Generator
────────────────────────────────
Produces a complete, runnable ASP.NET Core MVC project structure.
When merged with LLM-generated business files and opened in Visual Studio,
pressing F5 / "Run" starts the project immediately.

Target framework: .NET 8 (net8.0) — simplest, most compatible.
"""

import uuid
import os


import re

def _project_name(module_name: str) -> str:
    """Derive a clean C# project name (PascalCase) from the module filename."""
    stem = os.path.splitext(module_name)[0]
    # Strip common VB prefixes (frm, mdl, cls, mod)
    for prefix in ("frm", "mdl", "cls", "mod"):
        if stem.lower().startswith(prefix):
            stem = stem[len(prefix):]
            break
            
    # Convert kebab-case, snake_case, dots, and spaces to camelCase
    # e.g., 'cobol-sample-project' -> 'cobolSampleProject'
    words = [w for w in re.split(r'[-_\s\.]+', stem) if w]
    if not words:
        return "migratedAppMvc"
        
    camel_stem = words[0].lower() + "".join(word.capitalize() for word in words[1:])
    
    # Ensure it starts with a letter
    if not camel_stem[0].isalpha():
        camel_stem = "app" + camel_stem
        
    return f"{camel_stem}Mvc"


def _namespace(project_name: str) -> str:
    # Ensure strictly alphanumeric and valid for C# namespace
    clean = re.sub(r'[^a-zA-Z0-9]', '', project_name)
    if not clean or not clean[0].isalpha():
        clean = "app" + clean
    # First letter should be lowercase to maintain camelCase
    return clean[0].lower() + clean[1:] if clean else "app"


# ── File generators ───────────────────────────────────────────────────────────

def _sln(project_name: str) -> str:
    proj_guid = str(uuid.uuid5(uuid.NAMESPACE_DNS, project_name)).upper()
    return f"""
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.8.34310.169
MinimumVisualStudioVersion = 10.0.40219.1
Project("{{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}}") = "{project_name}", "{project_name}\\{project_name}.csproj", "{{{proj_guid}}}"
EndProject
Global
\tGlobalSection(SolutionConfigurationPlatforms) = preSolution
\t\tDebug|Any CPU = Debug|Any CPU
\t\tRelease|Any CPU = Release|Any CPU
\tEndGlobalSection
\tGlobalSection(ProjectConfigurationPlatforms) = postSolution
\t\t{{{proj_guid}}}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
\t\t{{{proj_guid}}}.Debug|Any CPU.Build.0 = Debug|Any CPU
\t\t{{{proj_guid}}}.Release|Any CPU.ActiveCfg = Release|Any CPU
\t\t{{{proj_guid}}}.Release|Any CPU.Build.0 = Release|Any CPU
\tEndGlobalSection
\tGlobalSection(SolutionProperties) = preSolution
\t\tHideSolutionNode = FALSE
\tEndGlobalSection
EndGlobal
""".lstrip()


def _csproj(project_name: str) -> str:
    return """<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>{ns}</RootNamespace>
    <AssemblyName>{name}</AssemblyName>
  </PropertyGroup>

  <ItemGroup>
    <!-- Core MVC & Migration Adapters from 4.6.1 -->
    <PackageReference Include="Microsoft.AspNetCore.Mvc.Razor.RuntimeCompilation" Version="10.0.0" />
    <PackageReference Include="Microsoft.AspNetCore.SystemWebAdapters" Version="1.3.0" />
    
    <!-- Database Dependencies -->
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="10.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" Version="10.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.Tools" Version="10.0.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
    </PackageReference>
    
    <!-- Utilities -->
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
    <PackageReference Include="Dapper" Version="2.1.24" />
  </ItemGroup>

</Project>
""".format(ns=project_name, name=project_name)


def _program_cs(ns: str) -> str:
    return f"""using {ns}.Services;

var builder = WebApplication.CreateBuilder(args);

// ── Services ──────────────────────────────────────────────────────────────────
builder.Services.AddControllersWithViews()
    .AddRazorRuntimeCompilation();

// System.Web Adapters for 4.6.1 backwards compatibility
builder.Services.AddSystemWebAdapters();

// Register application services
builder.Services.AddScoped<IMigrationService, MigrationService>();

var app = builder.Build();

// ── Middleware ────────────────────────────────────────────────────────────────
if (!app.Environment.IsDevelopment())
{{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseAuthorization();

// ── Routes ────────────────────────────────────────────────────────────────────
app.MapControllerRoute(
    name: "default",
    pattern: "{{controller=Home}}/{{action=Index}}/{{id?}}");

app.Run();
"""


def _appsettings() -> str:
    return """{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "ConnectionStrings": {
    "DefaultConnection": ""
  }
}
"""


def _appsettings_dev() -> str:
    return """{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  }
}
"""


def _view_imports(ns: str) -> str:
    return f"""@using {ns}
@using {ns}.Models
@addTagHelper *, Microsoft.AspNetCore.Mvc.TagHelpers
"""


def _view_start() -> str:
    return """@{
    Layout = "_Layout";
}
"""


def _layout(project_name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>@ViewData["Title"] - {project_name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" />
    <link rel="stylesheet" href="~/css/site.css" asp-append-version="true" />
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" asp-controller="Home" asp-action="Index">{project_name}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" asp-controller="Home" asp-action="Index">Home</a>
                    </li>
                    <!-- NAV_LINKS_PLACEHOLDER -->
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <main role="main" class="pb-3">
            @RenderBody()
        </main>
    </div>

    <footer class="border-top footer text-muted mt-5 py-3">
        <div class="container text-center">
            <p>&copy; @DateTime.Now.Year {project_name} — Migrated by GOD-3000</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="~/js/site.js" asp-append-version="true"></script>
    @await RenderSectionAsync("Scripts", required: false)
</body>
</html>
"""


def _home_controller(ns: str) -> str:
    return f"""using Microsoft.AspNetCore.Mvc;

namespace {ns}.Controllers
{{
    public class HomeController : Controller
    {{
        public IActionResult Index()
        {{
            return View();
        }}

        public IActionResult Error()
        {{
            return View();
        }}
    }}
}}
"""


def _home_index(project_name: str) -> str:
    return f"""@{{
    ViewData["Title"] = "Home";
}}

<div class="jumbotron py-5">
    <h1 class="display-4">Welcome to {project_name}</h1>
    <p class="lead">
        This project was automatically migrated from legacy VB6/COBOL by <strong>GOD-3000</strong>.
    </p>
    <hr class="my-4" />
    <p>Use the navigation above to access migrated modules.</p>
    <div class="mt-4">
        <!-- HOME_LINKS_PLACEHOLDER -->
    </div>
</div>
"""


def _site_css() -> str:
    return """/* site.css - GOD-3000 Migrated Project */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f8f9fa;
}

.navbar-brand {
    font-weight: 700;
    letter-spacing: 0.02em;
}

.footer {
    background: #f8f9fa;
}

/* Form styling */
.form-control:focus {
    border-color: #0d6efd;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.btn-primary {
    padding: 8px 24px;
}
"""


def _site_js() -> str:
    return """// site.js - GOD-3000 Migrated Project
// Place custom JavaScript here
"""


def _migration_service(ns: str) -> str:
    return f"""using System;
using System.Threading.Tasks;

namespace {ns}.Services
{{
    /// <summary>
    /// Core interface for migrated business logic services.
    /// </summary>
    public interface IMigrationService
    {{
        Task<string> ExecuteLegacyModuleAsync(string moduleName, object parameters);
        bool ValidateState();
    }}

    /// <summary>
    /// Default implementation for the migration service.
    /// Acts as a bridge to underlying COBOL/VB6 migrated logic.
    /// </summary>
    public class MigrationService : IMigrationService
    {{
        public async Task<string> ExecuteLegacyModuleAsync(string moduleName, object parameters)
        {{
            // TODO: Implement actual interop or call to migrated C# module
            await Task.Delay(100); // Simulate work
            return $"Executed migrated module: {{moduleName}}";
        }}

        public bool ValidateState()
        {{
            return true;
        }}
    }}
}}
"""


def _gitignore() -> str:
    return """obj/
bin/
.vs/
*.user
*.suo
appsettings.Development.json
"""


# ── Main entry point ──────────────────────────────────────────────────────────

def build_project_scaffold(module_name: str) -> tuple[str, str, list[dict]]:
    """
    Generate all scaffold/boilerplate files for a runnable ASP.NET MVC project.

    Returns:
        project_name (str)  — e.g. "InvoiceMvc"
        namespace    (str)  — e.g. "InvoiceMvc"
        files        (list) — [{path, content}, ...] with paths relative to project root
    """
    project_name = _project_name(module_name)
    ns           = _namespace(project_name)
    p            = project_name  # short alias for inner paths

    files = [
        # ── Solution ──────────────────────────────────────────────────────────
        {"path": f"{project_name}.sln",                                     "content": _sln(project_name)},
        # ── Project file ──────────────────────────────────────────────────────
        {"path": f"{p}/{p}.csproj",                                         "content": _csproj(project_name)},
        # ── App entry point ───────────────────────────────────────────────────
        {"path": f"{p}/Program.cs",                                         "content": _program_cs(ns)},
        # ── Config ────────────────────────────────────────────────────────────
        {"path": f"{p}/appsettings.json",                                   "content": _appsettings()},
        {"path": f"{p}/appsettings.Development.json",                       "content": _appsettings_dev()},
        # ── Razor ─────────────────────────────────────────────────────────────
        {"path": f"{p}/Views/_ViewImports.cshtml",                          "content": _view_imports(ns)},
        {"path": f"{p}/Views/_ViewStart.cshtml",                            "content": _view_start()},
        {"path": f"{p}/Views/Shared/_Layout.cshtml",                        "content": _layout(project_name)},
        {"path": f"{p}/Views/Home/Index.cshtml",                            "content": _home_index(project_name)},
        # ── Home controller ───────────────────────────────────────────────────
        {"path": f"{p}/Controllers/HomeController.cs",                      "content": _home_controller(ns)},
        # ── Static files ──────────────────────────────────────────────────────
        {"path": f"{p}/wwwroot/css/site.css",                               "content": _site_css()},
        {"path": f"{p}/wwwroot/js/site.js",                                 "content": _site_js()},
        # ── Models & Services ─────────────────────────────────────────────────
        {"path": f"{p}/Models/.gitkeep",                                    "content": ""},
        {"path": f"{p}/Services/MigrationService.cs",                       "content": _migration_service(ns)},
        # ── Git ───────────────────────────────────────────────────────────────
        {"path": ".gitignore",                                               "content": _gitignore()},
    ]

    return project_name, ns, files


def merge_llm_files(
    scaffold_files: list[dict],
    llm_files:      list[dict],
    project_name:   str,
    namespace:      str,
) -> list[dict]:
    """
    Merge LLM-generated business files into the scaffold.

    LLM files have paths like:
        Controllers/frmInvoiceController.cs
        Models/InvoiceViewModel.cs
        Views/frmInvoice/Index.cshtml

    We prefix them with `<project_name>/` to put them inside the project folder.
    We also fix any namespace references if needed.
    """
    p = project_name
    merged = list(scaffold_files)

    # 1. Detect controllers to build dynamic UI links
    import re
    controllers = []
    for f in llm_files:
        path = f.get("path", "")
        content = f.get("content", "")
        if "controller" in path.lower() and path.endswith(".cs"):
            m = re.search(r"class\s+(\w+)Controller", content)
            if m and m.group(1) != "Home":
                controllers.append(m.group(1))
    
    controllers = list(dict.fromkeys(controllers))
    
    nav_links = ""
    home_links = ""
    for c in controllers:
        nav_links += f'                    <li class="nav-item"><a class="nav-link text-info" asp-controller="{c}" asp-action="Index">{c} Module</a></li>\n'
        home_links += f'        <a href="/{c}" class="btn btn-primary btn-lg me-2 mt-2">Open {c} Module</a>\n'

    # Inject links into scaffold layout
    for i in range(len(merged)):
        if "Views/Shared/_Layout.cshtml" in merged[i]["path"]:
            merged[i]["content"] = merged[i]["content"].replace("<!-- NAV_LINKS_PLACEHOLDER -->", nav_links)
        elif "Views/Home/Index.cshtml" in merged[i]["path"]:
            merged[i]["content"] = merged[i]["content"].replace("<!-- HOME_LINKS_PLACEHOLDER -->", home_links)

    # 2. Merge LLM files and unify namespaces
    for f in llm_files:
        orig_path = f.get("path", "")
        content   = f.get("content", "")

        # Unify namespace dynamically using Regex
        content = re.sub(r"namespace\s+[\w.]+", f"namespace {namespace}", content)

        # Fix placeholder strings (just in case they are in using statements or comments)
        content = (content
            .replace("YourAppNamespace", namespace)
            .replace("YourApp",          namespace)
            .replace("AppNamespace",     namespace))

        # Prefix with project inner folder if not already there
        if not orig_path.startswith(p + "/"):
            new_path = f"{p}/{orig_path}"
        else:
            new_path = orig_path

        # Remove _new suffix if LLM accidentally added it
        new_path = new_path.replace("_new.cs", ".cs").replace("_new.cshtml", ".cshtml")

        merged.append({"path": new_path, "content": content})

    return merged
