import json
from PIL import Image, ImageDraw, ImageFont

# Sample data (Use your full JSON here)
questions_data = json.load(open("./scripts/questions.json"))
def generate_question_image(data):
    # Image Settings
    width, height = 800, 500
    bg_color = (255, 255, 255)  # White background
    text_color = (44, 62, 80)   # Dark Blue-Grey
    accent_color = (52, 152, 219) # Blue

    # Create Image
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Attempt to load fonts (defaults to standard if not found)
    try:
        header_font = ImageFont.truetype("arial.ttf", 24)
        main_font = ImageFont.truetype("arial.ttf", 32)
        option_font = ImageFont.truetype("arial.ttf", 26)
    except:
        header_font = main_font = option_font = ImageFont.load_default()

    # Draw Header (Topic & Difficulty)
    draw.rectangle([0, 0, width, 60], fill=accent_color)
    draw.text((20, 15), f"{data['topic']} | {data['difficulty']}", fill=(255,255,255), font=header_font)

    # Draw Question
    draw.text((40, 100), data['question'], fill=text_color, font=main_font)

    # Draw Options
    y_pos = 180
    for key, val in data['options'].items():
        draw.text((60, y_pos), f"{key}) {val}", fill=text_color, font=option_font)
        y_pos += 60

    # Save
    img.save(data['image_path'])
    print(f"Generated: {data['image_path']}")

# Run for all questions
for q in questions_data:
    generate_question_image(q)