# Ready-to-run Windows release

Download **Trickster-0.5.0-windows-x64.zip** from the repository's [Releases page](https://github.com/Atmosaero/Trickster/releases/tag/v0.5.0). Extract the complete archive, then double-click **Trickster.exe** inside the extracted folder. Keep the bundled DLLs and plugin directories together with the executable.

The Windows x64 package includes Qt, Microsoft VC runtime DLLs, native MuJoCo, licenses, source and synthetic example projects. Qt SDK, Python, Godot and Unreal Engine are not required. The editor starts empty. Choose the built-in mannequin or a template under Scene > Choose scene, or open your own FBX/glTF character.

User-supplied local model libraries and their animations are excluded from public releases. Physics tools remain experimental; the 62 open scientific acceptance gates are documented in [PHYSICS_RELIABILITY.md](PHYSICS_RELIABILITY.md).

Check the ZIP with `Get-FileHash .\Trickster-0.5.0-windows-x64.zip -Algorithm SHA256` and compare it with the attached `.sha256` file. BUILD-INFO.txt identifies the exact source commit; `Trickster.exe --build-info` reports the same identity. Other operating systems have not been validated for this release.

Public packages are built from a clean tagged checkout. `package.ps1 -PublicRelease` verifies the executable identity, refuses a nonempty output directory, excludes local libraries and uses explicit tracked payload lists. See [BUILD.md](BUILD.md) for build requirements.

## Optional evidence and experiment downloads

The release also provides [historical validation evidence](https://github.com/Atmosaero/Trickster/releases/download/v0.5.0/Trickster-0.5.0-validation-evidence.zip) and [full-body experimental projects](../examples/reliability/README.md), each with its SHA-256 sidecar. They are separate downloads, not required to run the editor. The evidence retains original build identities, failed reports and context; it is not a fresh combined run or dynamics certificate.

The release stores guides/examples/licenses once at the root alongside buildable source, using an explicit payload manifest. Its executable, bundled source and tag refer to the same clean commit.
