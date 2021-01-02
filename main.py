import logging
from pathlib import Path
import argparse
from combiner import *
from geom_removal import remove_redundant_geometry
from stl import save_to_stl, save_to_step
from OCC.Display.SimpleGui import init_display
from face_factory import FaceFactory

logger = logging.getLogger("TFT")
logger.setLevel(logging.DEBUG)

display, start_display, _, _ = init_display()

# Also, useful site to make svg letters: https://maketext.io/
# My blessed documentation: https://old.opencascade.com/doc/occt-6.9.0/refman/html/class_geom2d___b_spline_curve.html#a521ec5263443aca0d5ec43cd3ed32ac6
def main(word1, word2, height_mm, output_dir):
    display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
    display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
    display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")

    face_images_dir = Path(__file__).parent / "face_images/aldrich"
    face_factory = FaceFactory(face_images_dir)

    letters, faces1, faces2 = combine_words(word1, word2, face_factory, height_mm)
    # letters = remove_redundant_geometry(letters)
    letters = offset_shapes(letters, height_mm)

    for letter in letters:
        if letter:
            display.DisplayShape(letter)

    save_to_stl(letters, output_dir)
    save_to_step(letters, output_dir)

    start_display()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Combine words into Two-Faced Type, and output as STLs")
    parser.add_argument('words', metavar='word', type=str, nargs=2, help='the words to combine')
    parser.add_argument('-o', '--output_dir', metavar='output_directory', type=str,
                        help="The directory to write STL files to. Will be created if it doesn't exist", required=True)
    parser.add_argument('--height', metavar='height_mm', type=float, help="The height of the characters, in mm",
                        required=True)
    args = parser.parse_args()

    main(args.words[0], args.words[1], args.height, args.output_dir)

