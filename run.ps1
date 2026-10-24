param([switch]$Demo, [string]$Project)
$ErrorActionPreference = 'Stop'
$executable = Join-Path $PSScriptRoot 'Trickster.exe'
if (-not (Test-Path -LiteralPath $executable)) { $executable = Join-Path $PSScriptRoot 'build\Trickster.exe' }
if (-not (Test-Path -LiteralPath $executable)) { $executable = Join-Path $PSScriptRoot 'dist\Trickster\Trickster.exe' }
if (-not (Test-Path -LiteralPath $executable)) { throw 'Run .\build.ps1 first.' }
$launchArguments = @()
if ($Demo) { $launchArguments += '--demo' }
if ($Project) { $resolvedProject = (Resolve-Path -LiteralPath $Project).Path; $launchArguments += '"' + $resolvedProject + '"' }
if ($launchArguments.Count) {
    Start-Process -FilePath $executable -WorkingDirectory $PSScriptRoot -ArgumentList $launchArguments -WindowStyle Normal
} else {
    Start-Process -FilePath $executable -WorkingDirectory $PSScriptRoot -WindowStyle Normal
}
