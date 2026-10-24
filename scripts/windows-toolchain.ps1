function Resolve-TricksterQtRoot([string]$Requested, [string]$BuildPath) {
    $candidates = @()
    if ($Requested) { $candidates = @($Requested) } else {
        $candidates += @($env:QT_ROOT, $env:QTDIR) | Where-Object { $_ }
        $cache = Join-Path $BuildPath 'CMakeCache.txt'
        if (Test-Path -LiteralPath $cache) {
            foreach ($line in Get-Content -LiteralPath $cache) {
                if ($line -match '^CMAKE_PREFIX_PATH:[^=]+=(.*)$') { $candidates += $matches[1].Split(';') }
                if ($line -match '^Qt6_DIR:[^=]+=(.*)$') { $candidates += [System.IO.Path]::GetFullPath((Join-Path $matches[1] '../../..')) }
            }
        }
        foreach ($name in @('windeployqt.exe', 'qmake6.exe', 'qmake.exe')) {
            $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($command) { $candidates += Split-Path -Parent (Split-Path -Parent $command.Source) }
        }
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath (Join-Path $candidate 'lib/cmake/Qt6/Qt6Config.cmake'))) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }
    throw 'Qt 6 MSVC SDK not found. Pass -QtRoot, set QT_ROOT/QTDIR, or put Qt tools on PATH.'
}

function Find-TricksterVisualStudio {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
    if (-not (Test-Path -LiteralPath $vswhere)) {
        $command = Get-Command vswhere.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command) { $vswhere = $command.Source }
    }
    if (Test-Path -LiteralPath $vswhere) {
        $installation = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        if ($LASTEXITCODE -eq 0 -and $installation) { return ($installation | Select-Object -First 1).Trim() }
    }
    if ($env:VSINSTALLDIR -and (Test-Path -LiteralPath (Join-Path $env:VSINSTALLDIR 'Common7/Tools/VsDevCmd.bat'))) { return $env:VSINSTALLDIR }
    throw 'MSVC C++ tools were not found. Install Visual Studio C++ build tools or use its developer shell.'
}

function Resolve-TricksterCrtRoot([string]$Requested) {
    if ($Requested) {
        $candidates = @($Requested)
    } else {
        $redistRoots = @()
        if ($env:VCToolsRedistDir) { $redistRoots += $env:VCToolsRedistDir }
        try {
            $vs = Find-TricksterVisualStudio
            $redist = Join-Path $vs 'VC/Redist/MSVC'
            if (Test-Path -LiteralPath $redist) {
                $redistRoots += @(Get-ChildItem -LiteralPath $redist -Directory | Sort-Object { if ($_.Name -match '^\d+\.\d+(\.\d+){0,2}$') { [version]$_.Name } else { [version]'0.0' } } -Descending | ForEach-Object FullName)
            }
        } catch { Write-Verbose $_ }
        $candidates = @()
        foreach ($redistRoot in $redistRoots) {
            $x64 = Join-Path $redistRoot 'x64'
            if (Test-Path -LiteralPath $x64) {
                $candidates += @(Get-ChildItem -LiteralPath $x64 -Directory -Filter 'Microsoft.VC*.CRT' | ForEach-Object FullName)
            }
        }
    }
    foreach ($candidate in $candidates) {
        if ((Test-Path -LiteralPath (Join-Path $candidate 'vcruntime140.dll')) -and (Test-Path -LiteralPath (Join-Path $candidate 'msvcp140.dll'))) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }
    throw 'VC x64 runtime not found. Pass -CrtRoot with its Microsoft.VC*.CRT directory.'
}
