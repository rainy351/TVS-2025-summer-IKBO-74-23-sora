
from termcolor import cprint
import re


def process_colored_message(msg):
    # Регулярное выражение для поиска всех цветовых токенов
    pattern = r'(\[(?:YLW|GRY|GRN|RED|WHT)\]:)'
    parts = re.split(pattern, msg)
    parts = [part for part in parts if part.strip()]
    current_color = None
    
    for part in parts:
        if re.match(pattern, part):
            color_map = {
                '[YLW]:': 'yellow',
                '[GRY]:': 'grey',
                '[GRN]:': 'green',
                '[RED]:': 'red',
                '[WHT]:': 'white'
            }
            current_color = color_map.get(part)
        else:
            if current_color:
                cprint(part, current_color)
                current_color = None
            else:
                print(part)
   