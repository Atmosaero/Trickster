# Building Trickster

The product version comes from `CMakeLists.txt`. `Trickster.exe --build-info` reports the version, short Git SHA and dirty state. Project format versions are independent; see [migration](PHYSICS_MIGRATION.md).

## Windows x64

Install a C++17 MSVC toolchain, Ninja, CMake 3.24+ and Qt 6.5+ for MSVC x64, including Widgets, OpenGLWidgets, Network and Test. Visual Studio discovery uses its `vswhere` installer tool. OpenGL is required for the viewport.

```powershell
.\build.ps1 -QtRoot 'C:\Qt\6.12.0\msvc2022_64'
.\run.ps1
```

Alternatively set `QT_ROOT` or `QTDIR`, or put Qt's `qmake`/`windeployqt` on PATH. An existing build's CMake cache can supply Qt. An explicit `-QtRoot` takes precedence. No machine-specific installation path is assumed.

`-BuildDirectory build-local` creates an isolated build; `-Targets Trickster,TricksterMVPTests` builds named targets. Close the editor before replacing its executable. To reuse a downloaded SDK, pass `-CMakeArguments '-DFETCHCONTENT_SOURCE_DIR_MUJOCO_SDK=C:/path/to/cached/mujoco_sdk-src'`.

CMake fetches the official unmodified MuJoCo **3.3.7 Windows x86_64** SDK and checks SHA-256 `1108ad01f6a1e63d42725188404c9af50b81902c368ef026d20d5148c115a08b`. The cache is under the build directory's `_deps`. Network access is needed for the initial download. There is no physics Python runtime or Bullet dependency.

## Portable packaging

```powershell
.\package.ps1 -BuildDirectory build -OutputDirectory dist/Trickster-local
```

Qt is resolved as for building. The VC runtime is discovered from `VCToolsRedistDir` or the selected Visual Studio installation. Explicit `-QtRoot` and `-CrtRoot` override discovery. `-NoArchive` prepares just the folder.

`package.ps1` uses [package-manifest.json](../scripts/package-manifest.json) for explicit runtime, guide, example and source lists. Guides/examples/licenses are stored once at the package root, alongside buildable `src`, `tests`, `scripts`, `third_party` and CMake/build scripts. There is no second `source/docs` or `source/examples` copy. Historical reports and experimental archives are separate [release attachments](RELEASES.md).

Local libraries are excluded by default. Add `-IncludeLocalLibrary` only for a private local package. `-PublicRelease` requires a clean matching executable/checkout, an empty output directory and tracked payload files; it rejects `-IncludeLocalLibrary`. It writes BUILD-INFO.txt, START-HERE.txt, a ZIP and a SHA-256 sidecar. It does not publish anything. All packaging modes require an empty output folder to prevent stale payloads.

The package includes Qt/VC/MuJoCo runtimes, synthetic examples, guides, notices and source. Extract the complete ZIP and run `Trickster.exe`. The editor starts empty. Python is needed only for the optional stdio bridge or development scripts.

## Other platforms and debugging

On other systems provide an installed `mujoco 3.3.7 EXACT CONFIG` CMake package and the Qt modules above. Only Windows x64 has been validated; no other-platform claim is made.

`-DTRICKSTER_DEBUG_SYMBOLS=ON` enables MSVC debug symbols in an optimized build. AddressSanitizer additionally uses `/fsanitize=address /Zi` and linker `/DEBUG /INCREMENTAL:NO`; its development runtime is not shipped. See [Testing](TESTING.md) for regression, independent consumer, physics and performance commands.
