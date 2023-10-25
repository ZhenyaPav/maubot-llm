from PIL import Image
import base64, json
from .utils import replace_tags

def get_char_data(image_path:str) -> dict:
    try:
        # Open the image file
        with Image.open(image_path) as img:
            # Get the EXIF data
            exif_data = img.getexif()
            chara = base64.b64decode(img.text['chara']).decode('utf-8')
            data = json.loads(chara)
            return data
    except Exception as e:
        print(f"Error: {e}")

def get_char_system_prompt(char:dict, user_name:str) -> str:
    prompt = ''
    prompt += char['description'] + '\n'
    if 'personality' in char:
        prompt += f'\n{{{{char}}}}\'s personality: {char["personality"]}\n'
    if 'scenario' in char:
        prompt += f'Scenario: {char["scenario"]}\n'
    if 'mes_example' in char:
        prompt += replace_tags(char['mes_example'], char['name'], user_name)
    return prompt

if __name__ == "__main__":
    char = get_char_data("/media/veracrypt2/Downloads/main_Emily _tavern.png")
    print(get_char_system_prompt(char, "Eugene"))