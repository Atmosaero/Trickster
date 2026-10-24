extends SceneTree

func _initialize() -> void:
    call_deferred("convert")

func get_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node
    for child in node.get_children():
        var found = get_player(child)
        if found != null:
            return found
    return null

func convert() -> void:
    var args = OS.get_cmdline_user_args()
    if args.size() != 2:
        push_error("Expected resource path and destination directory")
        quit(1)
        return
    var packed = load(args[0]) as PackedScene
    if packed == null:
        quit(2)
        return
    var original = packed.instantiate()
    var player = get_player(original)
    var names: Array[String] = [""]
    if player != null:
        for clip in player.get_animation_list():
            if clip != "RESET":
                names.append(String(clip))
    original.free()
    DirAccess.make_dir_recursive_absolute(args[1])
    var entries = []
    for clip in names:
        var character = packed.instantiate()
        root.add_child(character)
        var animation_player = get_player(character)
        if animation_player != null:
            var animation = animation_player.get_animation(clip) if clip != "" else null
            for library_name in animation_player.get_animation_library_list():
                animation_player.remove_animation_library(library_name)
            if animation != null:
                var library = AnimationLibrary.new()
                library.add_animation(clip, animation)
                animation_player.add_animation_library("", library)
        var tree = character.find_child("AnimationTree", true, false)
        if tree is AnimationTree:
            tree.active = false
        var document = GLTFDocument.new()
        var state = GLTFState.new()
        var result = document.append_from_scene(character, state)
        if result != OK:
            push_error("Cannot convert " + clip + ": " + error_string(result))
            quit(3)
            return
        var file_name = "TestCharacter_Rest.glb" if clip == "" else clip.validate_filename() + ".glb"
        result = document.write_to_filesystem(state, args[1].path_join(file_name))
        if result != OK:
            push_error("Cannot write " + file_name)
            quit(4)
            return
        entries.append({"name": "TestCharacter · Rest" if clip == "" else clip.trim_prefix("HumanM_").replace("_", " "), "file": file_name, "category": "Characters" if clip == "" else "Motion clips", "description": "TestCharacter / " + ("Rest pose" if clip == "" else clip)})
        print("EXPORTED ", file_name)
        character.free()
    var manifest = FileAccess.open(args[1].path_join("catalog.json"), FileAccess.WRITE)
    manifest.store_string(JSON.stringify({"title": "TestCharacter", "resourceOnly": true, "entries": entries}, "\t"))
    print("TRICKSTER_CONVERTED ", entries.size())
    quit(0)
