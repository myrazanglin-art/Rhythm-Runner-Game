extends CharacterBody2D
class_name Player

# 分界线Y坐标（屏幕中间）
var divider_y: float = 360.0

# 跑道偏移（距离分界线的距离）
const LANE_OFFSET: float = 60.0

# 上方跑道Y坐标
var upper_lane_y: float = 0.0
# 下方跑道Y坐标
var lower_lane_y: float = 0.0

# 当前跑道（true=上方，false=下方）
var is_upper_lane: bool = false

# 切换动画速度
const SWITCH_SPEED: float = 2000.0  # 从800增加到2000，切换更快

# 玩家状态
var is_attacking: bool = false
var is_switching: bool = false

# 攻击判定区域（攻击时检查是否有敌人）
var attack_range: float = 80.0

@onready var sprite: Sprite2D = $Sprite2D
@onready var attack_area: Area2D = $AttackArea
@onready var attack_collision: CollisionShape2D = $AttackArea/CollisionShape2D
@onready var anim: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
	# 设置分界线位置（屏幕中间）
	divider_y = get_viewport().size.y / 2.0 if get_viewport() else 360.0
	upper_lane_y = divider_y - LANE_OFFSET
	lower_lane_y = divider_y + LANE_OFFSET
	
	# 初始位置：下方跑道
	is_upper_lane = false
	global_position.y = lower_lane_y
	
	# 设置攻击判定区域
	if attack_collision:
		var shape := RectangleShape2D.new()
		shape.size = Vector2(attack_range, 60.0)
		attack_collision.shape = shape
		attack_collision.position = Vector2(attack_range * 0.5, 0.0)
	
	# 加载玩家贴图
	if sprite:
		var texture_path := "res://assets/player/p3r.png"
		# 尝试多种方式加载贴图
		var texture: Texture2D = null
		
		# 方法1: 直接load
		texture = load(texture_path) as Texture2D
		
		# 方法2: 如果失败，尝试ResourceLoader
		if not texture:
			texture = ResourceLoader.load(texture_path, "Texture2D") as Texture2D
		
		# 方法3: 如果还是失败，尝试加载资源
		if not texture:
			var resource = ResourceLoader.load(texture_path)
			if resource is Texture2D:
				texture = resource as Texture2D
		
		if texture:
			sprite.texture = texture
			sprite.modulate = Color.WHITE
			sprite.z_index = 10  # 确保玩家在最上层
			sprite.scale = Vector2(0.15, 0.15)  # 缩小到30%大小
			print("Player texture loaded successfully: ", texture_path)
			print("Texture size: ", texture.get_size())
			print("Scaled size: ", texture.get_size() * sprite.scale)
		else:
			push_error("Failed to load player texture: " + texture_path)
			# 创建备用显示
			var rect := ColorRect.new()
			rect.size = Vector2(32, 48)
			rect.color = Color(0.2, 0.8, 0.2, 1)
			rect.z_index = 10
			add_child(rect)
			sprite.modulate = Color(0.2, 0.8, 0.2, 1)
			print("Using fallback green rectangle for player")

func _physics_process(delta: float) -> void:
	# 玩家固定在屏幕左侧
	velocity.x = 0.0
	
	# 平滑移动到目标跑道
	var target_y: float = upper_lane_y if is_upper_lane else lower_lane_y
	var current_y: float = global_position.y
	
	if abs(current_y - target_y) > 1.0:
		is_switching = true
		var direction: float = 1.0 if target_y > current_y else -1.0
		var move_distance: float = SWITCH_SPEED * delta
		if abs(current_y - target_y) < move_distance:
			global_position.y = target_y
			is_switching = false
		else:
			global_position.y += direction * move_distance
	else:
		is_switching = false
		global_position.y = target_y
	
	# 强制固定X位置
	global_position.x = 150.0
	
	# 应用移动（虽然velocity.x=0，但保持调用以维持物理状态）
	move_and_slide()
	global_position.x = 150.0

func switch_lane() -> bool:
	# 切换跑道
	if not is_switching:
		is_upper_lane = not is_upper_lane
		if anim and anim.has_animation("switch"):
			anim.play("switch")
		return true
	return false

func get_current_lane() -> String:
	return "upper" if is_upper_lane else "lower"

func attack() -> bool:
	if not is_attacking:
		is_attacking = true
		if anim and anim.has_animation("attack"):
			anim.play("attack")
		_attack_cooldown()
		return true
	return false

func _attack_cooldown() -> void:
	await get_tree().create_timer(0.2).timeout
	is_attacking = false

func check_enemy_hit() -> Array:
	# 检查攻击范围内是否有敌人
	var enemies: Array = []
	if attack_area:
		var overlapping_bodies := attack_area.get_overlapping_bodies()
		for body in overlapping_bodies:
			if body is Note and body.note_type == "enemy":
				enemies.append(body)
	return enemies
