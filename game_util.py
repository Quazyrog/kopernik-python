import pygame
import pytmx
from pygame.sprite import Group, Sprite, spritecollideany
from pygame.math import Vector2
from pytmx import TiledTileLayer, TiledObject

SCREEN_SIZE = (1366, 768)
ASSETS_DIR = "./Assets"


class Game:
    def __init__(self):
        self.running = False
        self.screen = None
        self.player = None
        self.level = None
        self.player_movement = Vector2(0, 0)

    def start(self) -> None:
        self.initialize()
        self.running = True
        t0 = pygame.time.get_ticks()
        while self.running:
            self.handle_events()
            t1 = pygame.time.get_ticks()
            self.update((t1 - t0) / 1000)
            self.render()
            t0 = t1

    def initialize(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                sgn = 1 if event.type == pygame.KEYDOWN else -1
                change = Vector2(0 ,0)
                if pygame.K_UP == event.key:
                    change.y = -sgn
                elif pygame.K_DOWN == event.key:
                    change.y = sgn
                elif pygame.K_LEFT == event.key:
                    change.x = -sgn
                elif pygame.K_RIGHT == event.key:
                    change.x = sgn
                elif pygame.K_SPACE == event.key and event.type == pygame.KEYUP:
                    sprite = pygame.sprite.spritecollideany(self.player, self.level.interactions, False)
                    if sprite is None:
                        return
                    interacted = sprite.map_object
                    self.level.activate_object(interacted)
                self.player_movement += change
                self.player.move(self.player_movement)

    def update(self, time_delta: float) -> None:
        self.player.update(time_delta)

    def render_tiles_layer(self, layer: TiledTileLayer, offset: Vector2) -> None:
        for x, y, image in layer.tiles():
            pos_x = offset[0] + x * self.level.tile_size
            pos_y = offset[1] + y * self.level.tile_size
            self.screen.blit(image, (pos_x, pos_y))

    def render_objects_layer(self, layer: TiledTileLayer, offset: Vector2) -> None:
        for obj in layer:
            print(obj, obj.image)
            if obj.image:
                self.screen.blit(obj.image, (obj.x + offset.x, obj.y + offset.y))


    def render(self) -> None:
        offset = Vector2()
        offset.x = (SCREEN_SIZE[0] - self.level.map_data.width * self.level.tile_size) // 2
        offset.y = (SCREEN_SIZE[1] - self.level.map_data.height * self.level.tile_size) // 2

        self.screen.fill((0, 0, 0))
        for layer in self.level.map_data.visible_tile_layers:
            self.render_tiles_layer(self.level.map_data.layers[layer], offset)
        for layer in self.level.map_data.visible_object_groups:
            self.render_objects_layer(self.level.map_data.layers[layer], offset)
        self.screen.blit(self.player.image, self.player.rect.move(offset.x, offset.y))

        pygame.display.flip()

    
class Level:
    def __init__(self, name: str, game: Game):
        self.map_data = pytmx.load_pygame("%s/%s.tmx" % (ASSETS_DIR, name))
        self.colliders = pygame.sprite.Group()
        self.interactions = pygame.sprite.Group()
        self.triggers = pygame.sprite.Group()
        self.game = game
        self.player = None
        self.tile_size = self.map_data.tilewidth
        self.bounds = pygame.Rect(0, 0, self.tile_size * self.map_data.width, self.tile_size * self.map_data.height)
        self.name = name
        assert self.map_data.tilewidth == self.map_data.tileheight

        for group in self.map_data.objectgroups:
            if group.name == "Collision":
                for obj in group:
                    self.colliders.add(MapObject(obj))
            if group.name == "Interaction":
                for obj in group:
                    self.interactions.add(MapObject(obj))
            if group.name == "Trigger":
                for obj in group:
                    self.triggers.add(MapObject(obj))

    def set_player(self, player: "Player", on_spawn : bool) -> None:
        self.player = player
        player.level = self
        if not on_spawn:
            return
        try:
            spawn = self.map_data.get_object_by_name("Spawn")
            player.position = Vector2(spawn.x, spawn.y)
        except ValueError:
            pass

    def activate_object(self, obj : TiledObject) -> None:
        print(obj)


class MapObject(pygame.sprite.Sprite):
    def __init__(self, obj_data):
        super().__init__()
        self.rect = (obj_data.x, obj_data.y, obj_data.width, obj_data.height)
        self.map_object = obj_data


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.level = None
        self.image = pygame.image.load("%s/Player.png" % ASSETS_DIR)
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self._position = Vector2(0, 0)
        self._speed = Vector2(0, 0)
        self.velocity = 2
        self._triggered = set()

    def move(self, direction: Vector2):
        try:
            self._speed = direction.normalize() * self.velocity * self.level.tile_size
        except ValueError:
            self._speed = Vector2(0, 0)

    @property
    def position(self) -> Vector2:
        return self._position

    @position.setter
    def position(self, value: Vector2) -> None:
        self._position = value
        self.rect = pygame.Rect(value.x, value.y, self.rect.width, self.rect.height)

    def update(self, time_delta: float):
        if self._speed.length() == 0:
            return
        before = self.rect
        mov = self._speed * time_delta
        self.rect = pygame.Rect(self.position.x + mov.x, self.position.y + mov.y, before.width, before.height)
        if spritecollideany(self, self.level.colliders, False) is None and self.level.bounds.contains(self.rect):
            self._position += mov
            s = set()
            for obj in pygame.sprite.spritecollide(self, self.level.interactions, False):
                s.add(obj.map_object)
            for obj in s:
                if obj not in self._triggered:
                    self.level.activate_object(obj)
            self._triggered = s
        else:
            self.rect = before
