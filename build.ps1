param([switch]$Run, [switch]$Clean, [string]$QtRoot, [string]$BuildDirectory = 'build', [string[]]$CMakeArguments = @(), [string[]]$Targets = @())
$ErrorActionPreference = 'Stop'
$buildPath = if ([System.IO.Path]::IsPathRooted($BuildDirectory)) { [System.IO.Path]::GetFullPath($BuildDirectory) } else { [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $BuildDirectory)) }
. (Join-Path $PSScriptRoot 'scripts/windows-toolchain.ps1')
$QtRoot = Resolve-TricksterQtRoot $QtRoot $buildPath
$vsPath = Find-TricksterVisualStudio
$devCmd = Join-Path $vsPath 'Common7\Tools\VsDevCmd.bat'
$env:VSINSTALLDIR = $vsPath.TrimEnd('\') + '\'
$env:VCINSTALLDIR = Join-Path $env:VSINSTALLDIR 'VC\'
$env:VSLANG = '1033'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$devEnvironment = & $env:ComSpec /d /c "chcp 65001 >nul && call `"$devCmd`" -no_logo -arch=x64 -host_arch=x64 >nul && set"
if ($LASTEXITCODE -ne 0) { throw 'MSVC environment setup failed.' }
foreach ($line in $devEnvironment) {
    if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') }
}
$env:VSLANG = '1033'
$compilerLocale = Join-Path $env:VCToolsInstallDir 'bin\Hostx64\x64'
$includePrefix = 'Note: including file: '
if (-not (Test-Path -LiteralPath (Join-Path $compilerLocale '1033')) -and (Test-Path -LiteralPath (Join-Path $compilerLocale '1049'))) { $includePrefix = 'Примечание: включение файла: ' }
& cmake -S $PSScriptRoot -B "$buildPath" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_PREFIX_PATH=$QtRoot" "-DTRICKSTER_MSVC_INCLUDE_PREFIX=$includePrefix" @CMakeArguments
if ($LASTEXITCODE -ne 0) { throw 'Configure failed.' }
if ($Clean) { & cmake --build "$buildPath" --target clean }
$buildArguments = @("--build", $buildPath, "--parallel", "6")
if ($Targets.Count) { $buildArguments += "--target"; $buildArguments += $Targets }
& cmake @buildArguments
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
if ($Run) { Start-Process -FilePath (Join-Path $buildPath 'Trickster.exe') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden }
