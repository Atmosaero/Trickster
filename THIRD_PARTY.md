# Third-party components

Trickster source code and its original procedural mannequin are MIT licensed (LICENSE). No Cascadeur code, artwork, binaries or SDK is used. Inspiration is limited to the animation workflow.

## Qt 6.12.0

The Windows build dynamically links the unmodified Qt Core, Gui, Widgets, Network, OpenGL and OpenGLWidgets libraries and deploys the Windows platform/style plugins from the installed Qt SDK. The open-source LGPLv3 option is used. Qt DLLs are separate files and may be replaced with compatible modified builds. Trickster imposes no restriction on reverse engineering for debugging modifications to these libraries. Trickster source, build scripts and project code are provided here; the application is not statically linked to Qt.

- Qt source and build instructions: https://code.qt.io/qt/qtbase.git/tree/?h=6.12.0 and https://download.qt.io/archive/qt/6.12/6.12.0/submodules/
- Qt licensing: https://doc.qt.io/qt-6/licensing.html
- LGPLv3 and GPLv3 texts: licenses/LGPL-3.0-only.txt and licenses/GPL-3.0-only.txt.
- SDK-provided module inventory, component copyright notices, license expressions and references: licenses/qtbase-6.12.0.spdx.json. This is the SDK's complete qtbase inventory; not every platform-specific source component in it is deployed by this Windows application.
- Component license texts and extracted notices accompany that inventory in licenses/.

The Qt Test library is used for local verification only and is omitted from the portable application. SDK build tools are not redistributed.

## Microsoft C++ runtime

The portable build includes unmodified x64 DLLs from the installed MSVC redistributable directory. They are Microsoft redistributable components, separately licensed under the Visual Studio toolchain terms; they are not covered by Trickster's MIT license. Windows system OpenGL and platform libraries are not copied.

## Optional verification tools and fixtures

The Khronos glTF Validator npm package (Apache-2.0) is installed only under ignored artifacts/validator; it is not part of the application or its dependency chain. See https://github.com/KhronosGroup/glTF-Validator.

CesiumMan is used only as an external import/export test fixture under ignored artifacts/external. Copyright 2017 Cesium, CC BY 4.0; the Cesium logo has separate trademark terms. Its source README and attribution were downloaded alongside the fixture. It is not included in the shipped demo or portable archive. Source: https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CesiumMan.

No non-commercial dependency or content is used in Trickster's application code or bundled mannequin.


## Optional local character library

This local build optionally includes converted user-supplied assets from a user-selected source directory. Converted files under `library/TestCharacter` are user content, not MIT-licensed Trickster assets. No ownership or redistribution license is inferred for them, and the library is excluded from source control. Local-only packages may include them for the requesting user's workflow. Public release packages exclude the local library; no redistribution permission is inferred.

A compatible Godot executable was used as an external conversion tool against a copied temporary project. Godot is not bundled or linked into Trickster. Its GLTFDocument API is documented at https://docs.godotengine.org/en/stable/classes/class_gltfdocument.html.

## ufbx

FBX import statically links the unmodified ufbx decoder. The MIT alternative is selected. Copyright (c) 2020 Samuli Raivio. Upstream revision is recorded in third_party/ufbx/UPSTREAM.txt; the full license is in third_party/ufbx/LICENSE and licenses/ufbx-LICENSE.txt. Source: https://github.com/ufbx/ufbx.

## MuJoCo 3.3.7

The application dynamically links the official unmodified native CPU MuJoCo 3.3.7 library under Apache-2.0. The exact Windows SDK URL and SHA-256 are pinned in CMake and third_party/mujoco/UPSTREAM.txt. No Python, viewer executable or plugin DLL is required or shipped. Native runtime source/build instructions: https://github.com/google-deepmind/mujoco/tree/3.3.7. The license and complete SDK embedded-component notices are included in third_party/mujoco and licenses/MuJoCo-*.

Bullet is no longer linked, built or included as a source dependency. Its old license is retained only as historical attribution for previous releases; historical validation documents explicitly describe their earlier backend.

The portable application also includes the Qt JPEG image-format plugin; its notices are covered by the supplied qtbase inventory and component notices.

BoxTextured, AnimatedMorphCube and DamagedHelmet from the official Khronos glTF-Sample-Assets repository are optional local verification fixtures under ignored artifacts/external. They and their derived screenshots/exports are not part of the portable distribution. Their individual model licenses remain with their upstream assets.

## Local Epic mannequin scenes

The ignored `library/EpicMannequins` directory contains Manny and Quinn converted from locally installed Epic Unreal assets. Source packages, GLBs, textures and any local prepared projects are user content, not MIT-licensed Trickster assets. They are not added to source control. The isolated conversion scripts contain only tool orchestration and no Epic asset data. The local packaging script can copy an installed library with explicit `-IncludeLocalLibrary`; this does not grant redistribution rights. See [scene library workflow](docs/SCENE_LIBRARY.md).
