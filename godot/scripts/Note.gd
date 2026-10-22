extends Node2D
class_name Note

# 音符类型：
# - obstacle: 障碍物（需要切换跑道躲避）
# - enemy: 敌人（需要攻击）
# - hold: 长按音符（需要长按J键）
var note_type: String = "obstacle"

# 跑道位置（"upper" 或 "lower"）
var lane: String = "lower"

var hit_time: float = 0.0
var speed: float = 0.0
var target_position: Vector2 = Vector2.ZERO

# 长按音符的时长（仅对 hold 类型有效）
var hold_duration: float = 0.0

# 分界线Y坐标
var divider_y: float = 360.0

# 跑道偏移
const LANE_OFFSET: float = 60.0

func _ready() -> void:
	_update_appearance()
	_update_position()

func _process(delta: float) -> void:
	if target_position:
		var dir := (target_position - global_position).normalized()
		global_position += dir * speed * delta
		# 保持在同一跑道
		_update_position()

func _update_position() -> void:
	var target_y: float = 0.0
	if lane == "upper":
		target_y = divider_y - LANE_OFFSET
	else:
		target_y = divider_y + LANE_OFFSET
	global_position.y = target_y

func _update_appearance() -> void:
	var sprite: Sprite2D = $Sprite2D
	if sprite:
		if note_type == "hold":
			# 长按音符：使用长条形状（ColorRect）
			# 移除 Sprite2D，使用 ColorRect 代替
			if sprite.get_parent():
				sprite.queue_free()
			
			# 检查是否已经创建了 HoldRect
			var existing_rect = get_node_or_null("HoldRect")
			if existing_rect:
				existing_rect.queue_free()
			
			var rect := ColorRect.new()
			rect.name = "HoldRect"
			add_child(rect)
			
			# 根据时长计算长度
			# 使用一个合理的最小长度（至少 200 像素），或者基于速度计算
			var min_length: float = 200.0
			var calculated_length: float = 0.0
			
			if speed > 0 and hold_duration > 0:
				# 长度 = 时长 * 速度（像素/秒）
				calculated_length = hold_duration * speed
			else:
				# 如果速度还没设置，使用一个基于时长的估算值
				# 假设平均速度约为 400 像素/秒
				calculated_length = hold_duration * 400.0
			
			# 确保长度至少为最小值
			var length: float = max(calculated_length, min_length)
			
			rect.size = Vector2(length, 50.0)  # 宽度根据时长，高度固定为 50
			rect.color = Color(0.2, 0.8, 1.0, 0.8)  # 青色半透明
			rect.position = Vector2(-length * 0.5, -25.0)  # 居中
			
			# 添加边框
			var existing_border = get_node_or_null("HoldBorder")
			if existing_border:
				existing_border.queue_free()
			
			var border := ColorRect.new()
			border.name = "HoldBorder"
			border.size = rect.size + Vector2(4, 4)
			border.position = rect.position - Vector2(2, 2)
			border.color = Color(0.0, 0.6, 1.0, 1.0)  # 深青色边框
			border.z_index = -1
			add_child(border)
		else:
			var texture_path: String = ""
			if note_type == "obstacle":
				# 障碍物：使用专门的障碍物贴图
				texture_path = "res://assets/obstacles/obstacle.png"
			elif note_type == "enemy":
				# 敌人：使用敌人贴图
				texture_path = "res://assets/enemies/p3r.png"
			
			var texture := load(texture_path) as Texture2D
			if texture:
				sprite.texture = texture
				# 根据类型设置缩放和颜色
				if note_type == "obstacle":
					sprite.scale = Vector2(0.5, 0.5)  # 障碍物缩小到50%
					sprite.modulate = Color(1.0, 0.6, 0.2)  # 橙色
				elif note_type == "enemy":
					sprite.modulate = Color(0.8, 0.2, 0.8)  # 紫色
			else:
				push_warning("Failed to load note texture: " + texture_path)
				# 如果贴图加载失败，使用颜色区分
				if note_type == "obstacle":
					sprite.modulate = Color(1.0, 0.6, 0.2)
				elif note_type == "enemy":
					sprite.modulate = Color(0.8, 0.2, 0.8)

