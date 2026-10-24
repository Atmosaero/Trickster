param(
    [string]$BuildDirectory = 'build',
    [switch]$NoArchive,
    [switch]$PublicRelease,
    [switch]$IncludeLocalLibrary,
    [string]$OutputDirectory = 'dist/Trickster',
    [string]$QtRoot,
    [string]$CrtRoot
)
$ErrorActionPreference = 'Stop'
$buildPath = if ([System.IO.Path]::IsPathRooted($BuildDirectory)) { [System.IO.Path]::GetFullPath($BuildDirectory) } else { [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $BuildDirectory)) }
$destination = if ([System.IO.Path]::IsPathRooted($OutputDirectory)) { [System.IO.Path]::GetFullPath($OutputDirectory) } else { [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $OutputDirectory)) }
$versionSource = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'CMakeLists.txt')
if ($versionSource -notmatch 'project\(Trickster VERSION ([0-9]+\.[0-9]+\.[0-9]+)') { throw 'Cannot read product version.' }
$productVersion = $matches[1]
$archive = Join-Path (Split-Path -Parent $destination) "Trickster-$productVersion-windows-x64.zip"
if (-not $NoArchive -and (Test-Path -LiteralPath $archive)) { throw "Archive already exists; choose a new output parent: $archive" }
if ($PublicRelease -and $IncludeLocalLibrary) { throw 'Public releases cannot include local libraries.' }
if ((Test-Path -LiteralPath $destination) -and (Get-ChildItem -LiteralPath $destination -Force | Select-Object -First 1)) { throw 'Package output must be an empty directory to avoid stale payloads.' }
if ($PublicRelease) {
    $pending = & git -c "safe.directory=$PSScriptRoot" -C $PSScriptRoot status --porcelain
    if ($LASTEXITCODE -ne 0 -or $pending) { throw 'Public releases require a clean Git checkout.' }
    $releaseHead = (& git -c "safe.directory=$PSScriptRoot" -C $PSScriptRoot rev-parse --short HEAD).Trim()
    $releaseBuild = (& (Join-Path $buildPath 'Trickster.exe') --build-info | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $releaseBuild -ne "Trickster $productVersion ($releaseHead)") { throw 'The executable must match the clean release commit and product version.' }
}
. (Join-Path $PSScriptRoot 'scripts/windows-toolchain.ps1')
$QtRoot = Resolve-TricksterQtRoot $QtRoot $buildPath
$CrtRoot = Resolve-TricksterCrtRoot $CrtRoot
$manifest = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'scripts/package-manifest.json') | ConvertFrom-Json
$gitArguments = @('-c', "safe.directory=$PSScriptRoot", '-C', $PSScriptRoot, 'ls-files', '--cached')
if (-not $PublicRelease) { $gitArguments += @('--others', '--exclude-standard') }
$projectPaths = @(& git @gitArguments)
if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate source files; package from a Git checkout.' }
$payload = @($manifest.files) + @($manifest.guides) + @($manifest.guideAssets) + @($manifest.examples)
foreach ($folder in $manifest.sourceDirectories) {
    $payload += @($projectPaths | Where-Object { $_.StartsWith($folder + '/') })
}
$payload = @($payload | Sort-Object -Unique)
# Resolve and validate everything before creating any output.
foreach ($relative in $payload) {
    $source = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $relative))
    if (-not $source.StartsWith($PSScriptRoot.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw "Payload escapes the project: $relative" }
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing package payload: $relative" }
    if ($PublicRelease -and $projectPaths -notcontains $relative) { throw "Untracked public payload: $relative" }
}
$runtimeFiles = @()
foreach ($name in @('Trickster.exe', 'TricksterPhysicsReplay.exe', 'mujoco.dll')) { $runtimeFiles += @{ Source = Join-Path $buildPath $name; Target = $name } }
foreach ($name in $manifest.qtLibraries) { $runtimeFiles += @{ Source = Join-Path $QtRoot "bin/$name"; Target = $name } }
foreach ($plugin in $manifest.qtPlugins) { $runtimeFiles += @{ Source = Join-Path $QtRoot "plugins/$plugin"; Target = $plugin } }
foreach ($plugin in $manifest.optionalQtPlugins) {
    $source = Join-Path $QtRoot "plugins/$plugin"
    if (Test-Path -LiteralPath $source -PathType Leaf) { $runtimeFiles += @{ Source = $source; Target = $plugin } }
}
foreach ($dll in Get-ChildItem -LiteralPath $CrtRoot -Filter '*.dll' -File) { $runtimeFiles += @{ Source = $dll.FullName; Target = $dll.Name } }
foreach ($file in $runtimeFiles) {
    if (-not (Test-Path -LiteralPath $file.Source -PathType Leaf)) { throw "Missing runtime file: $($file.Source)" }
}
New-Item -ItemType Directory -Path $destination -Force | Out-Null
foreach ($relative in $payload) {
    $target = Join-Path $destination $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $relative) -Destination $target -Force
}
foreach ($file in $runtimeFiles) {
    $target = Join-Path $destination $file.Target
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $file.Source -Destination $target -Force
}
if ($IncludeLocalLibrary -and (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'library'))) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'library') -Destination $destination -Recurse -Force
}
Set-Content -LiteralPath (Join-Path $destination 'qt.conf') -Encoding ASCII -Value "[Paths]`nPlugins=."
if ($PublicRelease) { Set-Content -LiteralPath (Join-Path $destination 'BUILD-INFO.txt') -Encoding ASCII -Value $releaseBuild }
$startText = @(
    'Trickster for Windows x64',
    'Extract the entire ZIP into a folder, then double-click Trickster.exe.',
    'No Qt SDK, Python, Unreal Engine, Godot or development tools are required to run.',
    'Start empty; choose a built-in mannequin/template or open your FBX/GLB/glTF.',
    'Guides and examples are in docs/ and examples/. Buildable source is at this root.',
    'Historical evidence and large experiments are separate release downloads.',
    'Physics is experimental; see docs/PHYSICS_RELIABILITY.md.'
)
Set-Content -LiteralPath (Join-Path $destination 'START-HERE.txt') -Encoding UTF8 -Value $startText
if (-not $NoArchive) {
    Compress-Archive -LiteralPath $destination -DestinationPath $archive
    $checksum = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath ($archive + '.sha256') -Encoding ASCII -Value "$checksum  $(Split-Path -Leaf $archive)"
    Write-Output "Archive: $archive"
}
Write-Output "Ready: $destination\Trickster.exe"
