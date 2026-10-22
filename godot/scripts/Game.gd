extends Node2D

const NOTE_SCENE: PackedScene = preload("res://scenes/Note.tscn")

@onready var audio: AudioStreamPlayer = $Audio
@onready var player: CharacterBody2D = $Player
@onready var hit_line: Node2D = $HitLine
@onready var ui_score: Label = $UI/Labels/Score
@onready var ui_combo: Label = $UI/Labels/Combo
@onready var ui_feedback: Label = $UI/Labels/Feedback
@onready var ui_song_title: Label = $UI/Labels/SongTitle
@onready var ui_difficulty: Label = $UI/Labels/Difficulty

# 分界线Y坐标（屏幕中间）
var divider_y: float = 360.0

# 跑道偏移
const LANE_OFFSET: float = 60.0

var beatmap: Dictionary = {}
var spawn_index: int = 0
var active_notes: Array = []

var score: int = 0
var combo: int = 0

# 长按音符相关
var current_hold_note: Note = null  # 当前正在长按的音符
var hold_start_time: float = 0.0  # 开始长按的时间
var is_holding: bool = false  # 是否正在长按

# 难度配置
var difficulty_settings: Dictionary = {
	"Easy": {
		"speed_multiplier": 0.6,
		"perfect_dodge_distance": 16.0,
		"great_dodge_distance": 32.0,
		"miss_dodge_distance": 48.0,
		"perfect_hit_distance": 24.0,
		"great_hit_distance": 48.0,
		"miss_hit_distance": 72.0,
		"prespawn_time": 2.5,
		"score_multiplier": 0.8
	},
	"Normal": {
		"speed_multiplier": 0.75,
		"perfect_dodge_distance": 12.0,
		"great_dodge_distance": 24.0,
		"miss_dodge_distance": 36.0,
		"perfect_hit_distance": 20.0,
		"great_hit_distance": 40.0,
		"miss_hit_distance": 60.0,
		"prespawn_time": 2.0,
		"score_multiplier": 1.0
	},
	"Hard": {
		"speed_multiplier": 0.9,
		"perfect_dodge_distance": 8.0,
		"great_dodge_distance": 16.0,
		"miss_dodge_distance": 24.0,
		"perfect_hit_distance": 16.0,
		"great_hit_distance": 32.0,
		"miss_hit_distance": 48.0,
		"prespawn_time": 1.5,
		"score_multiplier": 1.2
	}
}

# 当前难度设置
var current_difficulty: String = "Normal"
var speed_multiplier: float = 0.75
var perfect_dodge_distance: float = 12.0
var great_dodge_distance: float = 24.0
var miss_dodge_distance: float = 36.0
var perfect_hit_distance: float = 20.0
var great_hit_distance: float = 40.0
var miss_hit_distance: float = 60.0
var prespawn_time: float = 2.0
var score_multiplier: float = 1.0

# 敌人攻击窗口提前量
const ENEMY_ATTACK_WINDOW := 0.2

func _ready() -> void:
	# 设置分界线位置
	divider_y = 360.0
	
	# 等待一帧确保viewport准备好
	await get_tree().process_frame
	
	# 如果viewport可用，使用实际屏幕高度
	if get_viewport():
		var viewport_size: Vector2 = get_viewport().size
		if viewport_size.y > 0:
			divider_y = viewport_size.y / 2.0
	
	# 加载玩家选择的歌曲和难度
	_load_player_settings()
	_load_beatmap()
	_prepare_audio()
	
	# 初始化玩家和判定线
	if player:
		player.divider_y = divider_y
		player.global_position.x = 150.0
		player.global_position.y = divider_y + LANE_OFFSET  # 初始在下方跑道
		
		# 判定线在玩家当前位置
		hit_line.global_position.x = 150.0
		hit_line.global_position.y = divider_y
		
		print("Game initialized - Song: ", GameConfig.get_selected_song())
		print("Difficulty: ", current_difficulty)
		print("Divider Y: ", divider_y)
		print("Upper lane: ", divider_y - LANE_OFFSET)
		print("Lower lane: ", divider_y + LANE_OFFSET)
	
	# 绘制分界线
	_draw_divider()
	
	# 添加背景色以便看清
	_draw_background()
	
	# 更新UI显示歌曲和难度信息
	_update_song_info()
	
	AudioServer.set_bus_mute(0, not GameConfig.audio_enabled)
	if audio.stream and GameConfig.audio_enabled:
		audio.play()
		print("Audio started playing - Song: ", GameConfig.get_selected_song())
	else:
		if not audio.stream:
			push_warning("No audio stream loaded for song: ", GameConfig.get_selected_song())

func _load_player_settings() -> void:
	# 获取玩家选择的难度并应用设置
	current_difficulty = GameConfig.get_selected_difficulty()
	var settings = difficulty_settings.get(current_difficulty, difficulty_settings["Normal"])
	
	speed_multiplier = settings["speed_multiplier"]
	perfect_dodge_distance = settings["perfect_dodge_distance"]
	great_dodge_distance = settings["great_dodge_distance"]
	miss_dodge_distance = settings["miss_dodge_distance"]
	perfect_hit_distance = settings["perfect_hit_distance"]
	great_hit_distance = settings["great_hit_distance"]
	miss_hit_distance = settings["miss_hit_distance"]
	prespawn_time = settings["prespawn_time"]
	score_multiplier = settings["score_multiplier"]
	
	print("Applied difficulty settings: ", current_difficulty)
	print("Speed multiplier: ", speed_multiplier)
	print("Score multiplier: ", score_multiplier)

func _update_song_info() -> void:
	if ui_song_title:
		ui_song_title.text = "Song: %s" % GameConfig.get_selected_song()
	if ui_difficulty:
		ui_difficulty.text = "Difficulty: %s" % current_difficulty

func _draw_background() -> void:
	# 添加上下跑道背景色区分
	var background := Control.new()
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	background.z_index = -10
	add_child(background)
	
	var upper_bg := ColorRect.new()
	upper_bg.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	upper_bg.anchor_bottom = 0.5
	upper_bg.color = Color(0.1, 0.1, 0.15, 1.0)
	upper_bg.z_index = -10
	background.add_child(upper_bg)
	
	var lower_bg := ColorRect.new()
	lower_bg.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	lower_bg.anchor_top = 0.5
	lower_bg.color = Color(0.15, 0.1, 0.1, 1.0)
	lower_bg.z_index = -10
	background.add_child(lower_bg)

func _draw_divider() -> void:
	# 使用Line2D绘制分界线
	var divider := Line2D.new()
	divider.width = 4.0
	divider.default_color = Color(1.0, 1.0, 1.0, 1.0)
	divider.z_index = 5
	divider.points = PackedVector2Array([
		Vector2(0, divider_y),
		Vector2(1280, divider_y)
	])
	add_child(divider)
	
	# 添加一个更明显的分界线指示器
	var divider_marker := Line2D.new()
	divider_marker.width = 2.0
	divider_marker.default_color = Color(1.0, 0.3, 0.3, 0.8)
	divider_marker.z_index = 4
	divider_marker.points = PackedVector2Array([
		Vector2(0, divider_y - 1),
		Vector2(1280, divider_y - 1)
	])
	add_child(divider_marker)
	
	print("Divider drawn at Y: ", divider_y)

func _process(delta: float) -> void:
	if audio.playing:
		_spawn_due_notes()
		_check_obstacle_collision()
		_check_enemy_collision()
		_check_hold_note()
		_cleanup_passed_notes()
		_cleanup_off_screen_notes()
		# 更新判定线位置跟随玩家
		if player:
			hit_line.global_position.y = player.global_position.y

func _input(event: InputEvent) -> void:
	if event is InputEventKey:
		var keycode: int = event.keycode
		
		# J键释放：检查是否提前结束长按
		if keycode == KEY_J and not event.pressed:
			if is_holding and current_hold_note:
				# 检查是否提前释放
				var current_time: float = _music_time()
				var elapsed: float = current_time - hold_start_time
				var note_right := _get_note_right(current_hold_note)
				var hit_line_x: float = hit_line.global_position.x
				
				# 如果长按音符还未完全通过判定线，判定为提前结束
				if note_right >= hit_line_x or elapsed < current_hold_note.hold_duration * 0.9:
					_end_hold_early()
			return
		
		if event.pressed and not event.echo:
			# K键：切换跑道（处理障碍物）
			if keycode == KEY_K:
				var switch_success: bool = player.switch_lane()
				if switch_success:
					var current_lane: String = player.get_current_lane()
					# 查找刚才所在跑道的障碍物
					var previous_lane: String = "lower" if current_lane == "upper" else "upper"
					var best_note := _find_best_obstacle_by_lane_space(previous_lane)
					if best_note:
						# 基于空间距离判定闪避
						var left_edge := _get_note_left(best_note)
						var hit_line_x: float = hit_line.global_position.x
						var distance := absf(left_edge - hit_line_x)
						
						if distance <= perfect_dodge_distance:
							_on_perfect_dodge(best_note, "Perfect Dodge", int(1000 * score_multiplier))
						elif distance <= great_dodge_distance:
							_on_perfect_dodge(best_note, "Great Dodge", int(500 * score_multiplier))
						elif distance <= miss_dodge_distance:
							_on_perfect_dodge(best_note, "Dodge", int(200 * score_multiplier))
					# 更新判定线位置到玩家当前位置
					hit_line.global_position.y = player.global_position.y
			
			# J键：攻击（处理敌人）或开始长按（处理长按音符）
			elif keycode == KEY_J:
				# 首先检查是否有长按音符需要处理
				var hold_note := _find_hold_note_at_hitline()
				if hold_note:
					# 开始长按
					_start_hold(hold_note)
				else:
					# 普通攻击处理敌人
					var attack_success: bool = player.attack()
					if attack_success:
						# 使用基于距离的检测方法（不依赖碰撞体）
						var best_enemy: Note = null
						var best_distance: float = 9999.0
						var hit_line_x: float = hit_line.global_position.x
						var player_lane: String = player.get_current_lane()
						
						# 遍历所有活跃音符，找到在玩家跑道上且距离判定线最近的敌人
						for note in active_notes:
							if note is Note and note.note_type == "enemy" and note.lane == player_lane:
								var left_edge := _get_note_left(note)
								# 只考虑在判定线附近（攻击范围内）的敌人
								var distance := absf(left_edge - hit_line_x)
								if distance <= miss_hit_distance and distance < best_distance:
									best_distance = distance
									best_enemy = note
						
						if best_enemy:
							if best_distance <= perfect_hit_distance:
								_on_hit(best_enemy, "Perfect", int(1000 * score_multiplier), true)
							elif best_distance <= great_hit_distance:
								_on_hit(best_enemy, "Great", int(500 * score_multiplier), true)
							elif best_distance <= miss_hit_distance:
								_on_hit(best_enemy, "Miss", 0, false)
							else:
								_on_miss()
						else:
							_on_miss()

func _on_hit(note: Node, label: String, add_score: int, keep_combo: bool) -> void:
	score += add_score
	if keep_combo:
		combo += 1
	else:
		combo = 0
	_set_feedback(label)
	_update_ui()
	active_notes.erase(note)
	note.queue_free()

func _on_perfect_dodge(note: Node, label: String, add_score: int) -> void:
	# Perfect Dodge：成功躲避障碍物
	score += add_score
	combo += 1
	_set_feedback(label)
	_update_ui()
	active_notes.erase(note)
	note.queue_free()

func _on_collision(obstacle: Node) -> void:
	# 撞上障碍物：扣分
	var penalty = int(500 * score_multiplier)
	score = max(0, score - penalty)
	combo = 0
	_set_feedback("Collision! -%d" % penalty)
	_update_ui()
	active_notes.erase(obstacle)
	obstacle.queue_free()

func _on_miss() -> void:
	combo = 0
	_set_feedback("Miss")
	_update_ui()

func _set_feedback(text: String) -> void:
	ui_feedback.text = text

func _update_ui() -> void:
	ui_score.text = "Score: %d" % score
	ui_combo.text = "Combo: %d" % combo

func _load_beatmap() -> void:
	# 根据选择的歌曲加载对应的谱面
	var selected_song = GameConfig.get_selected_song()
	var beatmap_path = _get_beatmap_path_for_song(selected_song)
	
	print("Loading beatmap for song: ", selected_song)
	print("Beatmap path: ", beatmap_path)
	
	var file := FileAccess.open(beatmap_path, FileAccess.READ)
	if file:
		var content := file.get_as_text()
		beatmap = JSON.parse_string(content)
		spawn_index = 0
		print("Successfully loaded beatmap for: ", selected_song)
	else:
		push_error("Failed to load beatmap: %s" % beatmap_path)
		# 如果谱面加载失败，使用默认谱面
		_load_default_beatmap()

func _get_beatmap_path_for_song(song_name: String) -> String:
	# 根据歌曲和难度生成谱面路径
	# 格式: res://data/beatmaps/{song_name}_{difficulty}.json
	var difficulty_lower = current_difficulty.to_lower()
	var beatmap_path = "res://data/beatmaps/%s_%s.json" % [song_name, difficulty_lower]
	
	# 检查文件是否存在
	if ResourceLoader.exists(beatmap_path):
		return beatmap_path
	
	# 如果不存在，尝试加载默认的（不带难度后缀的）文件作为回退
	var fallback_path = "res://data/beatmaps/%s.json" % song_name
	if ResourceLoader.exists(fallback_path):
		print("Warning: Difficulty-specific beatmap not found, using default: ", fallback_path)
		return fallback_path
	
	# 最后的回退：使用 example.json
	return "res://data/beatmaps/example.json"

func _load_default_beatmap() -> void:
	# 加载默认谱面作为备用
	var default_path = "res://data/beatmaps/example.json"
	var file := FileAccess.open(default_path, FileAccess.READ)
	if file:
		var content := file.get_as_text()
		beatmap = JSON.parse_string(content)
		spawn_index = 0
		print("Loaded default beatmap: ", default_path)
	else:
		push_error("Failed to load default beatmap: %s" % default_path)
		# 如果连默认谱面都没有，创建一个空的谱面结构
		beatmap = {
			"audio": "",
			"notes": []
		}
		print("Created empty beatmap structure")

func _prepare_audio() -> void:
	# 使用从 GameConfig 获取的歌曲路径
	var song_path: String = GameConfig.get_selected_song_path()
	print("Loading song: ", GameConfig.get_selected_song())
	print("Song path: ", song_path)
	
	if song_path and ResourceLoader.exists(song_path):
		var stream := ResourceLoader.load(song_path)
		if stream:
			audio.stream = stream
			print("Successfully loaded audio stream")
		else:
			push_error("Failed to load audio stream: %s" % song_path)
	else:
		push_error("Song file not found: %s" % song_path)

func _music_time() -> float:
	return audio.get_playback_position()

func _spawn_due_notes() -> void:
	if not beatmap.has("notes"):
		return
	var notes: Array = beatmap["notes"]
	var t := _music_time()
	
	# 记录已处理的hit_time，确保同一时间的两条跑道上不会同时出现障碍物
	var processed_obstacle_times: Dictionary = {}
	
	while spawn_index < notes.size():
		var n: Dictionary = notes[spawn_index]
		var hit_time: float = n.get("time", 0.0)
		var note_type: String = n.get("type", "obstacle")
		
		# 检查障碍物：同一时间不能出现在两条跑道上
		if note_type == "obstacle":
			if processed_obstacle_times.has(hit_time):
				# 如果这个时间已经有障碍物了，跳过这条障碍物
				spawn_index += 1
				continue
			processed_obstacle_times[hit_time] = true
		
		if hit_time - t <= prespawn_time:
			_spawn_note(n)
			spawn_index += 1
		else:
			break

func _spawn_note(n: Dictionary) -> void:
	var note := NOTE_SCENE.instantiate()
	var note_type: String = n.get("type", "obstacle")
	var hit_time: float = n.get("time", 0.0)
	var lane: String = n.get("lane", "lower")  # "upper" 或 "lower"
	var hold_duration: float = n.get("duration", 0.0)  # 长按音符的时长
	
	note.note_type = note_type
	note.hit_time = hit_time
	note.lane = lane
	note.divider_y = divider_y
	note.hold_duration = hold_duration  # 设置长按时长
	
	# 横版：从右侧生成，向左移动到玩家位置（判定线）
	var spawn_x: float = 1280.0 + 100.0  # 屏幕右侧外
	var spawn_y: float = divider_y - LANE_OFFSET if lane == "upper" else divider_y + LANE_OFFSET
	note.global_position = Vector2(spawn_x, spawn_y)
	add_child(note)
	
	var target_x: float = hit_line.global_position.x
	var distance: float = absf(target_x - note.global_position.x)
	var current_time: float = _music_time()
	
	# 对于敌人：计算让它在hit_time - ENEMY_ATTACK_WINDOW时到达判定线
	# 对于长按音符：计算让它在 hit_time 时到达判定线
	var arrival_time: float = hit_time
	if note_type == "enemy":
		arrival_time = hit_time - ENEMY_ATTACK_WINDOW
	elif note_type == "hold":
		arrival_time = hit_time  # 长按音符在 hit_time 时开始
	
	var dt: float = maxf(arrival_time - current_time, 0.01)
	note.speed = distance / dt * speed_multiplier  # 应用难度速度倍数
	note.target_position = Vector2(target_x, spawn_y)
	active_notes.append(note)
	
	# 对于长按音符，在设置 speed 后更新外观以正确显示长度
	if note_type == "hold":
		note._update_appearance()
	
	print("Spawned note: type=", note_type, " lane=", lane, " hit_time=", hit_time, " speed=", note.speed, " hold_duration=", hold_duration)

func _check_obstacle_collision() -> void:
	# 检查障碍物是否撞上玩家（完全基于空间）
	if not player:
		return
	
	var player_lane: String = player.get_current_lane()
	var hit_line_x: float = hit_line.global_position.x
	
	for i in range(active_notes.size() - 1, -1, -1):
		var obstacle = active_notes[i]
		if obstacle is Note and obstacle.note_type == "obstacle":
			# 检查障碍物是否在玩家跑道上
			if obstacle.lane == player_lane:
				# 检查障碍物是否已经到达或超过判定线
				var obstacle_left: float = _get_note_left(obstacle)
				# 如果障碍物的左边缘已经越过判定线，判定为碰撞
				if obstacle_left < hit_line_x:
					_on_collision(obstacle)

func _cleanup_off_screen_notes() -> void:
	# 清理已经越过玩家位置的音符（基于左边缘）
	if not player:
		return
	var player_x: float = player.global_position.x
	for i in range(active_notes.size() - 1, -1, -1):
		var note = active_notes[i]
		if note is Note:
			var left_edge := _get_note_left(note)
			if left_edge < player_x:
				active_notes.remove_at(i)
				note.queue_free()

func _cleanup_passed_notes() -> void:
	# 保留此函数以防未来需要时间基础的清理逻辑
	pass

func _check_enemy_collision() -> void:
	# 敌人到达玩家判定线且未被击杀，则按撞击处理（扣分）
	if not player:
		return
	var player_lane: String = player.get_current_lane()
	var hit_line_x: float = hit_line.global_position.x
	for i in range(active_notes.size() - 1, -1, -1):
		var e = active_notes[i]
		if e is Note and e.note_type == "enemy":
			if e.lane == player_lane:
				var left_edge := _get_note_left(e)
				if left_edge <= hit_line_x:
					# 若尚未在攻击判定中被移除，则视为被撞击
					_on_enemy_collision(e)

func _on_enemy_collision(e: Node) -> void:
	var penalty = int(700 * score_multiplier)
	score = max(0, score - penalty)
	combo = 0
	_set_feedback("Enemy Hit! -%d" % penalty)
	_update_ui()
	active_notes.erase(e)
	e.queue_free()

func _get_note_left(n: Node) -> float:
	# 计算音符左边缘的全局x坐标
	var half_width := 16.0
	if n.has_node("Sprite2D"):
		var s: Sprite2D = n.get_node("Sprite2D")
		if s and s.texture:
			var sz: Vector2 = s.texture.get_size() * s.scale
			half_width = sz.x * 0.5
	elif n.has_node("HoldRect"):
		# 长按音符使用 HoldRect
		var rect: ColorRect = n.get_node("HoldRect")
		half_width = rect.size.x * 0.5
	return n.global_position.x - half_width

func _get_note_right(n: Node) -> float:
	# 计算音符右边缘的全局x坐标
	var half_width := 16.0
	if n.has_node("Sprite2D"):
		var s: Sprite2D = n.get_node("Sprite2D")
		if s and s.texture:
			var sz: Vector2 = s.texture.get_size() * s.scale
			half_width = sz.x * 0.5
	elif n.has_node("HoldRect"):
		# 长按音符使用 HoldRect
		var rect: ColorRect = n.get_node("HoldRect")
		half_width = rect.size.x * 0.5
	return n.global_position.x + half_width

func _find_hold_note_at_hitline() -> Note:
	# 查找在判定线上的长按音符
	if not player:
		return null
	
	var player_lane: String = player.get_current_lane()
	var hit_line_x: float = hit_line.global_position.x
	
	for note in active_notes:
		if note is Note and note.note_type == "hold" and note.lane == player_lane:
			var left_edge := _get_note_left(note)
			var right_edge := _get_note_right(note)
			
			# 检查判定线是否在长按音符范围内
			if left_edge <= hit_line_x and hit_line_x <= right_edge:
				return note
	
	return null

func _start_hold(note: Note) -> void:
	# 开始长按
	if current_hold_note != null:
		# 如果已经有长按音符，先结束它（失败）
		_end_hold_early()
	
	current_hold_note = note
	hold_start_time = _music_time()
	is_holding = true
	player.is_attacking = true  # 设置玩家为攻击状态
	print("Started holding note at time: ", hold_start_time)

func _check_hold_note() -> void:
	# 检查长按状态
	if not is_holding or current_hold_note == null:
		return
	
	# 检查 J 键是否仍然按下
	if not Input.is_key_pressed(KEY_J):
		# J 键已释放，检查是否提前结束
		_end_hold_early()
		return
	
	var current_time: float = _music_time()
	var elapsed: float = current_time - hold_start_time
	var hit_line_x: float = hit_line.global_position.x
	var note_left := _get_note_left(current_hold_note)
	var note_right := _get_note_right(current_hold_note)
	
	# 检查长按音符是否已经完全通过判定线
	if note_right < hit_line_x:
		# 长按音符已完全通过，检查是否完成
		if elapsed >= current_hold_note.hold_duration * 0.9:  # 允许 90% 的容错
			# 成功完成长按
			_on_hold_complete()
		else:
			# 提前结束，失败
			_end_hold_early()
	elif note_left > hit_line_x + 50.0:
		# 长按音符还未到达判定线，提前释放，失败
		_end_hold_early()

func _end_hold_early() -> void:
	# 提前结束长按（失败）
	if current_hold_note:
		_on_miss()
		_set_feedback("Hold Failed!")
		active_notes.erase(current_hold_note)
		current_hold_note.queue_free()
	
	current_hold_note = null
	is_holding = false
	player.is_attacking = false
	print("Hold ended early")

func _on_hold_complete() -> void:
	# 成功完成长按
	if current_hold_note:
		var score_add: int = int(1000 * score_multiplier * (1.0 + combo * 0.1))
		score += score_add
		combo += 1
		_set_feedback("Hold Complete! +%d" % score_add)
		_update_ui()
		active_notes.erase(current_hold_note)
		current_hold_note.queue_free()
	
	current_hold_note = null
	is_holding = false
	player.is_attacking = false
	print("Hold completed successfully")

func _find_best_obstacle_by_lane_space(lane: String) -> Note:
	# 基于空间距离找到最近的障碍物
	var best: Note = null
	var best_distance: float = 9999.0
	var hit_line_x: float = hit_line.global_position.x
	
	for n in active_notes:
		if n is Note and n.note_type == "obstacle" and n.lane == lane:
			var left_edge := _get_note_left(n)
			# 只考虑在判定线右侧或接近判定线的障碍物（还未完全越过）
			if left_edge >= hit_line_x - miss_dodge_distance:
				var distance := absf(left_edge - hit_line_x)
				if distance < best_distance:
					best_distance = distance
					best = n
	return best
