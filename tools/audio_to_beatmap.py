#!/usr/bin/env python3
"""
Audio → Beatmap Generator (Enhanced Version)
============================================

Purpose:
    Perform deep audio analysis from an audio file (supports .ogg/.wav/.mp3 etc.)
    and generate different beatmaps for three difficulty levels (Easy, Normal, Hard).

Enhanced audio analysis features:
    - BPM estimation and beat tracking
    - Onset detection
    - Spectral analysis (spectral centroid, spectral rolloff, zero crossing rate)
    - Energy envelope analysis
    - Beat strength analysis
    - Dynamic range analysis
    - Frequency band energy distribution (low, mid, high)
    - Music structure analysis with dynamic difficulty adjustment
    - Melodic contour analysis for melodic pattern generation

Usage (from project root):
    pip install -r requirements.txt
    python tools/audio_to_beatmap.py godot/assets/audio/song1.ogg

Note:
    The script automatically generates beatmap files for three difficulties:
    - godot/data/beatmaps/song1_easy.json
    - godot/data/beatmaps/song1_normal.json
    - godot/data/beatmaps/song1_hard.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import random
from dataclasses import dataclass
from enum import Enum

import librosa
import numpy as np


class MusicSection(Enum):
    INTRO = "intro"
    VERSE = "verse"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    OUTRO = "outro"
    DROP = "drop"
    BREAK = "break"


@dataclass
class DynamicDifficultySegment:
    start_time: float
    end_time: float
    intensity: float  # 0.0-1.0
    density_multiplier: float
    complexity_multiplier: float
    section_type: MusicSection


@dataclass
class MelodicContour:
    """Represents melodic contour information for pattern generation"""
    pitch_sequence: List[float]  # Normalized pitch values (0.0-1.0)
    contour_type: str  # "ascending", "descending", "arc", "stable", "complex"
    start_time: float
    end_time: float
    strength: float  # How prominent this melodic contour is


@dataclass
class AudioAnalysis:
    """Data structure for audio analysis results"""
    bpm: float
    duration: float
    beat_times: List[float]
    onset_times: List[float]
    onset_strengths: List[float]
    spectral_centroids: np.ndarray
    spectral_rolloff: np.ndarray
    zero_crossing_rate: np.ndarray
    rms_energy: np.ndarray
    tempo_strength: float
    dynamic_range: float
    low_freq_energy: np.ndarray
    mid_freq_energy: np.ndarray
    high_freq_energy: np.ndarray
    beat_strengths: List[float]
    sustained_notes: List[Tuple[float, float, float]]  # (start_time, end_time, strength)
    music_sections: List[DynamicDifficultySegment]
    chroma_features: np.ndarray
    harmonic_content: np.ndarray
    percussive_content: np.ndarray
    melodic_contours: List[MelodicContour]  # Melodic contour analysis
    # Multi-layer spectral features for advanced note generation
    spectral_flatness: np.ndarray  # Controls note randomness (0-1, higher = more random)
    spectral_flux: np.ndarray  # Controls note density (higher = more notes)


def detect_melodic_contours(
    y: np.ndarray,
    sr: int,
    duration: float,
    hop_length: int = 512
) -> List[MelodicContour]:
    """
    Detect melodic contours in the audio for pattern-based note generation
    
    This analyzes the pitch content over time to identify melodic patterns
    that can be used to create more musically meaningful note sequences.
    """
    print("[Melodic Analysis] Detecting melodic contours...")
    
    # Extract pitch using librosa's piptrack
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)
    
    # Get dominant pitches over time
    dominant_pitches = []
    pitch_strengths = []
    
    for i in range(pitches.shape[1]):
        index = magnitudes[:, i].argmax()
        pitch = pitches[index, i]
        strength = magnitudes[index, i]
        
        if pitch > 0 and strength > 0.1:  # Filter out weak/noisy pitches
            dominant_pitches.append(pitch)
            pitch_strengths.append(strength)
        else:
            dominant_pitches.append(0.0)
            pitch_strengths.append(0.0)
    
    # Normalize pitches to 0-1 range for pattern recognition
    valid_pitches = [p for p in dominant_pitches if p > 0]
    if len(valid_pitches) > 0:
        min_pitch = min(valid_pitches)
        max_pitch = max(valid_pitches)
        pitch_range = max_pitch - min_pitch
        
        if pitch_range > 0:
            normalized_pitches = [
                (p - min_pitch) / pitch_range if p > 0 else 0.0 
                for p in dominant_pitches
            ]
        else:
            normalized_pitches = [0.5 if p > 0 else 0.0 for p in dominant_pitches]
    else:
        normalized_pitches = [0.0] * len(dominant_pitches)
    
    # Detect contour segments using sliding window
    contours: List[MelodicContour] = []
    window_size = min(8, len(normalized_pitches) // 20)  # Adaptive window size, reduced to avoid too many contours
    
    for i in range(0, len(normalized_pitches) - window_size, window_size):
        segment = normalized_pitches[i:i + window_size]
        valid_segment = [p for p in segment if p > 0]
        
        if len(valid_segment) < 3:  # Need at least 3 points for contour analysis
            continue
        
        # Calculate contour characteristics
        start_val = valid_segment[0]
        end_val = valid_segment[-1]
        max_val = max(valid_segment)
        min_val = min(valid_segment)
        
        # Determine contour type
        if end_val > start_val + 0.2:
            contour_type = "ascending"
        elif start_val > end_val + 0.2:
            contour_type = "descending"
        elif max_val - min_val < 0.1:
            contour_type = "stable"
        elif start_val < end_val and max_val > end_val + 0.1:
            contour_type = "arc"
        else:
            contour_type = "complex"
        
        # Calculate segment strength (average magnitude)
        strength_segment = pitch_strengths[i:i + window_size]
        avg_strength = np.mean([s for s in strength_segment if s > 0]) if any(strength_segment) else 0.0
        
        # Convert frame indices to time
        start_time = librosa.frames_to_time(i, sr=sr, hop_length=hop_length)
        end_time = librosa.frames_to_time(i + window_size, sr=sr, hop_length=hop_length)
        
        if avg_strength > 0.05 and (end_time - start_time) > 0.5:  # Only include reasonably strong contours with minimum duration
            contours.append(MelodicContour(
                pitch_sequence=valid_segment,
                contour_type=contour_type,
                start_time=start_time,
                end_time=end_time,
                strength=avg_strength
            ))
    
    print(f"[Melodic Analysis] Detected {len(contours)} melodic contours")
    
    # Sort by strength and keep the strongest ones (limit to reasonable number)
    contours.sort(key=lambda x: x.strength, reverse=True)
    return contours[:50]  # Limit to top 50 strongest contours to avoid excessive patterns


def detect_music_sections(
    y: np.ndarray,
    sr: int,
    duration: float,
    hop_length: int = 512
) -> List[DynamicDifficultySegment]:
    print("[Structure Analysis] Detecting music sections...")
    
    # Calculate beat-synchronous features
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    rms_energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    
    # Use librosa's structure analysis
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    beat_frames = librosa.util.fix_frames(beats, x_min=0, x_max=len(onset_env)-1)
    
    # Calculate beat-synchronous chroma features
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    chroma_sync = librosa.util.sync(chroma, beat_frames, aggregate=np.median)
    
    # Calculate structure similarity matrix
    similarity = librosa.segment.recurrence_matrix(chroma_sync, mode='affinity')
    
    # Detect section boundaries
    bounds = librosa.segment.agglomerative(similarity, k=8)  # Detect 8 main sections
    
    # Convert boundaries to time
    bound_times = librosa.frames_to_time(bounds, sr=sr, hop_length=hop_length)
    
    sections: List[DynamicDifficultySegment] = []
    
    # Analyze intensity characteristics of each section
    for i in range(len(bound_times) - 1):
        start_time = bound_times[i]
        end_time = bound_times[i + 1]
        
        # Calculate average energy intensity for this section
        start_frame = librosa.time_to_frames(start_time, sr=sr, hop_length=hop_length)
        end_frame = librosa.time_to_frames(end_time, sr=sr, hop_length=hop_length)
        
        segment_energy = rms_energy[start_frame:end_frame]
        segment_onset = onset_env[start_frame:end_frame]
        
        if len(segment_energy) > 0:
            intensity = float(np.mean(segment_energy) / np.max(rms_energy))
            onset_intensity = float(np.mean(segment_onset) / np.max(onset_env))
            
            # Combined intensity
            combined_intensity = (intensity + onset_intensity) / 2
            
            # Infer section type based on intensity
            if i == 0:
                section_type = MusicSection.INTRO
                # Intro usually has lower intensity
                combined_intensity *= 0.7
            elif i == len(bound_times) - 2:
                section_type = MusicSection.OUTRO
                combined_intensity *= 0.8
            elif combined_intensity > 0.7:
                section_type = MusicSection.CHORUS  # High intensity might be chorus
            elif combined_intensity > 0.5:
                section_type = MusicSection.VERSE   # Medium intensity might be verse
            else:
                section_type = MusicSection.BRIDGE  # Low intensity might be bridge
            
            # Calculate density and complexity multipliers
            density_multiplier = 0.5 + combined_intensity  # 0.5-1.5
            complexity_multiplier = 0.6 + combined_intensity * 0.9  # 0.6-1.5
            
            sections.append(DynamicDifficultySegment(
                start_time=start_time,
                end_time=end_time,
                intensity=combined_intensity,
                density_multiplier=density_multiplier,
                complexity_multiplier=complexity_multiplier,
                section_type=section_type
            ))
    
    print(f"[Structure Analysis] Detected {len(sections)} music sections")
    for i, section in enumerate(sections):
        print(f"                  Section {i+1}: {section.section_type.value} "
              f"({section.start_time:.1f}s-{section.end_time:.1f}s) "
              f"Intensity: {section.intensity:.2f}")
    
    return sections


def analyse_audio_enhanced(
    audio_path: Path,
    sr: int = 22050,
    hop_length: int = 512,
) -> AudioAnalysis:
    """
    Enhanced audio analysis function extracting multiple musical features.

    Returns:
        AudioAnalysis: Data structure containing all analysis results
    """
    print(f"[Analysis] Loading audio file: {audio_path}")
    y, sr = librosa.load(str(audio_path), sr=sr, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)
    
    print(f"[Analysis] Audio duration: {duration:.2f} seconds")
    print(f"[Analysis] Sample rate: {sr} Hz")
    
    # 1. BPM and beat tracking
    print("[Analysis] Estimating BPM and detecting beats...")
    tempo, beat_frames = librosa.beat.beat_track(
        y=y, sr=sr, hop_length=hop_length, units='time'
    )
    # tempo might be numpy array, convert to single float
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
    else:
        tempo = float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length).tolist()
    
    # Calculate beat strengths (based on onset strength)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    beat_strengths = []
    for beat_time in beat_times:
        beat_frame = librosa.time_to_frames(beat_time, sr=sr, hop_length=hop_length)
        if 0 <= beat_frame < len(onset_env):
            beat_strengths.append(float(onset_env[beat_frame]))
        else:
            beat_strengths.append(0.0)
    
    # 2. Onset detection
    print("[Analysis] Detecting onsets (drums/strong hits)...")
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=hop_length,
        units='time', backtrack=True
    )
    onset_times = onset_frames.tolist()
    
    # Get strength for each onset
    onset_strengths = []
    for onset_time in onset_times:
        onset_frame = librosa.time_to_frames(onset_time, sr=sr, hop_length=hop_length)
        if 0 <= onset_frame < len(onset_env):
            onset_strengths.append(float(onset_env[onset_frame]))
        else:
            onset_strengths.append(0.0)
    
    # 3. Spectral analysis
    print("[Analysis] Performing spectral analysis...")
    stft = librosa.stft(y, hop_length=hop_length)
    magnitude = np.abs(stft)
    
    # Spectral centroid - reflects timbre brightness
    spectral_centroids = librosa.feature.spectral_centroid(
        y=y, sr=sr, hop_length=hop_length
    )[0]
    
    # Spectral rolloff - reflects spectral energy concentration
    spectral_rolloff = librosa.feature.spectral_rolloff(
        y=y, sr=sr, hop_length=hop_length
    )[0]
    
    # Spectral flatness - measures how noise-like vs tone-like the sound is
    # Higher flatness (closer to 1) = more noise-like → more random note patterns
    # Lower flatness (closer to 0) = more tone-like → more structured patterns
    print("[Analysis] Calculating spectral flatness...")
    spectral_flatness = librosa.feature.spectral_flatness(
        y=y, S=magnitude, hop_length=hop_length
    )[0]
    # Normalize to 0-1 range
    if np.max(spectral_flatness) > 0:
        spectral_flatness = spectral_flatness / np.max(spectral_flatness)
    
    # Spectral flux - measures spectral change between frames
    # Higher flux = rapid spectral changes → higher note density
    # Lower flux = stable spectrum → lower note density
    print("[Analysis] Calculating spectral flux...")
    spectral_flux = np.zeros(magnitude.shape[1] - 1)
    for i in range(magnitude.shape[1] - 1):
        # Calculate difference between consecutive frames
        diff = magnitude[:, i+1] - magnitude[:, i]
        spectral_flux[i] = np.sum(np.abs(diff))
    # Normalize to 0-1 range
    if np.max(spectral_flux) > 0:
        spectral_flux = spectral_flux / np.max(spectral_flux)
    # Pad to match other features (add one frame at the end)
    spectral_flux = np.append(spectral_flux, spectral_flux[-1] if len(spectral_flux) > 0 else 0.0)
    
    # Zero crossing rate - reflects timbre roughness
    # Higher ZCR = more rhythmic/percussive → generate notes
    # Lower ZCR = more tonal/noisy → filter out or reduce notes
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]
    
    # 4. Energy analysis
    print("[Analysis] Analyzing energy envelope...")
    rms_energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    
    # Dynamic range (ratio of max to min energy)
    dynamic_range = float(np.max(rms_energy) / (np.min(rms_energy) + 1e-10))
    
    # 5. Frequency band energy analysis (low, mid, high)
    print("[Analysis] Analyzing frequency band energy distribution...")
    # Define frequency band boundaries (Hz)
    low_freq_max = 200  # Low frequency: 0-200Hz
    mid_freq_max = 2000  # Mid frequency: 200-2000Hz
    # High frequency: 2000Hz and above
    
    # Calculate frequency bins
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low_bin = np.argmax(freqs >= low_freq_max)
    mid_bin = np.argmax(freqs >= mid_freq_max)
    
    # Calculate energy per band
    low_freq_energy = np.sum(magnitude[:low_bin, :], axis=0)
    mid_freq_energy = np.sum(magnitude[low_bin:mid_bin, :], axis=0)
    high_freq_energy = np.sum(magnitude[mid_bin:, :], axis=0)
    
    # 6. Beat strength (overall rhythm sense)
    tempo_strength = float(np.mean(onset_env))
    
    # 7. Sustained note detection (for hold notes)
    print("[Analysis] Detecting sustained notes (hold notes)...")
    # Use lower energy threshold and shorter minimum duration for sustained note detection
    sustained_notes = detect_sustained_notes(
        y, sr, rms_energy, onset_env, hop_length, duration,
        min_duration=0.3,  # Reduce minimum duration to 0.3 seconds
        energy_threshold=0.15  # Reduce energy threshold to 0.15 (15%)
    )
    
    # 8. Music structure analysis
    music_sections = detect_music_sections(y, sr, duration, hop_length)
    
    # 9. Harmonic and percussive separation
    print("[Analysis] Performing harmonic and percussive separation...")
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    
    # Calculate chroma features (harmonic analysis)
    chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr, hop_length=hop_length)
    
    # Calculate harmonic and percussive content
    harmonic_content = librosa.feature.rms(y=y_harmonic, hop_length=hop_length)[0]
    percussive_content = librosa.feature.rms(y=y_percussive, hop_length=hop_length)[0]
    
    # 10. Melodic contour analysis
    melodic_contours = detect_melodic_contours(y, sr, duration, hop_length)
    
    # Ensure tempo is float
    tempo_float = float(tempo) if not isinstance(tempo, float) else tempo
    
    # FIXED: Use ASCII characters instead of Unicode checkmarks for Windows compatibility
    print(f"[Analysis] [OK] BPM: {tempo_float:.2f}")
    print(f"[Analysis] [OK] Detected {len(beat_times)} beats")
    print(f"[Analysis] [OK] Detected {len(onset_times)} onsets")
    print(f"[Analysis] [OK] Detected {len(sustained_notes)} sustained notes")
    print(f"[Analysis] [OK] Beat strength: {tempo_strength:.3f}")
    print(f"[Analysis] [OK] Dynamic range: {dynamic_range:.2f}")
    print(f"[Analysis] [OK] Detected {len(melodic_contours)} melodic contours")
    print(f"[Analysis] [OK] Spectral flatness range: {np.min(spectral_flatness):.3f} - {np.max(spectral_flatness):.3f}")
    print(f"[Analysis] [OK] Spectral flux range: {np.min(spectral_flux):.3f} - {np.max(spectral_flux):.3f}")
    
    return AudioAnalysis(
        bpm=tempo_float,
        duration=duration,
        beat_times=beat_times,
        onset_times=onset_times,
        onset_strengths=onset_strengths,
        spectral_centroids=spectral_centroids,
        spectral_rolloff=spectral_rolloff,
        zero_crossing_rate=zero_crossing_rate,
        rms_energy=rms_energy,
        tempo_strength=tempo_strength,
        dynamic_range=dynamic_range,
        low_freq_energy=low_freq_energy,
        mid_freq_energy=mid_freq_energy,
        high_freq_energy=high_freq_energy,
        beat_strengths=beat_strengths,
        sustained_notes=sustained_notes,
        music_sections=music_sections,
        chroma_features=chroma,
        harmonic_content=harmonic_content,
        percussive_content=percussive_content,
        melodic_contours=melodic_contours,
        spectral_flatness=spectral_flatness,
        spectral_flux=spectral_flux,
    )


def detect_sustained_notes(
    y: np.ndarray,
    sr: int,
    rms_energy: np.ndarray,
    onset_env: np.ndarray,
    hop_length: int,
    duration: float,
    min_duration: float = 0.3,
    energy_threshold: float = 0.15,
) -> List[Tuple[float, float, float]]:
    """
    Detect sustained notes (hold notes) in audio.
    
    Uses improved algorithm:
    1. Uses sliding window for energy smoothing
    2. Allows energy fluctuations (not all frames need to exceed threshold)
    3. Uses lower threshold and shorter minimum duration
    
    Parameters:
        min_duration: Minimum duration in seconds, default 0.3 seconds
        energy_threshold: Energy threshold (relative to max energy), default 0.15
    
    Returns:
        List[Tuple[float, float, float]]: List of (start_time, end_time, average_strength)
    """
    # Calculate energy threshold
    max_energy = np.max(rms_energy)
    mean_energy = np.mean(rms_energy)
    threshold = max(max_energy * energy_threshold, mean_energy * 1.2)  # At least 1.2x mean energy
    
    print(f"[Sustained Note Detection] Max energy: {max_energy:.4f}, Mean energy: {mean_energy:.4f}, Threshold: {threshold:.4f}")
    
    # Use moving average to smooth energy, reducing noise impact
    window_size = max(3, int(0.1 * sr / hop_length))  # About 0.1 second window
    if window_size % 2 == 0:
        window_size += 1
    
    smoothed_energy = np.convolve(rms_energy, np.ones(window_size) / window_size, mode='same')
    
    # Find regions where energy exceeds threshold (allow some fluctuation)
    # Use more lenient condition: allow some frames below threshold
    energy_frames = np.where(smoothed_energy >= threshold)[0]
    
    if len(energy_frames) == 0:
        print("[Sustained Note Detection] No regions found above energy threshold")
        return []

    # Merge consecutive frames into sustained segments (allow small gaps)
    sustained_segments: List[Tuple[int, int]] = []
    start_frame = energy_frames[0]
    max_gap = int(0.2 * sr / hop_length)  # Allow up to 0.2 second gaps
    
    for i in range(1, len(energy_frames)):
        gap = energy_frames[i] - energy_frames[i-1]
        if gap > max_gap:
            # Gap too large, end current segment
            end_frame = energy_frames[i-1]
            duration_frames = end_frame - start_frame + 1
            duration_seconds = librosa.frames_to_time(duration_frames, sr=sr, hop_length=hop_length)
            
            if duration_seconds >= min_duration:
                sustained_segments.append((start_frame, end_frame))
            
            start_frame = energy_frames[i]
    
    # Process last segment
    end_frame = energy_frames[-1]
    duration_frames = end_frame - start_frame + 1
    duration_seconds = librosa.frames_to_time(duration_frames, sr=sr, hop_length=hop_length)
    if duration_seconds >= min_duration:
        sustained_segments.append((start_frame, end_frame))
    
    print(f"[Sustained Note Detection] Found {len(sustained_segments)} sustained segments (min duration: {min_duration} seconds)")
    
    # Convert to time and calculate average strength
    sustained_notes: List[Tuple[float, float, float]] = []
    for start_frame, end_frame in sustained_segments:
        start_time = librosa.frames_to_time(start_frame, sr=sr, hop_length=hop_length)
        end_time = librosa.frames_to_time(end_frame, sr=sr, hop_length=hop_length)
        actual_duration = end_time - start_time
        
        # Calculate average energy strength for this segment
        segment_energy = rms_energy[start_frame:end_frame+1]
        avg_strength = float(np.mean(segment_energy) / max_energy)
        
        sustained_notes.append((start_time, end_time, avg_strength))
        print(f"[Sustained Note Detection]   Segment {len(sustained_notes)}: {start_time:.2f}s - {end_time:.2f}s (duration: {actual_duration:.2f}s, strength: {avg_strength:.3f})")
    
    return sustained_notes


def get_section_at_time(
    analysis: AudioAnalysis,
    time: float
) -> Optional[DynamicDifficultySegment]:
    """Get the music section at specified time"""
    for section in analysis.music_sections:
        if section.start_time <= time <= section.end_time:
            return section
    return None


def get_dynamic_difficulty_params(
    analysis: AudioAnalysis,
    time: float,
    base_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Adjust difficulty parameters dynamically based on time and music section
    
    Returns:
        Adjusted difficulty parameters
    """
    section = get_section_at_time(analysis, time)
    
    if section is None:
        return base_params.copy()
    
    # Adjust parameters based on section intensity
    adjusted_params = base_params.copy()
    
    # Dynamically adjust note density
    adjusted_params["min_interval"] = base_params["min_interval"] / section.density_multiplier
    
    # Dynamically adjust obstacle interval
    adjusted_params["obstacle_min_gap"] = base_params["obstacle_min_gap"] / section.density_multiplier
    
    # Dynamically adjust onset threshold (high intensity sections use lower threshold, generating more notes)
    adjusted_params["onset_threshold"] = base_params["onset_threshold"] * (1.2 - section.intensity)
    
    # Dynamically adjust hold note ratio (high intensity sections generate more hold notes)
    adjusted_params["hold_ratio"] = min(0.95, base_params["hold_ratio"] * (1.0 + section.intensity * 0.3))
    
    return adjusted_params


def generate_melodic_pattern(
    analysis: AudioAnalysis,
    time: float,
    lane: str,
    contour: MelodicContour
) -> List[Dict]:
    """
    Generate note patterns based on melodic contours
    
    Creates sequences of notes that follow the detected melodic patterns,
    making the beatmap more musically engaging and rhythmically interesting.
    """
    notes = []
    
    # Determine pattern density based on contour strength and type
    if contour.strength > 0.3:
        # Strong contour: generate more notes
        num_notes = random.randint(3, 6)
    else:
        # Weak contour: generate fewer notes
        num_notes = random.randint(2, 4)
    
    # Calculate time span for the pattern
    time_span = contour.end_time - contour.start_time
    if time_span < 0.5:  # Ensure minimum time span
        time_span = 0.5
    
    note_interval = time_span / (num_notes + 1)
    
    # Generate notes following the contour shape
    for i in range(num_notes):
        note_time = contour.start_time + (i + 1) * note_interval
        
        # Skip if too close to existing notes or outside audio duration
        if note_time > analysis.duration - 0.1:
            continue
        
        # Determine note type based on contour characteristics
        if contour.contour_type == "ascending" and i == num_notes - 1:
            # Last note of ascending pattern: high probability of obstacle
            note_type = "obstacle" if random.random() < 0.7 else "enemy"
        elif contour.contour_type == "descending" and i == 0:
            # First note of descending pattern: high probability of obstacle
            note_type = "obstacle" if random.random() < 0.7 else "enemy"
        elif contour.contour_type == "arc" and (i == 0 or i == num_notes - 1):
            # Start or end of arc pattern
            note_type = "obstacle" if random.random() < 0.6 else "enemy"
        else:
            # Regular notes: use normal distribution
            note_type = "enemy" if random.random() < 0.8 else "obstacle"
        
        notes.append({
            "time": round(float(note_time), 3),
            "type": note_type,
            "lane": lane,
            "melodic_pattern": True  # Mark as generated from melodic pattern
        })
    
    return notes


def build_notes_for_difficulty(
    analysis: AudioAnalysis,
    difficulty: str,
    min_interval: Optional[float] = None,
    enemy_ratio: Optional[float] = None,
    obstacle_min_gap: Optional[float] = None,
    onset_threshold: Optional[float] = None,
) -> List[Dict]:
    """
    Generate beatmap notes based on difficulty level with dynamic difficulty curve.
    
    Difficulty parameters:
        Easy:   Fewer notes, more lenient intervals, lower onset threshold
        Normal: Medium density, balanced intervals
        Hard:   More notes, denser intervals, higher onset threshold
    """
    # Set base parameters based on difficulty
    difficulty_params = {
        "Easy": {
            "min_interval": 0.3,      # Minimum interval 0.3 seconds
            "enemy_ratio": 0.7,        # 70% enemies, 30% obstacles
            "obstacle_min_gap": 0.8,   # Obstacle minimum interval 0.8 seconds
            "onset_threshold": 0.3,    # Only use onsets with strength > 0.3
            "use_beats": True,         # Use beats as supplement
            "hold_min_duration": 0.5,  # Hold note minimum duration 0.5 seconds (reduced)
            "hold_ratio": 0.6,        # 60% of sustained notes become hold notes (increased)
            "melodic_pattern_ratio": 0.3,  # 30% of melodic contours generate patterns
        },
        "Normal": {
            "min_interval": 0.2,
            "enemy_ratio": 0.6,
            "obstacle_min_gap": 0.6,
            "onset_threshold": 0.2,
            "use_beats": True,
            "hold_min_duration": 0.4,  # Hold note minimum duration 0.4 seconds (reduced)
            "hold_ratio": 0.7,        # 70% of sustained notes become hold notes (increased)
            "melodic_pattern_ratio": 0.5,  # 50% of melodic contours generate patterns
        },
        "Hard": {
            "min_interval": 0.15,
            "enemy_ratio": 0.5,
            "obstacle_min_gap": 0.4,
            "onset_threshold": 0.1,
            "use_beats": True,
            "hold_min_duration": 0.3,  # Hold note minimum duration 0.3 seconds (reduced)
            "hold_ratio": 0.8,        # 80% of sustained notes become hold notes (increased)
            "melodic_pattern_ratio": 0.7,  # 70% of melodic contours generate patterns
        },
    }
    
    base_params = difficulty_params.get(difficulty, difficulty_params["Normal"])
    
    # Use timestamp as random seed to ensure different beatmaps each run
    import time
    random.seed(int(time.time() * 1000) % 1000000)

    # 1. First process sustained notes to generate hold notes
    hold_notes: List[Dict] = []
    used_time_ranges: List[Tuple[float, float, str]] = []  # Track used time ranges and lanes (start, end, lane)
    
    # Time window for conflict checking (0.1 seconds)
    time_window: float = 0.1
    
    def get_time_slot(t: float) -> float:
        """Round time to nearest time window"""
        return round(t / time_window) * time_window
    
    def check_lane_conflict(start: float, end: float, lane: str, existing_ranges: List[Tuple[float, float, str]]) -> bool:
        """Check if time range and lane conflict with existing notes"""
        for existing_start, existing_end, existing_lane in existing_ranges:
            # If lane is same and time overlaps, conflict exists
            if existing_lane == lane:
                if not (end < existing_start or start > existing_end):
                    return True
        return False
    
    print(f"[Hold Note Generation] Detected {len(analysis.sustained_notes)} sustained notes, min duration requirement: {base_params['hold_min_duration']} seconds, conversion ratio: {base_params['hold_ratio']*100:.0f}%")
    
    for idx, (start_time, end_time, strength) in enumerate(analysis.sustained_notes):
        duration = end_time - start_time
        
        # Get dynamic parameters for current section
        section_params = get_dynamic_difficulty_params(analysis, start_time, base_params)
        
        # Only process sustained notes meeting minimum duration
        if duration < section_params["hold_min_duration"]:
            continue
        
        # Decide whether to generate hold note based on dynamic hold_ratio
        if random.random() > section_params["hold_ratio"]:
            continue
        
        # Check for overlap with already generated notes (check time range and lane)
        if check_lane_conflict(start_time, end_time, "upper", used_time_ranges):
            # Upper lane conflict, try lower lane
            if check_lane_conflict(start_time, end_time, "lower", used_time_ranges):
                # Both lanes conflict, skip this hold note
                continue
            else:
                lane = "lower"
        elif check_lane_conflict(start_time, end_time, "lower", used_time_ranges):
            # Lower lane conflict, use upper lane
            lane = "upper"
        else:
            # No conflict, decide lane based on energy
            frame = librosa.time_to_frames(start_time, sr=22050, hop_length=512)
            
            # First decide preferred lane based on energy
            preferred_lane: Optional[str] = None
            if frame < len(analysis.high_freq_energy) and frame < len(analysis.low_freq_energy):
                high_energy = analysis.high_freq_energy[frame]
                low_energy = analysis.low_freq_energy[frame]
                
                # Lower threshold for more even distribution
                if high_energy > low_energy * 1.1:
                    preferred_lane = "upper"
                elif low_energy > high_energy * 1.1:
                    preferred_lane = "lower"
            
            # If energy is similar or undetermined, alternate based on time
            if preferred_lane is None:
                preferred_lane = "upper" if (int(start_time * 2) % 2 == 0) else "lower"
            
            lane = preferred_lane
        
        hold_notes.append({
            "time": round(float(start_time), 3),
            "type": "hold",
            "lane": lane,
            "duration": round(float(duration), 3),  # Hold duration
        })
        
        # Record time range and lane occupied by hold note
        used_time_ranges.append((start_time, end_time, lane))
    
    # 2. Generate melodic pattern notes
    melodic_notes: List[Dict] = []
    print(f"[Melodic Pattern Generation] Detected {len(analysis.melodic_contours)} melodic contours, pattern generation ratio: {base_params['melodic_pattern_ratio']*100:.0f}%")
    
    for contour in analysis.melodic_contours:
        # Decide whether to generate pattern based on ratio
        if random.random() > base_params["melodic_pattern_ratio"]:
            continue
        
        # Choose lane based on contour characteristics
        if contour.contour_type in ["ascending", "arc"]:
            lane = "upper" if random.random() < 0.7 else "lower"
        elif contour.contour_type in ["descending", "stable"]:
            lane = "lower" if random.random() < 0.7 else "upper"
        else:  # complex
            lane = "upper" if random.random() < 0.5 else "lower"
        
        # Generate pattern notes
        pattern_notes = generate_melodic_pattern(analysis, contour.start_time, lane, contour)
        melodic_notes.extend(pattern_notes)
    
    # 3. Generate regular notes (enemy and obstacle)
    # Filter onsets: based on strength threshold
    filtered_onsets: List[Tuple[float, float]] = []
    for time, strength in zip(analysis.onset_times, analysis.onset_strengths):
        # Use dynamic threshold
        section_params = get_dynamic_difficulty_params(analysis, time, base_params)
        if strength >= section_params["onset_threshold"]:
            filtered_onsets.append((time, strength))
    
    # If using beats, also add some beat points (but with lower priority than onsets)
    candidate_times: List[Tuple[float, float, str]] = []
    for time, strength in filtered_onsets:
        candidate_times.append((time, strength, "onset"))
    
    if base_params["use_beats"]:
        # Add beat points (with lower priority)
        for beat_time, beat_strength in zip(analysis.beat_times, analysis.beat_strengths):
            # Check if there's already a nearby onset
            has_nearby_onset = any(
                abs(onset_time - beat_time) < 0.05
                for onset_time, _ in filtered_onsets
            )
            # Use dynamic threshold
            section_params = get_dynamic_difficulty_params(analysis, beat_time, base_params)
            if not has_nearby_onset and beat_strength > section_params["onset_threshold"] * 0.5:
                candidate_times.append((beat_time, beat_strength, "beat"))
    
    # Sort by time
    candidate_times.sort(key=lambda x: x[0])
    
    # Merge overly dense time points (using dynamic interval)
    merged: List[Tuple[float, float, str]] = []
    for time, strength, source in candidate_times:
        # Check for overlap with hold notes (regardless of lane, since hold notes occupy entire time range)
        overlaps_with_hold = False
        for used_start, used_end, _ in used_time_ranges:
            if used_start <= time <= used_end:
                overlaps_with_hold = True
                break
        
        if overlaps_with_hold:
            continue  # Skip time points overlapping with hold notes
        
        # Check for overlap with melodic pattern notes
        overlaps_with_melodic = any(
            abs(melodic_note["time"] - time) < 0.1
            for melodic_note in melodic_notes
        )
        
        if overlaps_with_melodic:
            continue  # Skip time points too close to melodic pattern notes
        
        # Use dynamic minimum interval
        section_params = get_dynamic_difficulty_params(analysis, time, base_params)
        dynamic_min_interval = section_params["min_interval"]
        
        if not merged or time - merged[-1][0] >= dynamic_min_interval:
            merged.append((time, strength, source))
    
    # Generate regular notes
    notes: List[Dict] = []
    last_obstacle_time: float = -1.0

    # Track lanes used in each time window (avoid both lanes having notes at same time)
    used_lanes_by_time: Dict[float, str] = {}  # {rounded_time: lane}
    
    def is_lane_available_at_time(t: float, lane: str) -> bool:
        """Check if specified lane is available at specified time window"""
        slot = get_time_slot(t)
        if slot not in used_lanes_by_time:
            return True
        return used_lanes_by_time[slot] != lane
    
    def check_note_conflict_at_time(t: float, lane: str) -> bool:
        """Check if specified time and lane conflict with hold notes"""
        for hold_start, hold_end, hold_lane in used_time_ranges:
            if hold_lane == lane and hold_start <= t <= hold_end:
                return True
        return False

    for time, strength, source in merged:
        # Get spectral features at this time point
        frame = librosa.time_to_frames(time, sr=22050, hop_length=512)
        
        # Get Zero-Crossing Rate to filter out noise segments
        # High ZCR = rhythmic/percussive (good for notes)
        # Low ZCR = tonal/noisy (filter out)
        zcr_at_time = 0.0
        if 0 <= frame < len(analysis.zero_crossing_rate):
            zcr_at_time = float(analysis.zero_crossing_rate[frame])
        
        # Normalize ZCR (typical range: 0-0.5, but can vary)
        zcr_normalized = min(1.0, zcr_at_time * 2.0)  # Scale to 0-1
        
        # Filter out notes in noise segments (low ZCR = more tonal/noisy, less rhythmic)
        # Only generate notes if ZCR is above threshold (indicating rhythmic content)
        zcr_threshold = 0.15  # Adjust based on typical ZCR values
        if zcr_normalized < zcr_threshold:
            # Low ZCR: likely noise/tonal segment, skip or reduce probability
            if random.random() > zcr_normalized / zcr_threshold:
                continue
        
        # Get Spectral Centroid to control note type (sharp vs mellow)
        # High centroid = bright/sharp sound → more obstacles
        # Low centroid = mellow sound → more enemies
        centroid_at_time = 0.0
        if 0 <= frame < len(analysis.spectral_centroids):
            centroid_at_time = float(analysis.spectral_centroids[frame])
        
        # Normalize centroid (typical range: 1000-5000 Hz, normalize to 0-1)
        centroid_normalized = min(1.0, (centroid_at_time - 1000) / 4000) if centroid_at_time > 1000 else 0.0
        
        # Get Spectral Flatness to control randomness
        # High flatness = noise-like → more random patterns
        # Low flatness = tone-like → more structured patterns
        flatness_at_time = 0.5  # Default
        if 0 <= frame < len(analysis.spectral_flatness):
            flatness_at_time = float(analysis.spectral_flatness[frame])
        
        # Get Spectral Flux to control note density
        # High flux = rapid changes → higher density
        # Low flux = stable → lower density
        flux_at_time = 0.5  # Default
        if 0 <= frame < len(analysis.spectral_flux):
            flux_at_time = float(analysis.spectral_flux[frame])
        
        # Apply spectral flux to density: higher flux = more likely to keep this note
        # Lower flux = more likely to skip (reduce density)
        flux_density_factor = 0.3 + flux_at_time * 0.7  # Range: 0.3-1.0
        if random.random() > flux_density_factor:
            continue  # Skip this note due to low spectral flux
        
        # Get dynamic parameters
        section_params = get_dynamic_difficulty_params(analysis, time, base_params)
        dynamic_enemy_ratio = section_params["enemy_ratio"]
        dynamic_obstacle_gap = section_params["obstacle_min_gap"]
        
        # Determine note type using Spectral Centroid
        # High centroid (bright/sharp) → obstacle (need to dodge)
        # Low centroid (mellow) → enemy (can attack)
        base_obstacle_prob = 0.3  # Base probability for obstacle
        
        # Adjust based on spectral centroid
        # High centroid increases obstacle probability
        obstacle_prob = base_obstacle_prob + (centroid_normalized * 0.4)  # Range: 0.3-0.7
        
        # Apply spectral flatness to add randomness
        # High flatness = more random, so add more variation
        if flatness_at_time > 0.6:
            # High flatness: add more randomness
            obstacle_prob += (random.random() - 0.5) * 0.3
            obstacle_prob = max(0.1, min(0.9, obstacle_prob))  # Clamp to 0.1-0.9
        
        # Also consider onset strength as secondary factor
        if source == "onset" and len(analysis.onset_strengths) > 0:
            strength_percentile = np.percentile(analysis.onset_strengths, 75)
            if strength > strength_percentile:
                # High strength onset: slightly favor obstacle
                obstacle_prob += 0.1
        
        # Final decision
        note_type = "obstacle" if random.random() < obstacle_prob else "enemy"

        # Check obstacle interval restriction (use dynamic interval)
        if note_type == "obstacle":
            if last_obstacle_time >= 0.0 and (time - last_obstacle_time) < dynamic_obstacle_gap:
                note_type = "enemy"
            else:
                last_obstacle_time = time
        
        # Determine lane based on energy distribution
        # High frequency energy high -> upper lane, low frequency energy high -> lower lane
        frame = librosa.time_to_frames(time, sr=22050, hop_length=512)
        
        # First decide preferred lane based on energy
        preferred_lane: Optional[str] = None
        if frame < len(analysis.high_freq_energy) and frame < len(analysis.low_freq_energy):
            high_energy = analysis.high_freq_energy[frame]
            low_energy = analysis.low_freq_energy[frame]
            
            # Lower threshold for more even distribution
            if high_energy > low_energy * 1.1:
                preferred_lane = "upper"
            elif low_energy > high_energy * 1.1:
                preferred_lane = "lower"
        
        # If energy is similar or undetermined, alternate based on time
        if preferred_lane is None:
            preferred_lane = "upper" if (int(time * 2) % 2 == 0) else "lower"
        
        # Check if preferred lane is available (including conflicts with hold notes)
        if is_lane_available_at_time(time, preferred_lane) and not check_note_conflict_at_time(time, preferred_lane):
            lane = preferred_lane
        else:
            # Preferred lane occupied, use other lane
            lane = "lower" if preferred_lane == "upper" else "upper"
            # If other lane also occupied or conflicts with hold notes, skip this note
            if not is_lane_available_at_time(time, lane) or check_note_conflict_at_time(time, lane):
                continue
        
        # Record used lane
        time_slot = get_time_slot(time)
        used_lanes_by_time[time_slot] = lane

        notes.append({
            "time": round(float(time), 3),
            "type": note_type,
            "lane": lane,
        })
    
    # 4. Merge all notes and sort by time
    all_notes = notes + hold_notes + melodic_notes
    all_notes.sort(key=lambda n: n["time"])
    
    return all_notes


def get_onset_strength_at_time(
    analysis: AudioAnalysis,
    time: float,
    sr: int = 22050,
    hop_length: int = 512,
) -> float:
    """Get onset strength at specified time"""
    if not analysis.onset_times:
        return 0.0
    
    # Find closest onset
    closest_idx = min(
        range(len(analysis.onset_times)),
        key=lambda i: abs(analysis.onset_times[i] - time)
    )
    
    if abs(analysis.onset_times[closest_idx] - time) < 0.1:  # Within 0.1 seconds
        return analysis.onset_strengths[closest_idx]
    return 0.0


def get_energy_at_time(
    analysis: AudioAnalysis,
    time: float,
    sr: int = 22050,
    hop_length: int = 512,
) -> float:
    """Get energy at specified time"""
    frame = librosa.time_to_frames(time, sr=sr, hop_length=hop_length)
    if 0 <= frame < len(analysis.rms_energy):
        return float(analysis.rms_energy[frame])
    return 0.0


def infer_godot_audio_path(audio_path: Path) -> str:
    """Convert disk path to Godot's res:// path"""
    parts = audio_path.resolve().parts
    if "godot" in parts:
        idx = parts.index("godot")
        relative_parts = parts[idx + 1 :]
        return "res://" + "/".join(relative_parts)
    return f"res://assets/audio/{audio_path.name}"


def build_beatmap(
    audio_path: Path,
    analysis: AudioAnalysis,
    notes: List[Dict],
    difficulty: str,
) -> Dict:
    """Assemble into beatmap structure used by the project"""
    godot_audio_path = infer_godot_audio_path(audio_path)
    title = f"{audio_path.stem} ({difficulty})"

    return {
        "title": title,
        "bpm": round(analysis.bpm, 2),
        "offset": 0.0,
        "audio": godot_audio_path,
        "notes": notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enhanced audio analysis and beatmap generation tool (supports multiple difficulties and dynamic difficulty curves)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "audio",
        type=Path,
        help="Input audio file path (e.g.: godot/assets/audio/song1.ogg)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: godot/data/beatmaps/)",
    )
    parser.add_argument(
        "--difficulties",
        nargs="+",
        choices=["Easy", "Normal", "Hard"],
        default=["Easy", "Normal", "Hard"],
        help="Difficulty levels to generate (default: all)",
    )
    args = parser.parse_args()

    if not args.audio.exists():
        raise SystemExit(f"Error: Audio file not found: {args.audio}")
    
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Default output to godot/data/beatmaps/
        project_root = args.audio.resolve()
        while project_root.name != "AIST2010-project" and project_root.parent != project_root:
            project_root = project_root.parent
        output_dir = project_root / "godot" / "data" / "beatmaps"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Audio Analysis & Beatmap Generation Tool (Enhanced - Dynamic Difficulty Curves)")
    print("=" * 60)
    
    # Perform audio analysis
    analysis = analyse_audio_enhanced(args.audio)
    
    print("\n" + "=" * 60)
    print("Starting beatmap generation...")
    print("=" * 60)
    
    # Generate beatmap for each difficulty
    for difficulty in args.difficulties:
        print(f"\n[Generation] {difficulty} difficulty...")
        notes = build_notes_for_difficulty(analysis, difficulty)
        
        beatmap = build_beatmap(args.audio, analysis, notes, difficulty)
        
        # Generate output filename
        output_file = output_dir / f"{args.audio.stem}_{difficulty.lower()}.json"
        
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(beatmap, f, ensure_ascii=False, indent=2)

        print(f"[Generation] [OK] {difficulty} difficulty: {len(notes)} notes")
        print(f"[Generation] [OK] Saved to: {output_file}")
    
    print("\n" + "=" * 60)
    print("Generation complete!")
    print("=" * 60)
    print(f"\nAudio analysis summary:")
    print(f"  - BPM: {analysis.bpm:.2f}")
    print(f"  - Duration: {analysis.duration:.2f} seconds")
    print(f"  - Beats: {len(analysis.beat_times)}")
    print(f"  - Onsets: {len(analysis.onset_times)}")
    print(f"  - Beat strength: {analysis.tempo_strength:.3f}")
    print(f"  - Dynamic range: {analysis.dynamic_range:.2f}")
    print(f"  - Music sections: {len(analysis.music_sections)}")
    print(f"  - Melodic contours: {len(analysis.melodic_contours)}")


if __name__ == "__main__":
    main()
