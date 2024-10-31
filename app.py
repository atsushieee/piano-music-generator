from src.core.music_generator import MusicGenerator
from src.gui.music_generator_gui import MusicGeneratorGUI


generator = MusicGenerator()
gui = MusicGeneratorGUI(generator)
demo = gui.create_interface()

def main():
    demo.launch()

if __name__ == "__main__":
    main()
