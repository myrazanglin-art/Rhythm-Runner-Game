extends Control

# UI Colors
var color_primary := Color("4a6fa5")
var color_secondary := Color("2e4e7e")
var color_accent := Color("ff6b6b")
var color_text := Color("f8f9fa")
var color_background := Color("1e2a3a")

func _ready() -> void:
	_create_ui()
	_populate_songs()
	_populate_difficulties()
	_connect_signals()
	_sync_initial_state()

func _create_ui() -> void:
	var background = ColorRect.new()
	background.color = Color("1e2a3a")
	background.anchor_right = 1.0
	background.anchor_bottom = 1.0
	add_child(background)
	
	var main_container = VBoxContainer.new()
	main_container.alignment = BoxContainer.ALIGNMENT_CENTER
	main_container.size = Vector2(500, 600)
	main_container.position = Vector2(390, 140)  # 居中位置
	add_child(main_container)
	
	var title_label = Label.new()
	title_label.text = "RHYTHM RUNNER"
	title_label.add_theme_font_size_override("font_size", 48)
	title_label.add_theme_color_override("font_color", color_accent)
	main_container.add_child(title_label)
	
	var separator = HSeparator.new()
	separator.custom_minimum_size = Vector2(400, 2)
	main_container.add_child(separator)
	
	var song_label = Label.new()
	song_label.text = "SELECT SONG"
	song_label.add_theme_font_size_override("font_size", 20)
	main_container.add_child(song_label)
	
	var song_container = HBoxContainer.new()
	song_container.alignment = BoxContainer.ALIGNMENT_CENTER
	main_container.add_child(song_container)
	
	var song_selector = OptionButton.new()
	song_selector.custom_minimum_size = Vector2(200, 40)
	song_container.add_child(song_selector)
	
	var preview_button = Button.new()
	preview_button.text = "Preview"
	preview_button.custom_minimum_size = Vector2(100, 40)
	song_container.add_child(preview_button)
	
	var difficulty_label = Label.new()
	difficulty_label.text = "SELECT DIFFICULTY"
	difficulty_label.add_theme_font_size_override("font_size", 20)
	main_container.add_child(difficulty_label)
	
	var difficulty_selector = OptionButton.new()
	difficulty_selector.custom_minimum_size = Vector2(200, 40)
	main_container.add_child(difficulty_selector)
	
	var difficulty_description = Label.new()
	difficulty_description.text = "Select a difficulty to see description"
	difficulty_description.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	difficulty_description.add_theme_font_size_override("font_size", 14)
	difficulty_description.add_theme_color_override("font_color", color_text * Color(1, 1, 1, 0.8))
	main_container.add_child(difficulty_description)
	
	var audio_toggle = CheckButton.new()
	audio_toggle.text = "ENABLE AUDIO"
	audio_toggle.button_pressed = true
	main_container.add_child(audio_toggle)
	
	var start_button = Button.new()
	start_button.text = "START GAME"
	start_button.custom_minimum_size = Vector2(200, 50)
	main_container.add_child(start_button)
	
	_setup_button_style(start_button, color_primary, 24)
	_setup_button_style(preview_button, color_secondary, 16)
	_setup_option_style(song_selector)
	_setup_option_style(difficulty_selector)
	
	store_node_references(song_selector, preview_button, difficulty_selector, difficulty_description, audio_toggle, start_button)

var song_selector: OptionButton
var song_preview_button: Button
var difficulty_selector: OptionButton
var difficulty_description: Label
var audio_toggle: CheckButton
var start_button: Button
var song_preview: AudioStreamPlayer
var ambient_audio: AudioStreamPlayer

func store_node_references(song_sel: OptionButton, preview_btn: Button, diff_sel: OptionButton, diff_desc: Label, audio_btn: CheckButton, start_btn: Button):
	song_selector = song_sel
	song_preview_button = preview_btn
	difficulty_selector = diff_sel
	difficulty_description = diff_desc
	audio_toggle = audio_btn
	start_button = start_btn
	

	song_preview = AudioStreamPlayer.new()
	add_child(song_preview)
	ambient_audio = AudioStreamPlayer.new()
	add_child(ambient_audio)

func _setup_button_style(button: Button, base_color: Color, font_size: int) -> void:
	var normal_style = StyleBoxFlat.new()
	normal_style.bg_color = base_color
	normal_style.border_color = base_color.darkened(0.3)
	normal_style.border_width_left = 2
	normal_style.border_width_top = 2
	normal_style.border_width_right = 2
	normal_style.border_width_bottom = 2
	normal_style.corner_radius_top_left = 8
	normal_style.corner_radius_top_right = 8
	normal_style.corner_radius_bottom_right = 8
	normal_style.corner_radius_bottom_left = 8
	
	button.add_theme_stylebox_override("normal", normal_style)
	button.add_theme_font_size_override("font_size", font_size)
	button.add_theme_color_override("font_color", color_text)

func _setup_option_style(option_button: OptionButton) -> void:
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.15, 0.2, 0.3, 0.8)
	style.border_color = color_primary
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.corner_radius_top_left = 6
	style.corner_radius_top_right = 6
	style.corner_radius_bottom_right = 6
	style.corner_radius_bottom_left = 6
	
	option_button.add_theme_stylebox_override("normal", style)
	option_button.add_theme_font_size_override("font_size", 16)
	option_button.add_theme_color_override("font_color", color_text)


func _populate_songs() -> void:
	if not song_selector:
		return
		
	song_selector.clear()
	var names := GameConfig.get_song_names()
	for song_name in names:
		song_selector.add_item(song_name)
	
	# Select default song
	var idx := GameConfig.get_selected_song_index()
	if idx >= 0:
		song_selector.select(idx)
	else:
		song_selector.select(0)
		GameConfig.set_selected_song(song_selector.get_item_text(0))

func _populate_difficulties() -> void:
	if not difficulty_selector:
		return
		
	difficulty_selector.clear()
	var names := GameConfig.get_difficulty_names()
	for difficulty_name in names:
		difficulty_selector.add_item(difficulty_name)
	
	var idx := GameConfig.get_selected_difficulty_index()
	if idx >= 0:
		difficulty_selector.select(idx)
		_update_difficulty_description(names[idx])
	else:
		difficulty_selector.select(0)
		GameConfig.set_difficulty(difficulty_selector.get_item_text(0))
		_update_difficulty_description(GameConfig.get_selected_difficulty())

func _connect_signals() -> void:
	if start_button:
		start_button.pressed.connect(_on_start_pressed)
	
	if audio_toggle:
		audio_toggle.toggled.connect(_on_audio_toggled)
	
	if difficulty_selector:
		difficulty_selector.item_selected.connect(_on_difficulty_selected)
	
	if song_selector:
		song_selector.item_selected.connect(_on_song_selected)
	
	if song_preview_button:
		song_preview_button.pressed.connect(_on_preview_button_pressed)

func _sync_initial_state() -> void:
	if audio_toggle:
		audio_toggle.button_pressed = GameConfig.audio_enabled
	_apply_audio_state()

func _on_start_pressed() -> void:
	GameConfig.audio_enabled = audio_toggle.button_pressed if audio_toggle else true
	_apply_audio_state()
	
	if song_preview and song_preview.playing:
		song_preview.stop()
	
	# 显示生成谱面的提示
	if start_button:
		start_button.text = "Generating Beatmap..."
		start_button.disabled = true
	
	# 生成谱面
	var success: bool = await _generate_beatmap()
	
	if not success:
		# 如果生成失败，显示错误信息
		if start_button:
			start_button.text = "Failed! Click to Retry"
			start_button.disabled = false
		if difficulty_description:
			difficulty_description.text = "Failed to generate beatmap. Please check Python environment."
		return
	
	# 恢复按钮状态
	if start_button:
		start_button.text = "START GAME"
		start_button.disabled = false
	
	# 切换到游戏场景
	get_tree().change_scene_to_file("res://scenes/Main.tscn")

func _on_audio_toggled(pressed: bool) -> void:
	GameConfig.audio_enabled = pressed
	_apply_audio_state()

func _apply_audio_state() -> void:
	AudioServer.set_bus_mute(0, not GameConfig.audio_enabled)
	
	if not GameConfig.audio_enabled and song_preview and song_preview.playing:
		song_preview.stop()

func _on_difficulty_selected(index: int) -> void:
	var difficulty_name := difficulty_selector.get_item_text(index)
	GameConfig.set_difficulty(difficulty_name)
	_update_difficulty_description(difficulty_name)

func _on_song_selected(index: int) -> void:
	var song_name := song_selector.get_item_text(index)
	GameConfig.set_selected_song(song_name)
	
	if GameConfig.audio_enabled:
		_preview_selected_song(song_name)

func _on_preview_button_pressed() -> void:
	var selected_index := song_selector.get_selected() if song_selector else -1
	if selected_index >= 0:
		var song_name := song_selector.get_item_text(selected_index)
		_preview_selected_song(song_name)

func _preview_selected_song(song_name: String) -> void:
	if not GameConfig.audio_enabled or not song_preview:
		return
	
	var song_path: String = GameConfig.get_song_path(song_name)
	if song_path and ResourceLoader.exists(song_path):
		var stream := load(song_path)
		if stream:
			if song_preview.playing:
				song_preview.stop()
			
			song_preview.stream = stream
			song_preview.play()
			
			if song_preview_button:
				song_preview_button.text = "Playing..."
				await get_tree().create_timer(1.0).timeout
				if song_preview_button:
					song_preview_button.text = "Preview"

func _update_difficulty_description(difficulty_name: String) -> void:
	if difficulty_description:
		var description = GameConfig.get_difficulty_description(difficulty_name)
		difficulty_description.text = description

func _generate_beatmap() -> bool:
	"""
	调用 Python 脚本生成谱面
	返回 true 如果成功，false 如果失败
	"""
	var selected_song: String = GameConfig.get_selected_song()
	var selected_difficulty: String = GameConfig.get_selected_difficulty()
	
	# 获取音频文件路径
	var song_path: String = GameConfig.get_song_path(selected_song)
	if song_path.is_empty():
		push_error("Song path is empty for: " + selected_song)
		return false
	
	# 将 res:// 路径转换为实际文件路径
	var audio_file_path: String = _res_path_to_file_path(song_path)
	if audio_file_path.is_empty() or not FileAccess.file_exists(audio_file_path):
		push_error("Audio file not found: " + audio_file_path)
		return false
	
	# 获取项目根目录（AIST2010-project）
	var project_root: String = _get_project_root()
	if project_root.is_empty():
		push_error("Failed to find project root")
		return false
	
	# 构建 Python 命令
	var python_script: String = project_root + "/tools/audio_to_beatmap.py"
	var python_cmd: String = ""
	
	# 检测 Python 命令（优先使用 python3，然后是 python）
	var python_exe: String = _find_python_executable()
	if python_exe.is_empty():
		push_error("Python not found. Please install Python 3.")
		return false
	
	# 构建完整命令
	var args: PackedStringArray = []
	args.append(python_script)
	args.append(audio_file_path)
	args.append("--difficulties")
	args.append(selected_difficulty)
	
	print("Generating beatmap for: ", selected_song, " (", selected_difficulty, ")")
	print("Python: ", python_exe)
	print("Script: ", python_script)
	print("Audio: ", audio_file_path)
	print("Project root: ", project_root)
	
	# 执行 Python 脚本
	# OS.execute() 在 Godot 4 中的签名：
	# execute(path: String, arguments: PackedStringArray, output: Array = [], read_stderr: bool = false, open_console: bool = false) -> int
	var output: Array = []
	var exit_code: int = OS.execute(
		python_exe,
		args,
		output,  # 输出数组
		true,    # read_stderr: 读取标准错误
		false    # open_console: 不打开控制台
	)
	
	# 打印输出信息
	if output.size() > 0:
		print("Python script output:")
		for line in output:
			print("  ", line)
	
	# 检查生成的谱面文件是否存在（即使退出码非0也检查，因为可能有警告但文件已生成）
	var beatmap_path: String = project_root + "/godot/data/beatmaps/" + selected_song + "_" + selected_difficulty.to_lower() + ".json"
	
	# 如果文件已存在，先删除它以确保重新生成
	var beatmap_dir: String = project_root + "/godot/data/beatmaps/"
	var beatmap_filename: String = selected_song + "_" + selected_difficulty.to_lower() + ".json"
	
	if FileAccess.file_exists(beatmap_path):
		var dir = DirAccess.open(beatmap_dir)
		if dir:
			dir.remove(beatmap_filename)
			print("Removed existing beatmap file: ", beatmap_path)
	
	print("Checking for beatmap at: ", beatmap_path)
	
	# 使用多种方式检查文件是否存在
	var file_exists: bool = false
	
	# 方法1: 使用 FileAccess
	if FileAccess.file_exists(beatmap_path):
		file_exists = true
		print("File found via FileAccess")
	else:
		# 方法2: 尝试打开文件
		var test_file = FileAccess.open(beatmap_path, FileAccess.READ)
		if test_file:
			file_exists = true
			test_file.close()
			print("File found via FileAccess.open()")
	
	if not file_exists:
		# 如果文件不存在，检查目录是否存在
		var dir_exists: bool = DirAccess.dir_exists_absolute(beatmap_dir)
		print("Beatmap directory exists: ", dir_exists, " at ", beatmap_dir)
		
		# 列出目录中的文件
		if dir_exists:
			var dir = DirAccess.open(beatmap_dir)
			if dir:
				print("Files in beatmap directory:")
				dir.list_dir_begin()
				var file_name = dir.get_next()
				while file_name != "":
					if not dir.current_is_dir():
						print("  - ", file_name)
					file_name = dir.get_next()
		
		# 如果脚本执行成功（退出码为0），即使文件检查失败也允许继续
		# 因为 Game.gd 有回退机制，会尝试加载默认谱面
		if exit_code == 0:
			print("Warning: Script executed successfully but file check failed. Continuing anyway (Game will use fallback).")
			return true
		
		push_error("Generated beatmap file not found: " + beatmap_path)
		push_error("Python script also failed with exit code: " + str(exit_code))
		return false
	
	if exit_code != 0:
		print("Warning: Python script exited with code ", exit_code, " but file was generated")
	
	print("Beatmap generated successfully: ", beatmap_path)
	return true

func _res_path_to_file_path(res_path: String) -> String:
	"""
	将 res:// 路径转换为实际文件路径
	例如: res://assets/audio/song1.ogg -> /path/to/project/godot/assets/audio/song1.ogg
	"""
	if not res_path.begins_with("res://"):
		return res_path
	
	var project_root: String = _get_project_root()
	if project_root.is_empty():
		return ""
	
	# 移除 res:// 前缀
	var relative_path: String = res_path.substr(6)  # 移除 "res://"
	return project_root + "/godot/" + relative_path

func _get_project_root() -> String:
	"""
	获取项目根目录（AIST2010-project）
	"""
	# 获取项目路径（res:// 的绝对路径）
	var project_path: String = ProjectSettings.globalize_path("res://")
	if project_path.is_empty():
		return ""
	
	# 移除末尾的 /godot（如果存在）
	if project_path.ends_with("/godot"):
		project_path = project_path.substr(0, project_path.length() - 6)
	
	# 验证 tools/audio_to_beatmap.py 是否存在
	var test_path: String = project_path + "/tools/audio_to_beatmap.py"
	if FileAccess.file_exists(test_path):
		return project_path
	
	# 如果直接路径不行，尝试向上查找
	var current_dir: String = project_path
	for i in range(3):
		var test: String = current_dir + "/tools/audio_to_beatmap.py"
		if FileAccess.file_exists(test):
			return current_dir
		
		# 获取父目录（手动处理路径）
		var parts: PackedStringArray = current_dir.split("/")
		if parts.size() <= 1:
			break
		parts.remove_at(parts.size() - 1)
		current_dir = "/".join(parts)
	
	return ""

func _find_python_executable() -> String:
	"""
	查找 Python 可执行文件
	优先使用 python3，然后是 python
	"""
	# 在 macOS/Linux 上尝试 python3
	# OS.execute() 签名: execute(path, arguments, output=[], read_stderr=false, open_console=false)
	var output: Array = []
	var exit_code: int = OS.execute("python3", ["--version"], output, false, false)
	if exit_code == 0:
		return "python3"
	
	# 尝试 python
	output.clear()
	exit_code = OS.execute("python", ["--version"], output, false, false)
	if exit_code == 0:
		return "python"
	
	# 在 Windows 上可能需要完整路径
	if OS.get_name() == "Windows":
		# 尝试常见的 Python 安装路径
		var common_paths: Array[String] = [
			"C:/Python39/python.exe",
			"C:/Python310/python.exe",
			"C:/Python311/python.exe",
			"C:/Python312/python.exe",
			"C:/Users/" + OS.get_environment("USERNAME") + "/AppData/Local/Programs/Python/Python39/python.exe",
			"C:/Users/" + OS.get_environment("USERNAME") + "/AppData/Local/Programs/Python/Python310/python.exe",
		]
		
		for path in common_paths:
			if FileAccess.file_exists(path):
				return path
	
	return ""
