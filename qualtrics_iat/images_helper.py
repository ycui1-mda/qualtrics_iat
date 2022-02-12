from pathlib import Path
import cv2
import numpy as np
import os


def create_word_images(words,
                       target_folder,
                       category_name,
                       font=cv2.FONT_HERSHEY_DUPLEX,
                       font_scale=1,
                       image_size=(400, 400),
                       text_color=(0, 0, 0),
                       fill_color=(255, 255, 255)):
    """Create images for text stimuli as the center
    :param words: the list of words
    :param target_folder: the folder where the images will be saved
    :param category_name: the category name for the words (e.g., Pleasant, Good)
    :param font: the font of the text, by default, Hershey Duplex
    :param font_scale: the size of the font
    :param image_size: the size of the image (width, height), by default, 400 x 400
    :param text_color: the color (rgb values) of the word, by default, black
    :param fill_color: the color (rgb values) of the background, by default, white
    :return: None
    """
    for word in words:
        word_image = _image_with_color(fill_color, image_size)
        _draw_text(word_image, word, font, font_scale, text_color)
        target_path = _create_target_path(target_folder)
        file_destination = target_path / f"{category_name}_{word}.png"
        cv2.imwrite(os.fspath(file_destination), word_image)


def format_images(raw_folder,
                  target_folder,
                  category_name,
                  image_filename_pattern="*",
                  image_size=(400, 400),
                  fill_color=(255, 255, 255)):
    """Format the images to the desired size
    :param raw_folder: the folder where the raw images are saved, JPEG or PNG are preferred, BMP is OK
    :param target_folder: the folder where the created images are saved
    :param category_name: the category name for the images
    :param image_filename_pattern: the image filename pattern, by default, selects all
    :param image_size: the size of the image, default 400 x 400 pixels
    :param fill_color: the color when the image can't cover the desired size, default white
    :return: None
    """
    for image_file in Path(raw_folder).glob(image_filename_pattern):
        target_image = _image_with_color(fill_color, image_size)
        target_width, target_height = image_size
        raw_image = cv2.imread(str(image_file))
        raw_height, raw_width, _ = raw_image.shape
        height_ratio = target_height / raw_height
        width_ratio = target_width / raw_width
        change_ratio = min(width_ratio, height_ratio)
        resized_size = (min(int(raw_width * change_ratio), target_width),
                        min(int(raw_height * change_ratio), target_height))
        resized_image = cv2.resize(raw_image, resized_size)
        offset = (target_width - resized_size[0]) // 2, (target_height - resized_size[1]) // 2
        _paste(resized_image, target_image, offset)
        target_path = _create_target_path(target_folder)
        file_path = target_path / f"{category_name}_{image_file.stem}.png"
        cv2.imwrite(os.fspath(file_path), target_image)


def _create_target_path(target_folder):
    target_path = Path(target_folder)
    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)
    return target_path


def _paste(small_image, large_image, position=(0, 0)):
    """
    Paste a small image on a larger image
    :param small_image: the smaller image
    :param large_image: the larger image
    :param position: the position where the small image is pasted
    :return: None
    """
    x_offset, y_offset = position
    large_image[y_offset:y_offset+small_image.shape[0], x_offset:x_offset+small_image.shape[1]] = small_image


def _image_with_color(color, size):
    """
    Create an image with a solid color
    :param color: the color (rgb values) of the image
    :param size: the size of the image
    :return: the image that is created
    """
    width, height = size
    color_image = np.ones(shape=[height, width, 3], dtype=np.uint8)
    for color_index, color_value in enumerate(color):
        color_image[:, :, color_index] = color_value
    return color_image


def _draw_text(image, text, font, font_scale, color, x=None, y=None):
    """
    Draw text on an image
    :param image: the image that is to add an text
    :param text: the text that is to add to the image
    :param font: the font of the text
    :param font_scale: the font scale
    :param color: the color of the text
    :param x: the horizontal coordinate (x) for the text
    :param y: the vertical coordinate (y) for the text
    :return: None
    """
    thickness = 1
    image_height, image_width = image.shape[0], image.shape[1]
    text_width, text_height = cv2.getTextSize(text, font, font_scale, thickness)[0]
    if x is None:
        x = (image_width - text_width) // 2
    if y is None:
        y = (image_height + text_height) // 2
    cv2.putText(image, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
