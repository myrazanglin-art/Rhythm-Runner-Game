extends Node

var audio_enabled: bool = true
var _selected_difficulty: StringName = "Normal"
var _selected_song: StringName = "song1"

var _difficulty_sequence := [
	"Easy",
	"Normal",
	"Hard"
]

var _difficulty_data := {
	"Easy": {
		"description": "Slower spawn rate with generous timing windows."
	},
	"Normal": {
		"description": "Balanced challenge tuned for first clear."
	},
	"Hard": {
		"description": "Faster scroll speed and tighter timing."
	}
}

var _song_sequence := [
	"song1",
	"song2", 
	"song3",
	"song4",
	"song5"
]

var _song_data := {
	"song1": "res://assets/audio/song1.ogg",
	"song2": "res://assets/audio/song2.ogg",
	"song3": "res://assets/audio/song3.ogg",
	"song4": "res://assets/audio/song4.ogg",
	"song5": "res://assets/audio/song5.ogg"
}

func get_difficulty_names() -> PackedStringArray:
	var names := PackedStringArray()
	for difficulty_name in _difficulty_sequence:
		if _difficulty_data.has(difficulty_name):
			names.append(difficulty_name)
	return names

func get_difficulty_description(difficulty_name: String) -> String:
	if _difficulty_data.has(difficulty_name):
		return str(_difficulty_data[difficulty_name].get("description", ""))
	return ""

func set_difficulty(difficulty_name: String) -> void:
	if _difficulty_data.has(difficulty_name):
		_selected_difficulty = StringName(difficulty_name)

func get_selected_difficulty() -> String:
	return str(_selected_difficulty)

func get_selected_difficulty_index() -> int:
	return _difficulty_sequence.find(str(_selected_difficulty))

func get_song_names() -> PackedStringArray:
	var names := PackedStringArray()
	for song_name in _song_sequence:
		if _song_data.has(song_name):
			names.append(song_name)
	return names

func set_selected_song(song_name: String) -> void:
	if _song_data.has(song_name):
		_selected_song = StringName(song_name)

func get_selected_song() -> String:
	return str(_selected_song)

func get_selected_song_index() -> int:
	return _song_sequence.find(str(_selected_song))

func get_song_path(song_name: String) -> String:
	return _song_data.get(song_name, "")

func get_selected_song_path() -> String:
	return get_song_path(get_selected_song())
