# PowerShell script to build and run the VB.NET and COBOL sample
$ErrorActionPreference = "Stop"

Write-Host "--- Checking Environment ---" -ForegroundColor Cyan

# 1. Check for COBOL compiler
$cobcPath = Get-Command cobc -ErrorAction SilentlyContinue
if (-not $cobcPath) {
    Write-Host "[WARNING] cobc (GnuCOBOL compiler) was not found in your system PATH." -ForegroundColor Yellow
    Write-Host "Please download and install GnuCOBOL for Windows from: https://sourceforge.net/projects/open-cobol/ or https://superbol.eu" -ForegroundColor Yellow
    Write-Host "After installation, add the 'bin' folder of GnuCOBOL to your environment PATH and run this script again." -ForegroundColor Yellow
    Write-Host "For demo purposes, we will try to build the VB.NET application anyway, but execution will fail unless CobolLib.dll is present." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Found GnuCOBOL: $($cobcPath.Source)" -ForegroundColor Green
    
    Write-Host "`n--- Compiling COBOL DLL ---" -ForegroundColor Cyan
    # Compile to a DLL. GnuCOBOL -m compile flag outputs a shared library.
    & cobc -m CobolLib.cob
    Write-Host "[OK] Compiled CobolLib.dll successfully." -ForegroundColor Green
}

# 2. Check for dotnet SDK
$dotnetPath = Get-Command dotnet -ErrorAction SilentlyContinue
if (-not $dotnetPath) {
    Write-Error "dotnet SDK is not installed or not in PATH."
}

Write-Host "`n--- Building VB.NET Project ---" -ForegroundColor Cyan
& dotnet build --configuration Debug

# 3. Copy DLL to output folder if it exists
if (Test-Path "CobolLib.dll") {
    $binDir = "bin/Debug/net10.0"
    if (-not (Test-Path $binDir)) {
        New-Item -ItemType Directory -Force -Path $binDir | Out-Null
    }
    Copy-Item "CobolLib.dll" -Destination "$binDir/CobolLib.dll" -Force
    Write-Host "[OK] Copied CobolLib.dll to executable directory." -ForegroundColor Green
    
    Write-Host "`n--- Running Sample Application ---" -ForegroundColor Cyan
    & dotnet run
} else {
    Write-Host "`n[ERROR] CobolLib.dll was not generated. VB.NET program cannot run without it." -ForegroundColor Red
}
