# TODO: make the jumping frame based movement
import sys
import pygame
from pygame.locals import *
import os
vec = pygame.math.Vector2
from hammer import Enemy, DynamicAnimation
from utils import *
from jump_particles import Effect

pygame.init()

fps = 60
fpsClock = pygame.time.Clock()
cont = 0
width, height = 1024, 768
screen = pygame.display.set_mode((width, height))

def draw_grid():
    for y in range(0,height,TILESIZE):
        pygame.draw.line(screen,'red',(0,y),(width,y))
    for x in range(0,width,TILESIZE):
        pygame.draw.line(screen,'red',(x,0),(x,height))

def import_animations(path):
    all_animations = {}
    size = 32
    for _,__,image_files in os.walk(path):
        for image in image_files:
            animations = []
            surface = pygame.image.load(os.path.join(path,image)).convert_alpha()
            tile_num_x = int(surface.get_width() / 32)
            for col in range(tile_num_x):
                x = col*32
                new_surf = pygame.Surface((size,size),flags = pygame.SRCALPHA)
                new_surf.blit(surface,(0,0),pygame.Rect(x,0,32,32))
                animations.append(new_surf)
            all_animations[image[:-4]] = animations # [:-4] quitar el .png

    return all_animations

class Player(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.animations = import_animations('Ninja Frog')
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect(topleft=(x,y))
        self.pos = vec(self.rect.topleft)
        self.speed = .8
        
        self.gravity = .9
        self.initial_jump = -16
        self.on_ground = True
        self.friction = -.16
        self.status = 'idle'
        self.velocity = vec(0,0)
        self.acceleration = vec(0,self.gravity)
        self.frame_index = 0
        self.animation_speed = 0.2
        self.facing_right = True
        self.jump_key = False # quiero que al mantener pulsada la tecla del salto no se mantenga saltando
        self.collision_rect = pygame.Rect(self.rect.center-vec(8,10),(16,21)) # hay algunas animaciones donde este rectangulo esta lejos de encajar bien
        self.bounce_duration = 0
        self.bouncing = False
        self.bounce = False
        self.bounce_key = False
        self.wall_jump = False
        self.bounce_right = False
        self.bounce_left = False
        self.right_pressed = False
        self.left_pressed = False
        self.collision_type = {'horizontal':False,'vertical':False} 

    def animate(self):
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0
        self.image = animation[int(self.frame_index)]
        if self.facing_right:
            self.rect.topleft = self.collision_rect.topleft-vec(8,10)
        else:
            self.image = pygame.transform.flip(self.image,True,False)
            self.rect.topleft = self.collision_rect.topleft-vec(8,10)
        # por defecto, pygame dibuja el rectángulo en topleft, en este caso no importa y no habría que actualizar la posicion

    def horizontal_movement(self):
        if self.collision_rect.x <= 0:
            self.collision_rect.x = 0
            self.pos.x = self.collision_rect.x
        if self.collision_rect.right >= width:
            self.collision_rect.right = width
            self.pos.x = self.collision_rect.x

        #ramp_rect = self.ramps.sprite
        # if self.rect.colliderect(ramp_rect):
        #     if self.old_rect.right-1 <= ramp_rect.left: # a veces si pulso flecha derecha varias veces o la mantengo pulsada, estando pegado a la pared izquierda, al saltar me sube al punto superior del triángulo, y yo creo que este es un comportamiento normal al pulsar
        #         self.rect.right = ramp_rect.left
        #         self.pos.x = self.rect.x
        #     else:
        #         m = ramp_rect.height / ramp_rect.width
        #         top = ramp_rect.bottom - (ramp_rect.right - max(self.rect.left, ramp_rect.left)) * m # si estamos en la cima de la rampa
        #         #print(self.rect.bottom,top)
        #         if  self.on_ground or self.rect.bottom > top: # si el jugadfor está saltando encima dela rampa la condición self.rect.bottom > top sera falsa
        #             self.rect.bottom = top
        #             self.pos.y = self.rect.y
        #             self.velocity.y = 0
        #             self.on_ground = True

    def move(self):
        keys = pygame.key.get_pressed()
        # print(self.acceleration,self.velocity)
        # FIXME: cuidado con las animacines        
        self.acceleration.x = 0
        if not self.bouncing:
            self.status = 'run'
            if keys[K_RIGHT]:
                self.acceleration.x = self.speed
                self.facing_right = True
            elif keys[K_LEFT]:
                self.acceleration.x = -self.speed 
                self.facing_right = False
            else:
                self.status = 'idle'
            if self.on_ground and self.jump_key:
                self.velocity.y = self.initial_jump
                self.jump_key = False
        else:
            if keys[K_RIGHT]:
                self.right_pressed = True
                self.left_pressed = False
            elif keys[K_LEFT]:
                self.left_pressed = True
                self.right_pressed = False
        if not self.on_ground:
            if self.wall_jump: # si hay una colision con alguna pared horizontalmente y estamos cayendo 'fall', el jugador al caer sigue con la animacion de wall jump
                self.status = 'wall_jump'
            elif self.velocity.y < 0:
                self.status = 'jump'
            elif self.velocity.y > 1:
                self.status = 'fall'
    
    def apply_gravity(self, dt):
        self.velocity.y += self.acceleration.y * dt
        self.pos.y += self.velocity.y * dt + (self.acceleration.y * .5) * dt**2
        self.collision_rect.y = round(self.pos.y)

    def update(self):
        #print(self.status)
        self.move()        
        self.horizontal_movement()
        self.animate()
        
TILESIZE = 32

def load_map(file):
    f = ''
    with open(file) as f:
        f = f.readlines()
    return f
    
class Obstacle(pygame.sprite.Sprite):
    def __init__(self,pos,width,height,color):
        super().__init__()
        self.image = pygame.Surface((width,height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=pos)

    def update(self):
        pass
    
    # ___| <- P si el jugador va hacia la izquierda y la pared de la rampa está a la derecha tenemos que hacer colisión, si la pared estuviera a la izquierda no
    # P -> |___ si el jugador va hacia la derecha y la pared está a la izquierda, colisión, si está a la derecha nada
class Ramp(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, wall):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.wall = wall
        #self.image.fill('green')
        pygame.draw.polygon(self.image, color,
                            points=[(0, 0), (0, height), (width, height)])
        self.rect = self.image.get_rect(bottomleft=(x, y))


class Ramp2(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, wall):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.wall = wall
        #self.image.fill('green')
        pygame.draw.polygon(self.image, color,
                            points=[(0, height),(width,height),(width,0)])
        self.rect = self.image.get_rect(bottomleft=(x, y))

class Game:
    def __init__(self):
        self.player_sprite = pygame.sprite.GroupSingle()
        self.particles = list()
        self.wall_jump_effects = pygame.sprite.Group()

        self.obstacles =  pygame.sprite.Group()
        self.ramps = pygame.sprite.Group()
        # 
        self.ramps.add(Ramp(TILESIZE,20*TILESIZE,6*TILESIZE,3*TILESIZE,'red','left'))
        self.ramps.add(Ramp2(TILESIZE*17,21*TILESIZE,6*TILESIZE,TILESIZE*6,'red','left'))
        tiles_map = load_map("map.txt")
        self.hammer_enemy = pygame.sprite.GroupSingle()
        self.player_hitted = pygame.sprite.GroupSingle()
        for row,line in enumerate(tiles_map):
            for col, char in enumerate(line):
                if char == "1":
                    self.obstacles.add(Obstacle((col*TILESIZE,row*TILESIZE),TILESIZE,TILESIZE,'black'))
                elif char == "P":
                    print(col*TILESIZE,row*TILESIZE)
                    self.player_sprite.add(Player(col*TILESIZE,row*TILESIZE))
                elif char == "E":
                    self.hammer_enemy.add(Enemy((col*TILESIZE,row*TILESIZE+TILESIZE))) # el enemigo midbottom porque las imagenes no tienen todas la misma altura
        self.hammer_enemy.sprite.player = self.player_sprite.sprite
        self.obstacles.add(self.ramps) # para las colisiones horizontales, las verticales no funcionan todavía...

    def horizontal_movement(self, dt):
        player = self.player_sprite.sprite
        if player.bounce:
            if player.bounce_right:
                player.acceleration.x = -player.speed
            if player.bounce_left:
                player.acceleration.x = player.speed
            if pygame.time.get_ticks()-player.bounce_duration > 360: # hay que ajustar el tiempo de manera que no rebote durante demasiado tiempo, sino si estamos rebotando puede haber colisiones si el rebote dura demasiado y no hace falta pulsar las flechas para que haya colision
                player.velocity.y =0   
                player.bounce = False
                
        if player.on_ground and player.bouncing:
            if player.bounce_right:
                player.bounce_right = False
            if player.bounce_left:
                player.bounce_left = False
            player.bouncing = False
            player.velocity.x = 0
        # ecuaciones del movimiento
        #print(player.acceleration,player.velocity)
        player.acceleration.x += player.velocity.x * player.friction
        player.velocity.x += player.acceleration.x * dt
        player.pos.x += player.velocity.x * dt + 0.5 * player.acceleration.x * dt **2
        player.collision_rect.x = round(player.pos.x)
        player.collision_type['horizontal'] = False
        for obstacle in self.obstacles.sprites():
            if obstacle.rect.colliderect(player.collision_rect):                
                # if player.velocity.y and player.velocity.y > -10:                    
                #     player.status = 'wall_jump'
                #     player.wall_jump = True
                if isinstance(obstacle,Ramp):
                    ramp_rect = obstacle.rect
                    if player.collision_rect.right-5 > ramp_rect.left: # FIXME ese 5 mágico...
                        continue
                if isinstance(obstacle,Ramp2):
                    ramp_rect = obstacle.rect
                    if player.collision_rect.left+5 < ramp_rect.right: # FIXME ese 5 mágico...
                        continue
                player.collision_type['horizontal'] = True
                if player.velocity.x < 0:
                    if player.velocity.y and player.velocity.y > -10:                    
                        player.status = 'wall_jump'
                        player.wall_jump = True
                        #player.velocity.x =0 # FIXME
                    player.collision_rect.left = obstacle.rect.right
                    player.pos.x = player.collision_rect.x
                    if player.status == 'wall_jump':
                        if player.left_pressed and player.bounce_right and player.bouncing:
                            #print(cont,". ","rebota otra vez derecha")
                            #print(cont,". ",player.right_pressed,player.left_pressed)
                            player.bounce_right = False
                            ############################
                            player.facing_right = False
                            player.bouncing = False
                            player.wall_jump = False
                            player.status = 'jump'
                        if player.bounce_key and not player.bouncing  and not player.bounce:
                            #print(cont,". ","pared izquierda")
                            #self.particles.append(MissileExplosion(player.rect.bottomleft))
                            player.bounce_left =   True
                            ############################
                            player.wall_jump = False
                            player.bounce_key = False
                            player.velocity.x =0
                            player.velocity.y = -15
                            player.status = 'jump'
                            player.bounce = True
                            player.bouncing = True
                            player.facing_right = True
                            player.bounce_duration = pygame.time.get_ticks()
                    
                if player.velocity.x > 0:
                    if player.velocity.y and player.velocity.y > -10:                    
                        player.status = 'wall_jump'
                        #player.velocity.x =0 # FIXME
                        player.wall_jump = True
                        #player.velocity.x = 0
                    player.collision_rect.right = obstacle.rect.left
                    player.pos.x = player.collision_rect.x
                    if player.status == 'wall_jump':
                        if player.right_pressed and player.bounce_left and player.bouncing:
                            #print(cont,". ","rebota otra vez izquierda")
                            
                            #print(cont,". ",player.right_pressed,player.left_pressed)
                            player.bounce_left = False
                            ############################
                            player.facing_right = True
                            player.bouncing = False
                            player.wall_jump = False
                            player.status = 'jump'
                        if player.bounce_key and not player.bouncing and not player.bounce:
                            #print(cont,". ","pared derecha")
                            #self.particles.append(MissileExplosion(player.rect.bottomright))
                            print(player.rect.bottomright)
                            player.bounce_right =   True
                            player.velocity.x =0
                            ############################
                            player.wall_jump = False
                            player.bounce_key = False
                            player.velocity.y = -15
                            player.status = 'jump'
                            player.bounce = True
                            player.bouncing = True
                            player.facing_right = False
                            player.bounce_duration = pygame.time.get_ticks() 

        if player.wall_jump and not player.collision_type['horizontal']:
            player.wall_jump = False
            player.velocity.x =0
            
    def vertical_movement(self, dt):
        player = self.player_sprite.sprite
        #print("dt: ",self.dt)
        
        player.apply_gravity(dt)
        
        for obstacle in self.obstacles.sprites():
            if obstacle.rect.colliderect(player.collision_rect):
                if isinstance(obstacle,Ramp) or isinstance(obstacle,Ramp2):
                    continue
                if player.velocity.y > 0: 
                    player.collision_rect.bottom = obstacle.rect.top
                    
                    player.pos.y = player.collision_rect.y
                    player.velocity.y = 0
                    player.wall_jump = False
                    player.on_ground = True
                    
                if player.velocity.y < 0:
                    player.collision_rect.top = obstacle.rect.bottom
                    player.velocity.y = 0
                    player.pos.y = player.collision_rect.y
        if player.status == 'fall' and player.on_ground:
            self.particles.append(Effect(player.collision_rect.midbottom))
        if player.on_ground and player.velocity.y: # si lo tengo en player como antes, puedo saltar en el aire entre los dos rectángulos altos
            player.on_ground = False
    
    # FIXME: probar dibujando el triángulo al revés
    def vertical_ramp_collision(self):
        player = self.player_sprite.sprite
        
        for ramp in self.ramps.sprites():
            ramp_rect = ramp.rect
            #pygame.draw.rect(screen,'green',ramp_rect,1)
            if player.collision_rect.colliderect(ramp_rect):
                #print("on the ramp")
                if isinstance(ramp,Ramp):
                    ratio = ramp_rect.height / ramp_rect.width
                    bottom = ramp_rect.bottom - (ramp_rect.right - max(player.collision_rect.left, ramp_rect.left)) * ratio
                    if player.on_ground or player.collision_rect.bottom > bottom-5:
                        player.collision_rect.bottom = bottom
                        player.pos.y = player.collision_rect.y
                        player.velocity.y = 0
                        player.on_ground = True
                if isinstance(ramp,Ramp2):
                    ratio = ramp_rect.height / ramp_rect.width * -1
                    bottom = ramp_rect.bottom - (ramp_rect.left - min(player.collision_rect.right, ramp_rect.right)) * ratio
                    if player.on_ground or player.collision_rect.bottom > bottom-5:
                        player.collision_rect.bottom = bottom
                        player.pos.y = player.collision_rect.y
                        player.velocity.y = 0
                        player.on_ground = True
                       
    def collisions(self):
        for hammer in self.hammer_enemy.sprite.hammer.sprites():
            if self.player_sprite.sprite.rect.colliderect(hammer):
                self.player_hitted.add(DynamicAnimation(self.player_sprite.sprite.collision_rect.midtop-vec(0,20),500))
                hammer.kill()

    def update(self, dt):
        self.dt = dt

        self.horizontal_movement(dt)
        
        self.vertical_movement(dt)
        self.vertical_ramp_collision()
        
        #pygame.draw.rect(screen,'green',self.ramps.sprites()[0].rect,2)
        #self.ramp_collision()
             
        self.player_sprite.update()
        if self.player_hitted.sprite:
            self.player_hitted.sprite.rect.midtop = self.player_sprite.sprite.collision_rect.midtop-vec(0,20)
        #pygame.draw.rect(screen,'red',player.collision_rect)
        #print(self.player_sprite.sprite.status)
        
        #draw_grid()
        self.collisions()
        
    def draw(self):
        
        self.obstacles.draw(screen)
        self.ramps.draw(screen)
        self.hammer_enemy.update()
        self.hammer_enemy.draw(screen)
        self.player_sprite.draw(screen)
        self.player_hitted.update()
        self.player_hitted.draw(screen)
        self.wall_jump_effects.update()
        self.wall_jump_effects.draw(screen)
        for part in self.particles:
            part.update()
        

game = Game()


# no permitir saltar varias veces
cont = 0
while True:
    
    dt = fpsClock.tick(60) /1000 * fps
    dt = min(dt,1.5) # see https://stackoverflow.com/questions/70555914/player-dissapear-when-the-window-is-held
    
    player = game.player_sprite.sprite
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()    
        if event.type == KEYDOWN:
            if event.key == K_UP:
                player.jump_key = True
            if event.key == K_d:
                player.bounce_key = True
        if event.type == MOUSEBUTTONDOWN:
            game.particles.append(Effect(pygame.mouse.get_pos()))
        if event.type == KEYUP:
            if event.key == K_UP:
                player.jump_key = False
            if event.key == K_d:
                player.bounce_key = False
    
    cont += 1
    screen.fill('lightblue')    
    game.update(dt)
    
    game.draw()
    debug(str(pygame.mouse.get_pos()))
    # pygame.draw.rect(screen,'red',player.rect,2)
    # pygame.draw.rect(screen,'blue',player.collision_rect,2)
    
    pygame.display.update()
    
    