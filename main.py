# river_race.py — smaller hitboxes (mask shrink), start screen, 3 lives, 17s speed-up
import os, random, math, pygame


WIDTH, HEIGHT = 480, 720
FPS = 60
TITLE = "River Mage: Shrimp Run"


PLAYER_SPEED = 6
SCROLL_SPEED = 1.6
BASE_OBJECT_SPEED = 4
MAX_OBJECT_SPEED = 10
SPEED_STEP = 1.0
SPEED_STEP_INTERVAL_MS = 17_000  

SPAWN_NET_MS = 1150
SPAWN_SHRIMP_MS = 1400

START_LIVES = 3
HIT_COOLDOWN_MS = 800

MAX_BOAT_W, MAX_BOAT_H   = 100, 100
MAX_NET_W,  MAX_NET_H    = 120, 140
MAX_SHRIMP_W, MAX_SHRIMP_H = 64, 64

ASSETS_DIR = "assets"
IMG_WATER    = os.path.join(ASSETS_DIR, "water.png")
IMG_BOAT     = os.path.join(ASSETS_DIR, "boat.png")
IMG_MAGE     = os.path.join(ASSETS_DIR, "mage.png")
IMG_BOATMAGE = os.path.join(ASSETS_DIR, "boat_mage.png")
IMG_NET      = os.path.join(ASSETS_DIR, "net.png")
IMG_SHRIMP   = os.path.join(ASSETS_DIR, "shrimp.png")

pygame.init()
pygame.display.set_caption(TITLE)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

font = pygame.font.Font(None, 26)
big_font = pygame.font.Font(None, 48)


def try_load(p): return os.path.exists(p)
def load_image(p): return pygame.image.load(p).convert_alpha()

def set_white_colorkey(surf):
    surf.set_colorkey((255, 255, 255));  return surf

def scale_to_fit(surf, max_w, max_h):
    w, h = surf.get_size()
    if w <= max_w and h <= max_h: return surf
    k = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(surf, (max(1,int(w*k)), max(1,int(h*k))))

def safe_load_fit(path, fallback, max_w, max_h, white_transparent=False):
    surf = fallback
    if try_load(path):
        try:
            surf = load_image(path)
            if white_transparent: set_white_colorkey(surf)
        except Exception:
            pass
    return scale_to_fit(surf, max_w, max_h)

def spawn_x_for_width(rect_w, margin=20):
    avail = WIDTH - 2*margin - rect_w
    if avail <= 0: return (WIDTH - rect_w)//2
    return margin + random.randint(0, avail)

def make_shrunken_mask(surface, shrink_px: int):
    """
    Уменьшаем маску по периметру на shrink_px пикселей:
    1) создаём обычную маску
    2) скейлим её в меньший размер
    3) рисуем обратно по центру в маску исходного размера
    """
    base = pygame.mask.from_surface(surface)
    w, h = base.get_size()
    new_w = max(1, w - 2*shrink_px)
    new_h = max(1, h - 2*shrink_px)
    small = base.scale((new_w, new_h))
    result = pygame.Mask((w, h))
    result.clear()
    result.draw(small, (shrink_px, shrink_px))
    return result


def draw_procedural_water(size):
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    base = pygame.Surface((w, h)); base.fill((22,110,185))
    for y in range(0, h, 6):
        for x in range(0, w, 8):
            a = 30 + 25*math.sin((x*0.08)+(y*0.06))
            c = (20, int(120 + a/2), int(200 + a/3))
            pygame.draw.rect(base, c, (x, y, 8, 6))
    surf.blit(base, (0,0))
    for _ in range(100):
        rx, ry = random.randint(0,w), random.randint(0,h)
        pygame.draw.circle(surf, (230,250,255, random.randint(25,45)), (rx,ry), random.randint(6,14), 1)
    return surf

def draw_boat_placeholder(size=(84,84)):
    s = pygame.Surface(size, pygame.SRCALPHA); w,h=size
    hull = [(w*0.5,0),(w*0.95,h*0.45),(w*0.5,h*0.95),(w*0.05,h*0.45)]
    pygame.draw.polygon(s,(168,115,72),hull); pygame.draw.polygon(s,(90,60,38),hull,3)
    return s

def draw_mage_placeholder(size=(44,44)):
    s = pygame.Surface(size, pygame.SRCALPHA); w,h=size
    pygame.draw.ellipse(s,(80,60,160),(w*0.1,h*0.35,w*0.8,h*0.6))
    pygame.draw.circle(s,(245,220,180),(int(w*0.5),int(h*0.28)),int(h*0.18))
    pygame.draw.polygon(s,(200,40,40),[(w*0.5,h*0.02),(w*0.8,h*0.36),(w*0.2,h*0.36)])
    pygame.draw.ellipse(s,(200,40,40),(w*0.2,h*0.32,w*0.6,h*0.12))
    return s

def compose_boat_with_mage(boat, mage):
    s = boat.copy(); bw,bh = s.get_size()
    m_w = int(bw*0.45); k = m_w/mage.get_width()
    m = pygame.transform.smoothscale(mage, (m_w, int(mage.get_height()*k)))
    s.blit(m, (int(bw*0.5-m.get_width()/2), int(bh*0.48-m.get_height()/2)))
    return s

def draw_net_placeholder(size=(78,90)):
    s = pygame.Surface(size, pygame.SRCALPHA); w,h=size
    pygame.draw.rect(s,(160,120,60,255),(3,3,w-6,h-6), border_radius=12, width=5)
    for i in range(6):
        fx = int((i+0.5)*w/6); pygame.draw.circle(s,(230,200,120),(fx,10),6)
    mesh=(210,210,210,170); step=12
    for y in range(10,h-10,step):
        for x in range(10,w-10,step):
            pygame.draw.line(s,mesh,(x-step//2,y),(x,y+step//2),1)
            pygame.draw.line(s,mesh,(x,y+step//2),(x+step//2,y),1)
            pygame.draw.line(s,mesh,(x-step//2,y),(x,y-step//2),1)
            pygame.draw.line(s,mesh,(x,y-step//2),(x+step//2,y),1)
    return s

def draw_shrimp_placeholder(size=(40,26)):
    s = pygame.Surface(size, pygame.SRCALPHA); w,h=size
    pygame.draw.ellipse(s,(255,140,100),(0,2,int(w*0.7),h-4))
    pygame.draw.ellipse(s,(255,120,90),(int(w*0.55),4,int(w*0.25),h-8))
    pygame.draw.polygon(s,(255,110,85),[(int(w*0.8),h//2),(w,0),(w,h)])
    pygame.draw.circle(s,(20,20,20),(int(w*0.18),int(h*0.38)),2)
    return s


if try_load(IMG_WATER):
    try:
        water_img = load_image(IMG_WATER)
        water_img = pygame.transform.smoothscale(water_img, (WIDTH, HEIGHT))
    except Exception:
        water_img = draw_procedural_water((WIDTH, HEIGHT))
else:
    water_img = draw_procedural_water((WIDTH, HEIGHT))


if try_load(IMG_BOATMAGE):
    bm = load_image(IMG_BOATMAGE)
    set_white_colorkey(bm)
    boat_mage_img = scale_to_fit(bm, MAX_BOAT_W, MAX_BOAT_H)
elif try_load(IMG_BOAT) and try_load(IMG_MAGE):
    boat_img = safe_load_fit(IMG_BOAT, draw_boat_placeholder(), MAX_BOAT_W, MAX_BOAT_H, True)
    mage_img = safe_load_fit(IMG_MAGE, draw_mage_placeholder(), MAX_BOAT_W//2, MAX_BOAT_H//2, True)
    boat_mage_img = compose_boat_with_mage(boat_img, mage_img)
else:
    boat_mage_img = scale_to_fit(compose_boat_with_mage(draw_boat_placeholder(), draw_mage_placeholder()),
                                 MAX_BOAT_W, MAX_BOAT_H)


net_img    = safe_load_fit(IMG_NET,    draw_net_placeholder(),    MAX_NET_W,    MAX_NET_H, True)
shrimp_img = safe_load_fit(IMG_SHRIMP, draw_shrimp_placeholder(), MAX_SHRIMP_W, MAX_SHRIMP_H, True)

water_y1, water_y2 = 0, -HEIGHT


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = boat_mage_img
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT-40))
        self.speed = PLAYER_SPEED
        self.mask = make_shrunken_mask(self.image, shrink_px=10)  

    def update(self, keys):
        dx=dy=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:    dy -= self.speed*0.6
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  dy += self.speed*0.6
        self.rect.x += dx; self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(12, 60, WIDTH-24, HEIGHT-80))

class Net(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.image = net_img
        self.rect = self.image.get_rect()
        self.rect.x = spawn_x_for_width(self.rect.width, margin=20)
        self.rect.y = -self.rect.height - 10
        self.speed = speed
        self.mask = make_shrunken_mask(self.image, shrink_px=4)   

    def update(self):
        self.rect.y += int(self.speed)
        if self.rect.top > HEIGHT + 40: self.kill()

class Shrimp(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.image = shrimp_img
        self.rect = self.image.get_rect()
        self.rect.x = spawn_x_for_width(self.rect.width, margin=20)
        self.rect.y = -self.rect.height - 10
        self.speed = speed * 0.9
        self.mask = pygame.mask.from_surface(self.image)  

    def update(self):
        self.rect.y += int(self.speed)
        if self.rect.top > HEIGHT + 40: self.kill()


all_sprites = pygame.sprite.Group()
nets = pygame.sprite.Group()
shrimps = pygame.sprite.Group()
player = Player(); all_sprites.add(player)

SPAWN_NET = pygame.USEREVENT + 1
SPAWN_SHRIMP = pygame.USEREVENT + 2
pygame.time.set_timer(SPAWN_NET, SPAWN_NET_MS)
pygame.time.set_timer(SPAWN_SHRIMP, SPAWN_SHRIMP_MS)

running=True
game_started=False
game_over=False
score=0
lives=START_LIVES
object_speed=BASE_OBJECT_SPEED
last_hit_time=-HIT_COOLDOWN_MS
game_start_time=pygame.time.get_ticks()
next_speedup_time=game_start_time+SPEED_STEP_INTERVAL_MS

def reset_game():
    global all_sprites,nets,shrimps,player,game_over,score,lives,object_speed,last_hit_time,game_start_time,next_speedup_time,water_y1,water_y2
    all_sprites.empty(); nets.empty(); shrimps.empty()
    player=Player(); all_sprites.add(player)
    game_over=False; score=0; lives=START_LIVES
    object_speed=BASE_OBJECT_SPEED
    last_hit_time=-HIT_COOLDOWN_MS
    game_start_time=pygame.time.get_ticks()
    next_speedup_time=game_start_time+SPEED_STEP_INTERVAL_MS
    water_y1, water_y2 = 0, -HEIGHT


while running:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if not game_started:
            if event.type==pygame.KEYDOWN and event.key==pygame.K_RETURN:
                game_started=True; reset_game()
        elif not game_over:
            if event.type==SPAWN_NET:
                n=Net(object_speed); nets.add(n); all_sprites.add(n)
            if event.type==SPAWN_SHRIMP:
                s=Shrimp(object_speed); shrimps.add(s); all_sprites.add(s)
        else:
            if event.type==pygame.KEYDOWN and event.key==pygame.K_r:
                reset_game(); game_over=False

    keys = pygame.key.get_pressed()
    
    if game_started and not game_over:
        water_y1 += SCROLL_SPEED; water_y2 += SCROLL_SPEED
        if water_y1 >= HEIGHT: water_y1 = water_y2 - HEIGHT
        if water_y2 >= HEIGHT: water_y2 = water_y1 - HEIGHT

    
    if game_started and not game_over:
        player.update(keys); nets.update(); shrimps.update()

       
        if now >= next_speedup_time:
            object_speed = min(MAX_OBJECT_SPEED, object_speed + SPEED_STEP)
            next_speedup_time += SPEED_STEP_INTERVAL_MS

        
        caught = pygame.sprite.spritecollide(player, shrimps, dokill=True, collided=pygame.sprite.collide_mask)
        if caught: score += len(caught)

      
        if now - last_hit_time >= HIT_COOLDOWN_MS:
            hit_nets = pygame.sprite.spritecollide(player, nets, dokill=False, collided=pygame.sprite.collide_mask)
            if hit_nets:
                lives -= 1; last_hit_time = now
                for n in list(nets): n.kill()
                if lives <= 0: game_over = True

   
    screen.blit(water_img, (0, water_y1)); screen.blit(water_img, (0, water_y2))
    all_sprites.draw(screen)

    if not game_started:
        title = big_font.render("River Mage: Shrimp Run", True, (255,255,255))
        i1 = font.render("Move: Arrow keys / WASD", True, (240,240,240))
        i2 = font.render("Collect shrimps (+1)", True, (240,240,240))
        i3 = font.render("Avoid fishing nets", True, (240,240,240))
        i4 = font.render("Press ENTER to start", True, (255,220,120))
        for surf, dy in [(title,-60),(i1,0),(i2,30),(i3,60),(i4,120)]:
            screen.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2 + dy)))
    elif not game_over:
        screen.blit(font.render(f"Shrimps: {score}", True, (255,255,255)), (12,10))
        screen.blit(font.render(f"Speed: {object_speed:.1f}", True, (230,230,230)), (12,36))
        screen.blit(font.render(f"Lives: {lives}", True, (255,230,230)), (12,62))
        if now - last_hit_time < HIT_COOLDOWN_MS:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((255,60,60,60)); screen.blit(shade, (0,0))
    else:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); shade.fill((0,0,0,140))
        screen.blit(shade, (0,0))
        over1 = big_font.render("Game Over", True, (255,230,230))
        over2 = font.render(f"Shrimps collected: {score}", True, (255,230,230))
        over3 = font.render("Press R to play again", True, (255,230,230))
        for surf, dy in [(over1,-24),(over2,6),(over3,36)]:
            screen.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2 + dy)))

    pygame.display.flip()

pygame.quit()