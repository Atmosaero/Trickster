# Optional local scene libraries

Trickster starts empty. The built-in mannequin and synthetic examples need no external assets. Local catalogs live under ignored `library`; user-supplied geometry/textures are not MIT-licensed Trickster content and are excluded from public packages. See [third-party notices](../THIRD_PARTY.md).

## Manny and Quinn

An installed `library/EpicMannequins` catalog adds Manny/Quinn to **Scene > Choose scene > Characters**. Prepared `.trickster` rest scenes embed geometry/textures, explicit IK chains and mirror pairs, with no animations. GLBs can remain separately under `resources`.

For assets you are entitled to use, convert from an installed Unreal project into isolated staging:

```powershell
python scripts/import-epic-mannequins.py --engine 'C:\Epic Games\UE_5.8' --source 'C:\Projects\MyGame\Content\Characters\Mannequins' --asset-root '/Game/Characters/Mannequins'
```

`--source` must contain Meshes, Materials and Textures dependencies; `--asset-root` must match the original package mount. Conversion does not edit the source project. Unreal's PythonScriptPlugin and GLTFExporter are conversion-only requirements.

The converter exports LOD 0 skinning, metre/Y-up coordinates and baked textures into self-contained GLBs, disables animation export and checks for an unanimated skinned mesh. Review `export-report.json` warnings. Open each GLB, use Character profile > Suggest, review roles, axes, IK bend directions and mirror pairs, save as `Manny.trickster` / `Quinn.trickster` and update the catalog. A humanoid/IK profile does not supply validated anatomical limits automatically.

## Resource-only catalogs

Set `"resourceOnly": true` in a catalog to exclude that directory and descendants from scene selection, folder fallback and Recent. Files remain available through File > Open. The optional Godot TestCharacter converter retains this setting; it does not replace the built-in mannequin/templates.

No local model library is distributed publicly. `package.ps1 -IncludeLocalLibrary` is an explicit private-packaging option, incompatible with `-PublicRelease`; it grants no redistribution rights.
