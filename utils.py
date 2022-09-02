import os
import pygame
from random import randint
import json
import sys

vec = pygame.math.Vector2

# probar, getattr lanza una exception ValueError
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def import_animations_from_folders(path):
    animations = {}
    for root, dirs, files in os.walk(path):
        for name in dirs:
            r = os.path.join(root, name)
            animations[name] = load_folder_images(r)
    return animations

def debug(info,x=10,y=10):
    font = pygame.font.Font(None, 42)
    display_surf = pygame.display.get_surface()
    debug_surface = font.render(str(info),True,'White')
    debug_rect = debug_surface.get_rect(topleft=(x,y))
    pygame.draw.rect(display_surf,'Black',debug_rect)
    display_surf.blit(debug_surface,debug_rect)

def player_exists(data, player_name):
    for line in data:
        if line["player_name"] == player_name:
            return True
    return False

def import_folder(path):
    assert(path[-1] != '/')
    res = []
    for _,_,files in os.walk(path):
        for file in files:
            res.append(path+'/'+file)
    return res

# carga todas las imágenes que estén en una carpeta
def load_folder_images(path, scale=False, width=0,height=0):
    imgs = [ pygame.image.load(file).convert_alpha() for file in import_folder(path) ]
    if scale:
        return [pygame.transform.scale(img,(width,height)) for img in imgs ]
    assert(len(imgs))
    return imgs

def load_image(img, scale=False, width=0,height=0):
    img = pygame.image.load(img).convert_alpha()
    if scale:
        return pygame.transform.scale(img,(width,height))
    return img

def write_json(data,file_name):
    try:
        with open(file_name, 'w') as file:
            json.dump(data,file) 
        return True
    except Exception as e:
        print(e)
        return False

def read_json(file_name):
    read_data = dict()
    with open(file_name, 'r') as file:
        read_data = json.load(file) 
    return read_data

def create_player_profile(filename, player_name):
    data = read_json(filename)
    record = {"player_name":player_name, "gold": "0", "silver": "0","bronze":"0"}
    data.append(record)
    write_json(data,filename)
    return record

def get_player_ind(filename,player_name):
    data = read_json(filename)
    for ind,line in enumerate(data):
        if line["player_name"] == player_name:
            return ind,line
    raise ValueError("player doesn't exist")

def get_player_profile(filename,player_name):
    data = read_json(filename)
    for line in data:
        if line["player_name"] == player_name:
            return line
    return ''

def cut_image(path, width, height,y=0):
    image = load_image(path)
    #print(image.get_width())
    n_images = round(image.get_width()/width) # FIXME: round?
    images = []
    for col in range(n_images):
        surface = pygame.Surface((width,height),flags = pygame.SRCALPHA)
        surface.blit(image,(0,0),pygame.Rect(col*width,y,width,height))
        images.append(surface)
    return images

def rand_color():
    return randint(0,255),randint(0,255),randint(0,255)

def show_centered_text(surface,text,pos,font_size,color):
    font = pygame.font.Font('Vera.ttf', font_size)
    text = font.render(text,True,color)
    # text.fill('red')
    rect = text.get_rect(center=pos)
    surface.blit(text,rect)
    return rect

def draw_topleft_text(surface, text,x,y,font_size,color):
    font = pygame.font.Font('Vera.ttf', font_size)
    surf = font.render(text,True,color)
    # surf.fill('red')
    rect = surf.get_rect(topleft=(x,y))
    surface.blit(surf,rect)
    return rect

