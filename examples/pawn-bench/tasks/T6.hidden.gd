

func _test_hidden_old_save_fields() -> void:
	print("-- hidden: old save missing fields")
	GameSim.set_save_root("user://test/")
	_hero(true)
	_check(bool(GameSim.save_snapshot().get("ok", false)), "hidden: the hero saves")
	var path: String = GameSim._slot_path(GameSim.active_id)
	var old: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	for key in ["warps", "materials", "death", "shield_until", "follow_id", "effect", "found_popup"]:
		old.erase(key)
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(old))
	file.close()
	_check(bool(GameSim.load_snapshot().get("ok", false)), "hidden: the old save loads")
	GameSim._store_peer("1")
	GameSim._bind_peer("1")
	_check(typeof(GameSim.state.get("death")) == TYPE_DICTIONARY and not GameSim.is_down(), "hidden: a missing death field loads as alive")
	_check(typeof(GameSim.state.get("warps")) == TYPE_INT or typeof(GameSim.state.get("warps")) == TYPE_FLOAT, "hidden: a missing warps count loads as a number")
	_check(typeof(GameSim.state.get("materials")) == TYPE_DICTIONARY, "hidden: a missing materials bag loads empty")
	_check(is_equal_approx(GameSim.death_remaining(), 0.0), "hidden: death_remaining works on the old save")
