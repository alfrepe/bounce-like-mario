import sys

import pygame
from pygame.locals import *
from utils import *
from random import randint
from math import *

pygame.init()
vec = pygame.math.Vector2
fps = 60
fpsClock = pygame.time.Clock()

width, height = 640, 480
screen = pygame.display.set_mode((width, height))

class Player(pygame.sprite.Sprite):
    def __init__(self, pos) -> None:
        super().__init__()
        self.image = load_image('hammer_resized-removebg.png')
        self.rect = self.image.get_rect(topleft=pos)
    
    def update(self):
        pass

class Particle:
    def __init__(self, color, pos, angle,radius):
        self.color = color
        self.pos = vec(pos)
        self.radius = radius
        self.angle = angle
        self.dir = vec(1,0).rotate(self.angle).normalize()
        self.velocity = 1
        self.duration = pygame.time.get_ticks()
        interval = 2
        self.lifespan = interval
        self.cont = 0
        

    def update(self):
        self.pos.x += self.dir.x * self.velocity
        self.pos.y += self.dir.y * self.velocity
        pygame.draw.circle(screen, self.color, self.pos, self.radius)
        self.cont = 2
        #if pygame.time.get_ticks()-self.duration >= self.lifespan:
        self.radius -= 0.2

class Effect:
    def __init__(self, pos, color='white'):
        self.particles  =[]
        self.color = color
        self.angles = [ang for ang in range(0,210,30)]
        for ang in self.angles:
            self.particles.append(Particle(self.color, pos,-ang,2))

    def update(self):
        self.particles = [particle for particle in self.particles if particle.radius > 0]
        for particle in self.particles:
            particle.update()



if __name__ == '__main__':
    effect_spr = pygame.sprite.GroupSingle()
    wall_jump = pygame.sprite.GroupSingle()
    effects = []
    while True:
        screen.fill('lightblue')
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                effects.append(Effect(pygame.mouse.get_pos()))
                #wall_jump.add(WallJump(pygame.mouse.get_pos(),True))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    wall_jump.sprite.apply()

        # Update.
        for e in effects:
            e.update()
        # Draw.
        #wall_jump.update()
        wall_jump.draw(screen)
        pygame.display.update()
        fpsClock.tick(fps)