from asyncio import start_server
import sys

import pygame
from pygame.locals import *
from utils import *
from random import *
from math import *

pygame.init()

fps = 60
fpsClock = pygame.time.Clock()

width, height = 1500, 900
screen = pygame.display.set_mode((width, height))

class Head(pygame.sprite.Sprite):
    def __init__(self, pos,angle, left):
        super().__init__()
        self.left = left
        self.image = load_image('enemy/head.png') #hammer_resized-removebg.png
        self.rect = self.image.get_rect(midbottom=pos)
        self.acc = vec(0,0)
        self.pos = vec(pos)
        self.gravity = -0.08
        self.vel = vec(3,4)
        if self.left:
            self.vel.x *= -1
        else:
            self.image = pygame.transform.flip(self.image,True,False)
        self.angle = radians(angle)
        self.copy_img = self.image.copy()
        self.rotation = -60
        self.surf = pygame.Surface((100,100))
        self.surf.fill('red')
        self.mask = pygame.mask.from_surface(self.image )
        self.orig_pos = vec(self.rect.midbottom)
    
    def fixed_rotation(self, originPos, angle):
        pos = vec(self.orig_pos) # por vagancia
        image_rect = self.copy_img.get_rect(topleft = vec(pos.x-originPos[0],pos.y-originPos[1]))
        offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
        
        # roatated offset from pivot to center
        rotated_offset = offset_center_to_pivot.rotate(-angle)

        # roatetd image center
        rotated_image_center = (pos.x - rotated_offset.x, self.pos.y - rotated_offset.y)

        # get a rotated image
        self.image = pygame.transform.rotozoom(self.copy_img, angle,1)
        self.rect = self.image.get_rect(center = rotated_image_center)
        self.mask = pygame.mask.from_surface(self.image)
    
    def rotate_manual(self, rot):
        if self.left:
            self.image = pygame.transform.rotozoom(self.copy_img,rot,1)
        else:
            self.image = pygame.transform.rotozoom(self.copy_img,-rot,1)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)
    
class Handle(Head):
    def __init__(self, pos, angle, left):
        super().__init__(pos,angle,left)
        self.image = load_image('enemy/handle.png')
        self.rect = self.image.get_rect(midbottom=pos)
        if self.left:
            self.vel.x *= -1
        else:
            self.image = pygame.transform.flip(self.image,True,False)
        self.copy_img = self.image.copy()
        self.mask = pygame.mask.from_surface(self.image )
        self.orig_pos = vec(self.rect.midbottom)

class DynamicAnimation(pygame.sprite.Sprite):
    # if duration is zero, the animation continues until we call kill()
    def __init__(self,pos,duration=0):
        super().__init__()
        self.frame_index = 0
        self.animation_speed = 0.2
        self.frames = load_folder_images('effects/stars')
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(midbottom=pos)
        self.duration = duration
        self.start_time = 0
    
    def animate(self):
        if not self.start_time:
            self.start_time = pygame.time.get_ticks()
        if self.duration:
            if pygame.time.get_ticks()-self.start_time > self.duration:
                self.kill()
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self):
        self.animate()

# que se complete la animacion...
class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos) -> None:
        super().__init__()
        self.animations = import_animations_from_folders('enemy/hammer bro')
        
        for animations in self.animations.values():
            for ani in animations:
                ani.set_colorkey((77,109,243))
        images = self.animations['turning around']
        self.animations['turning around reversed'] = images[::-1]
        self.image = self.animations['throwing'][0]
        self.rect = self.image.get_rect(midbottom=pos)
        self.ani_ind = 0
        self.hammer = pygame.sprite.Group()
        self.can_launch = False
        self.face_left = True
        self.status = 'throwing'
        self.vx = -1
        self.accu = 0
        self.player = None
        # cada x tiempo que se mueva un poco, esto implica gravedad y colisiones como el jugador
        self.start_time = 0
        self.duration = 1500

    def animate(self):
        if int(self.ani_ind) >= len(self.animations[self.status]):
            if self.status == 'turning around' or self.status == 'turning around reversed':
                self.status = 'throwing'
            self.ani_ind = 0

        self.image = self.animations[self.status][int(self.ani_ind)]
        self.rect = self.image.get_rect(midbottom=self.rect.midbottom) # al ser las imagenes de distinta altura...
        self.ani_ind += 0.4
        if not self.face_left and self.status == 'throwing':
            self.image = pygame.transform.flip(self.image,True,False)
            self.image.set_colorkey((77,109,243))
                    
        if self.status == 'throwing':
            if not int(self.ani_ind):
                self.can_launch = True
            if int(self.ani_ind) == 15 and self.can_launch: # 15 el número de animación que lanza el martillo
                side = self.rect.topleft
                if not self.face_left:
                    side = self.rect.topright
                self.hammer.add(Hammer(side,20,self.face_left))
                self.can_launch = False

    def update(self):
        #pygame.draw.rect(screen,'red',self.rect)
        if self.face_left and self.player and self.player.rect.x > self.rect.x:
            self.status = 'turning around'
            self.ani_ind = 0
            self.face_left = False
        elif not self.face_left and self.player and self.player.rect.x < self.rect.x:
            self.status = 'turning around reversed'
            self.ani_ind = 0
            self.face_left = True
        #self.move()
        self.animate()
        self.hammer.update()
        self.hammer.draw(screen)
        
    
    def move(self):
        # keys = pygame.key.get_pressed()
        # if keys[pygame.K_LEFT]:
        #     self.rect.x -= 5
        # if keys[pygame.K_RIGHT]:
        #     self.rect.x += 5
        if not self.start_time:
            self.start_time = pygame.time.get_ticks()
        if pygame.time.get_ticks()-self.start_time > self.duration:
            self.start_time = pygame.time.get_ticks()
            self.rect.x += self.vx
            # dice = randint(0,1)
            # if not dice:
            #     self.rect.x += self.vx
            # else:
            #     self.rect.x -= self.vx
         

class Hammer(pygame.sprite.Sprite):
    def __init__(self, pos,angle, left):
        super().__init__()
        self.left = left
        self.animations = load_folder_images('enemy/hammer bro/hammer')
        for ani in self.animations:
            ani.set_colorkey((77,109,243))
        self.image =  self.animations[0]
        self.rect = self.image.get_rect(topleft=pos)
        if not self.left:
            self.rect = self.image.get_rect(topright=pos)
        self.pos = vec(pos)
        self.gravity = -0.08
        self.vel = vec(uniform(2,4),uniform(2,3.6))
        if self.left:
            self.vel.x *= -1
        else:
            self.image = pygame.transform.flip(self.image,True,False)
        self.angle = radians(angle)
        self.copy_img = self.image.copy()
        self.rotation = 60
        self.mask = pygame.mask.from_surface(self.image)
        self.orig_pos = vec(self.rect.midbottom)

    def update(self):
        #pygame.draw.rect(screen,'red',self.rect)
        self.pos.x += self.vel.x*cos(self.angle)
        self.pos.y += self.vel.y*-sin(self.angle)
        self.vel.y += self.gravity
        if not self.left:
            self.rect.topright = self.pos
        else:
            self.rect.topleft = self.pos
        self.rotate()
    
    def rotate(self):
        if self.left:
            self.image = pygame.transform.rotozoom(self.copy_img,self.rotation,1)
        else:
            self.image = pygame.transform.rotozoom(self.copy_img,-self.rotation,1)
        self.rect = self.image.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.rotation = (self.rotation+8)%360

class Player(pygame.sprite.Sprite):
        def __init__(self):
            super().__init__()
            self.image = pygame.Surface((40,40)) 
            self.image.fill('red')
            self.rect = self.image.get_rect(center = (300,300))
            self.mask = pygame.mask.from_surface(self.image)

        def update(self):
            if pygame.mouse.get_pos():
                self.rect.center = pygame.mouse.get_pos()

if __name__ == '__main__':
    left = True
    head = pygame.sprite.GroupSingle(Head((500,500),30,left))
    hammer = pygame.sprite.Group(head.sprite)
    hammer.add(Handle((500,500),30,left))

    hammer_bro = pygame.sprite.GroupSingle()
    enemy = pygame.sprite.GroupSingle(Enemy((300,400)))
    color = 'white'
    rotation = 0
    player = pygame.sprite.GroupSingle(Player())
    while True:
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                hammer_bro.add(Hammer(pygame.mouse.get_pos(),30,True))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    rotation += 30
                    # FIXME: 144 la altura de la imagen original
                    for spr in hammer.sprites():
                        spr.fixed_rotation((55,144),rotation)
                if event.key == pygame.K_c:
                    rotation -= 30
                    for spr in hammer.sprites():
                        spr.fixed_rotation((55,144),rotation)
                if event.key == pygame.K_x:
                    enemy.sprite.status = 'turning around'
                    enemy.sprite.ani_ind = 0
        screen.fill(color)
        # player.update()
        # player.draw(screen)
        hammer_bro.update()
        hammer_bro.draw(screen)
        collide = pygame.sprite.spritecollide(player.sprite, head, False, pygame.sprite.collide_mask)
        # if collide:
        #     color = 'red'
        # else:
        #     color = 'lightblue'
        #hammer.update()
        hammer.draw(screen)

        enemy.update()
        enemy.draw(screen)
        # for point in points:
        #     pygame.draw.circle(screen,'red',point,2)
        
        #hammer.draw(screen)
        # Draw.
        debug(str(fpsClock.get_fps()))

        pygame.display.update()
        fpsClock.tick(fps)
