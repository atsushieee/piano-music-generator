import random
import time
import fluidsynth
import yaml
import os
import requests
import zipfile
from tqdm import tqdm

class MusicGenerator:
    def __init__(self):
        self.is_playing = False
        self.intensity_level = random.randint(1, 4)
        self.manual_mode = False
        self.current_mode = "linked"
        self.rhythm_level = self.velocity_level = self.melody_level = self.bass_level = 1
        random.seed(None)
        
        # FluidSynthの初期化
        self.fs = fluidsynth.Synth()
        self.fs.start()
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'config', 'soundfont.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        soundfont_path = config['soundfont']['path']
        soundfont_dir = os.path.dirname(soundfont_path)

        if not os.path.exists(soundfont_path):
            print(f"The specified SoundFont file cannot be found. Start downloading...")
            try:
                self.download_and_setup_soundfont(soundfont_dir)
            except Exception as e:
                raise Exception(f"SoundFont download failed: {str(e)}")

        self.sfid = self.fs.sfload(soundfont_path)
        self.fs.sfont_select(0, self.sfid)
        self.fs.program_select(0, self.sfid, 0, 0)

    def __del__(self):
        if hasattr(self, 'fs'):
            self.fs.delete()

    def generate_twelve_tone_row(self, octave_range=1):
        base_octave = 60  # C4
        notes = [base_octave + i for i in range(12 * octave_range)]
        random.shuffle(notes)
        return notes

    def retrograde(self, row):
        return row[::-1]

    def inversion(self, row):
        base_note = row[0]
        return [base_note - (note - base_note) for note in row]

    def generate_dark_chords(self, octave_offset=0):
        base_chord = [
            [60, 63, 67], [62, 65, 69], [63, 66, 70], [65, 68, 72],
            [57, 60, 64], [59, 62, 65], [61, 64, 68], [58, 61, 64],
        ]
        chosen_chord = random.choice(base_chord)
        adjusted_chord = []
        for note in chosen_chord:
            adjusted_note = note + octave_offset
            while adjusted_note < 0:
                adjusted_note += 12
            adjusted_chord.append(adjusted_note)
        return adjusted_chord

    def generate_rhythm_dynamics_pitch(self):
        rhythm_base = [240, 180, 120, 60]
        velocity_base = [45, 69, 93, 117]
        rhythm_variation = [-30, 0, 30]
        velocity_variation = [-10, 0, 10]

        if self.current_mode == "linked":
            level = self.intensity_level
            rhythm = rhythm_base[level - 1] + random.choice(rhythm_variation)
            velocity = velocity_base[level - 1] + random.choice(velocity_variation)
            melody_octave_range = random.randint(-level, level)
            bass_octave_range = random.randint(-level, melody_octave_range)
        else:
            rhythm = rhythm_base[self.rhythm_level - 1] + random.choice(rhythm_variation)
            velocity = velocity_base[self.velocity_level - 1] + random.choice(velocity_variation)
            melody_octave_range = random.randint(-self.melody_level, self.melody_level)
            if melody_octave_range > 0:
                bass_octave_range = random.randint(-self.bass_level, min(self.bass_level, melody_octave_range))
            else:
                bass_octave_range = random.randint(-self.bass_level, max(self.bass_level, melody_octave_range))

        rhythm = max(30, rhythm)
        velocity = max(30, min(127, velocity))

        return rhythm, velocity, melody_octave_range, bass_octave_range

    def add_polyphonic_parts_to_output(self, melody_row, harmony_row):
        for i, note in enumerate(melody_row):
            rhythm, velocity, melody_octave_range, bass_octave_range = self.generate_rhythm_dynamics_pitch()

            note_with_offset = note + (12 * (melody_octave_range - 1))
            while note_with_offset < 0:
                note_with_offset += 12

            chord_size = random.randint(1, self.intensity_level + 1)
            dark_chord = self.generate_dark_chords(octave_offset=bass_octave_range * 12)
            chord_notes = random.sample(dark_chord, min(chord_size, len(dark_chord)))

            harmony_note = harmony_row[i % len(harmony_row)] + (bass_octave_range * 12)
            while harmony_note < 0:
                harmony_note += 12

            # FluidSynthを使用して音を再生
            self.fs.noteon(0, note_with_offset, int(velocity))
            self.fs.noteon(0, harmony_note, int(velocity - 20))
            
            for chord_note in chord_notes:
                self.fs.noteon(0, chord_note, int(velocity - 30))

            time.sleep(rhythm / 1000.0)

            # 音を停止
            self.fs.noteoff(0, note_with_offset)
            self.fs.noteoff(0, harmony_note)
            
            for chord_note in chord_notes:
                self.fs.noteoff(0, chord_note)

    def play_polyphonic_composition(self):
        self.is_playing = True

        original_row = self.generate_twelve_tone_row()
        row_retro = self.retrograde(original_row)
        row_inverted = self.inversion(original_row)
        row_retro_inverted = self.retrograde(row_inverted)

        while self.is_playing:
            # manual_modeの値を考慮
            if not self.manual_mode and self.current_mode == "linked":
                self.intensity_level = random.randint(1, 4)

            if random.random() < 0.25:
                original_row = self.generate_twelve_tone_row()
                row_retro = self.retrograde(original_row)
                row_inverted = self.inversion(original_row)
                row_retro_inverted = self.retrograde(row_inverted)

            melody_row = random.choice([original_row, row_retro, row_inverted, row_retro_inverted])
            harmony_row = random.choice([original_row, row_retro, row_inverted, row_retro_inverted])

            self.add_polyphonic_parts_to_output(melody_row, harmony_row)

        self.is_playing = False

    def start_music(self):
        if self.is_playing:
            return "Music is already playing."
        
        self.is_playing = True
        return "Music generation started."

    def stop_music(self):
        self.is_playing = False
        return "Music stopped."

    def download_and_setup_soundfont(self, soundfont_dir):
        zip_path = "FluidR3_GM.zip"
        url = "https://keymusician01.s3.amazonaws.com/FluidR3_GM.zip"
        
        # ディレクトリ作成
        os.makedirs(soundfont_dir, exist_ok=True)
        
        # ダウンロード
        print("Downloading SoundFont file....")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(zip_path, 'wb') as file, tqdm(
            desc="Downloading",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                progress_bar.update(size)
        
        # 解凍
        print("Unzipping files...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(soundfont_dir)
        
        # zipファイルの削除
        os.remove(zip_path)
        print("Set-up completed.")
