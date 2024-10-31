import gradio as gr
from src.core.music_generator import MusicGenerator
import threading

class MusicGeneratorGUI:
    def __init__(self, generator: MusicGenerator):
        self.generator = generator

    def update_mode(self, mode):
        mode = mode.lower().replace(" mode", "")
        self.generator.current_mode = mode
        return [
            gr.update(visible=(mode == "linked")),
            gr.update(visible=(mode == "individual")),
            f"{mode.capitalize()} モードに切り替えました。"
        ]
    
    def update_auto_intensity(self, auto):
        self.generator.manual_mode = not auto
        return gr.update(
            value=self.generator.intensity_level,
            interactive=not auto
        )
    
    def update_linked_intensity(self, level):
        self.generator.intensity_level = level
        self.generator.manual_mode = True
        return f"強度レベルが {level} に設定されました。"

    def update_individual_levels(self, rhythm, velocity, melody, bass):
        self.generator.rhythm_level = rhythm
        self.generator.velocity_level = velocity
        self.generator.melody_level = melody
        self.generator.bass_level = bass
        return "個別レベルが更新されました。"

    def start_music(self):
        result = self.generator.start_music()
        if result == "音楽の生成を開始しました。":
            music_thread = threading.Thread(target=self.generator.play_polyphonic_composition, daemon=True)
            music_thread.start()
        return result

    def stop_music(self):
        return self.generator.stop_music()

    def create_interface(self):
        with gr.Blocks() as demo:
            gr.Markdown("# Music Generation by 12-tone Technique")
            
            with gr.Row():
                start_btn = gr.Button("Start")
                stop_btn = gr.Button("Stop")
            
            mode_radio = gr.Radio(
                ["Linked Mode", "Individual Mode"], 
                label="Mode Selection", 
                value="Linked Mode"
            )
            
            with gr.Accordion("Linked Mode Settings", visible=True) as linked_settings:
                with gr.Row():
                    auto_intensity = gr.Checkbox(
                        label="Randomly change intensity levels(1-4)", 
                        value=not self.generator.manual_mode
                    )
                linked_slider = gr.Slider(
                    1, 4, step=1, 
                    label="Intensity Level", 
                    value=self.generator.intensity_level, 
                    interactive=self.generator.manual_mode
                )
            
            with gr.Accordion("Individual Mode Settings", visible=False) as individual_settings:
                rhythm_slider = gr.Slider(1, 4, step=1, label="Rhythm", value=self.generator.rhythm_level)
                velocity_slider = gr.Slider(1, 4, step=1, label="Velocity", value=self.generator.velocity_level)
                melody_slider = gr.Slider(1, 4, step=1, label="Melody", value=self.generator.melody_level)
                bass_slider = gr.Slider(1, 4, step=1, label="Bass", value=self.generator.bass_level)
            
            output = gr.Textbox(label="Status")
            
            mode_radio.change(
                self.update_mode,
                inputs=[mode_radio],
                outputs=[linked_settings, individual_settings, output]
            )
            
            auto_intensity.change(
                self.update_auto_intensity, 
                inputs=[auto_intensity], 
                outputs=[linked_slider]
            )
            
            linked_slider.change(
                self.update_linked_intensity, 
                inputs=[linked_slider], 
                outputs=[output]
            )
            
            individual_sliders = [rhythm_slider, velocity_slider, melody_slider, bass_slider]
            for slider in individual_sliders:
                slider.change(
                    self.update_individual_levels, 
                    inputs=individual_sliders, 
                    outputs=[output]
                )
            
            start_btn.click(self.start_music, outputs=[output])
            stop_btn.click(self.stop_music, outputs=[output])

        return demo
