from PIL import Image, ImageDraw, ImageFont
import re
import os
from typing import Tuple
from .logger import logging

CONFIG = {
    "background_image_path": "req/Всего по немногу5-ТОВ «Вайн Корк»(1).png",
    "form2_background": "req/Всего лишь скидка1-ТОВ «Вайн Корк»(1).png",
    "fonts": {
        "bold": "req/Evolventa-Bold.ttf",
        "regular": "req/Evolventa-Regular.ttf"
    },
    "output_directory": "output",
    "country_images_path": "req/country"
}

os.makedirs(CONFIG["output_directory"], exist_ok=True)

def remove_symbols(text: str) -> str:
    invalid_chars_pattern = r'[\\/:*?"<>|]'
    return re.sub(invalid_chars_pattern, '', text)

def add_newlines(text: str, max_line_length: int = 20) -> Tuple[str, int]:
    words = text.split()
    current_line_length = 0
    formatted_text = ""
    line_count = 0

    for word in words:
        word_length = len(word)
        if word == "|":
            formatted_text += "\n"
            current_line_length = 0
            line_count += 1
        elif current_line_length + word_length + 1 <= max_line_length:
            formatted_text += word + " "
            current_line_length += word_length + 1
        else:
            formatted_text += "\n" + word + " "
            current_line_length = word_length + 1
            line_count += 1

    if formatted_text:
        line_count += 1

    return formatted_text.strip(), line_count

def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path, size)

def form1(
    product_id: str,
    name: str,
    weight: str,
    price: int,
    country: str = "",
    bypass_text: bool = False
) -> None:
    if not country:
        background_path = CONFIG["background_image_path"]
    else:
        background_path = os.path.join(CONFIG["country_images_path"], f"{country.upper()}.png")
    
    try:
        background = Image.open(background_path)
    except FileNotFoundError:
        logging.critical(f"Background image for country '{country}' not found. ID: {product_id}, Name: {name}")
        return

    if bypass_text:
        text = name.upper()
    else:
        max_length = 17 if country else 20
        text, _ = add_newlines(name.upper(), max_length)

    card_width, card_height = background.size

    bold_font = load_font(CONFIG["fonts"]["bold"], 47)
    regular_font = load_font(CONFIG["fonts"]["regular"], 25)
    price_font = load_font(CONFIG["fonts"]["bold"], 85)

    draw = ImageDraw.Draw(background)

    text_bbox = draw.textbbox((0, 0), text, font=bold_font)
    price_text = str(price)
    price_bbox = draw.textbbox((0, 0), price_text, font=price_font)

    name_x = 45
    name_y = card_height - 227 - (text_bbox[3] - text_bbox[1])
    weight_x = 45
    weight_y = 345
    price_x = card_width - 45 - (price_bbox[2] - price_bbox[0])
    price_y = 380

    draw.text((name_x, name_y), text, fill=(0, 0, 0), font=bold_font, spacing=13)
    draw.text((weight_x, weight_y), weight, fill=(0, 0, 0), font=regular_font)
    draw.text((price_x, price_y), price_text, fill=(176, 31, 35), font=price_font, align="right")

    sanitized_filename = remove_symbols(f"{product_id}_{name}").replace("\n", "")
    output_path = os.path.join(CONFIG["output_directory"], f"{sanitized_filename}.png")
    background.save(output_path)

    if weight.lower() == "none":
        logging.error(f"{name} | {weight} | {price}")
    else:
        logging.success(f"{name} | {weight} | {price}")

def round_to_nearest(num: int, base: int) -> int:
    return base * round(num / base)

def round_discount_percentage(percentage: int) -> int:
    rounded_to_10 = round_to_nearest(percentage, 10)
    rounded_to_15 = round_to_nearest(percentage, 15)

    if abs(percentage - rounded_to_15) < abs(percentage - rounded_to_10):
        return rounded_to_15
    return rounded_to_10

def form2(
    product_id: str,
    name: str,
    weight: str,
    price: int,
    old_price: int,
    is_not_percentage: bool = False,
    bypass_text: bool = False
) -> None:
    if bypass_text:
        text = name
    else:
        text, _ = add_newlines(name.upper(), 17)

    try:
        background = Image.open(CONFIG["form2_background"])
    except FileNotFoundError:
        logging.critical(f"Form2 background image not found. ID: {product_id}, Name: {name}")
        return

    card_width, card_height = background.size

    large_font = load_font(CONFIG["fonts"]["bold"], 122)
    medium_font = load_font(CONFIG["fonts"]["regular"], 92)
    price_font_large = load_font(CONFIG["fonts"]["bold"], 220)
    discount_font = load_font(CONFIG["fonts"]["bold"], 220)
    price_font_regular = load_font(CONFIG["fonts"]["regular"], 168)

    draw = ImageDraw.Draw(background)

    discount_percentage = int(100 - (100 * old_price / price))
    rounded_discount = round_discount_percentage(discount_percentage)

    formatted_price = f"{price} ГРН"
    formatted_old_price = f"{old_price} ГРН"
    discount_text = f"-{rounded_discount}%"

    text_bbox = draw.textbbox((0, 0), text, font=large_font)
    price_bbox = draw.textbbox((0, 0), formatted_price, font=load_font(CONFIG["fonts"]["regular"], 168))
    discount_bbox = draw.textbbox((0, 0), discount_text, font=discount_font)
    old_price_bbox = draw.textbbox((0, 0), formatted_old_price, font=price_font_large)

    name_x = 120
    name_y = card_height - 900 - (text_bbox[3] - text_bbox[1])
    weight_x = 133
    weight_y = 1278
    old_price_x = card_width - 125 - (price_bbox[2] - price_bbox[0])
    old_price_y = 1400
    price_x = card_width - 115 - (old_price_bbox[2] - old_price_bbox[0])
    price_y = 1590
    discount_x = card_width - 800 - (discount_bbox[2] - discount_bbox[0])
    discount_y = 135

    draw.text((name_x, name_y), text, fill=(0, 0, 0), font=large_font, spacing=35)
    draw.text((weight_x, weight_y), weight, fill=(50, 44, 43), font=medium_font)
    draw.text((price_x, price_y), formatted_old_price, fill=(176, 31, 35), font=price_font_large, align="right")

    if not is_not_percentage:
        draw.text((discount_x, discount_y), discount_text, fill=(176, 31, 35), font=discount_font, align="right")

    draw.text(
        (old_price_x, old_price_y),
        formatted_price,
        fill=(50, 44, 43),
        font=price_font_regular,
        align="right"
    )

    line_start_1 = (old_price_x - 20, 1420)
    line_end_1 = (1300, 1520)
    line_start_2 = (old_price_x - 20, 1520)
    line_end_2 = (1300, 1420)
    line_color = (0, 0, 0)
    line_width = 6

    draw.line([line_start_1, line_end_1], fill=line_color, width=line_width)
    draw.line([line_start_2, line_end_2], fill=line_color, width=line_width)

    sanitized_filename = remove_symbols(f"{product_id}_{name}").replace("\n", "")
    output_path = os.path.join(CONFIG["output_directory"], f"{sanitized_filename}.png")
    background.save(output_path)
    
    if weight.lower() == "none":
        logging.error(f"{name} | {weight} | {price} | {old_price}")
    else:
        logging.success(f"{name} | {weight} | {price} | {old_price}")
