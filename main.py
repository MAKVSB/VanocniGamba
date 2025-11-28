import pygame
import random
import sys
import glob

SEQUENCE_GEN_LEN = 100
ICONSIZE = 80

class SlotState:
    def __init__(self, pos_x, pos_y, size_x, size_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.size_x = size_x
        self.size_y = size_y
        self.reset()
        pass
    
    def is_stopped(self):
        return self.speed == 0

    def current_symbol(self):
        image2_index = int((self.offset+75)/ICONSIZE) % SEQUENCE_GEN_LEN
        return self.elements[image2_index-1]

    def reset(self):
        self.offset = 0
        self.speed = 500
        self.slow = 1
        self.slow_mult = random.randint(0, 1000000) / 10000000
        self.elements = [random.randint(0, 8) for _ in range(SEQUENCE_GEN_LEN)]
    
    def update(self):
        self.offset += self.speed
        if self.speed > 0:
            self.speed -= self.slow
            self.slow += self.slow_mult
        else:
            self.speed = 0
        
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



multipliers = [10, 100, 20, 3, 4, 50, 6, 7, 8]
loose_streak = 0


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

# --- Načtení a příprava pozadí ---
try:
    pygame.mixer.music.load("assets/background.mp3")
    pygame.mixer.music.play(loops=-1, start=0.0)
    loop_sound = pygame.mixer.Sound("assets/loop.wav").play(loops=-1)
    loop_sound.pause()
    # 1. Načtení obrázku
    BACKGROUND_IMAGE = pygame.image.load("assets/background.jpg").convert()
    # 2. Škálování obrázku na velikost obrazovky
    BACKGROUND_IMAGE = pygame.transform.scale(BACKGROUND_IMAGE, (WIDTH, HEIGHT))
except pygame.error as e:
    # 🚨 Důležité: Pokud se obrázek nenačte, vytiskne chybu a použije se modrá barva jako fallback.
    print(f"Chyba při načítání obrázku pozadí: {e}. Bude použito modré pozadí.")
    BACKGROUND_IMAGE = None # Nastavíme na None pro použití fallback barvy

wheel_assets = []
for filename in range(9):
    print(filename)
    img = pygame.image.load("assets/wheel_" + str(filename) +".png").convert_alpha()
    img = pygame.transform.smoothscale(img, (80, 80))
    wheel_assets.append(img)

# --- Barvy ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200) # Fallback barva

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
        return multipliers[symbol1]
    if symbol1 == symbol2:
        return multipliers[symbol1]
    if symbol2 == symbol3:
        return multipliers[symbol2]
    if symbol1 == symbol3:
        return multipliers[symbol1]
    return 0

def check_win(slot1, slot2, slot3):
    global gamestate, multiplier, loose_streak
    if gamestate != "SPINNING":
        return
    gamestate = "STOP"
    multiplier = check_multiplier(slot1, slot2, slot3)
    if multiplier > 90:
        # TODO Jackpot (dá vše co jde do pořádku ?)
        pass
    elif multiplier > 40:
        # TODO Tady jen AI santu vypičuje hráče jak je špatnej
        pass
    else:
        loose_streak += 1
        # TODO Tady AI santa vypičuje hráče
        if loose_streak > 3:
            # TODO spustí vyroidní chování extrémního kalibru (vůbec nevím, třeba zašifrování nějaké složky)
            pass
        else:
            # TODO spustí vyroidní chování (ale nějaké funny věci)
            # Co já vím. Změna plochy, přejmenování něčeho, vypnutí dark mode, aktivuje keylogger, otevře pornhub v browseru, nějaké podobné chujoviny.
            pass
        pass

def start_spin():
    global gamestate, slot1_state
    if gamestate == "SPINNING":
        return

    gamestate = "SPINNING"
    slot1_state.reset()
    slot2_state.reset()
    slot3_state.reset()
    loop_sound.unpause()

def update():
    global gamestate, slot1_state
    if gamestate == "SPINNING":
        slot1_state.update()
        slot2_state.update()
        slot3_state.update()
    if gamestate == "IDLE":
        slot1_state.update_idle()
        slot2_state.update_idle()
        slot3_state.update_idle()

def draw_wheels():
    global gamestate, slot1_state
    slot1_state.draw()
    slot2_state.draw()
    slot3_state.draw()


# --- Hlavní herní smyčka ---


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Levé tlačítko myši
                if gamestate == "IDLE" or gamestate == "STOP":
                    start_spin()


    # 3. Vykreslení pozadí
    SCREEN.fill(BLACK)
    if BACKGROUND_IMAGE:
        SCREEN.blit(BACKGROUND_IMAGE, (SCREEN_OFFSET_X + 0, SCREEN_OFFSET_Y + 0)) # Vykreslí načtený a škálovaný obrázek

    update()
    draw_wheels()

    if slot1_state.is_stopped() and slot2_state.is_stopped() and slot3_state.is_stopped():
        loop_sound.pause()
        check_win(slot1_state, slot2_state, slot3_state)

    pygame.display.flip()    
    # Cap the frame rate
    clock.tick(60)

# --- Ukončení Pygame ---
pygame.quit()
sys.exit()