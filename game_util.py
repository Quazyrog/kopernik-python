import pygame
import pytmx
from pygame.sprite import Group, Sprite, spritecollideany
from pygame.math import Vector2
from pytmx import TiledTileLayer, TiledObject

SCREEN_SIZE = (1366, 768)
ASSETS_DIR = "./Assets"


class Game:
    _levels = {}

    def __init__(self):
        self.running = False
        self.screen = None
        self.player = None
        self.level = None
        self.player_movement = Vector2(0, 0)

    def main_loop(self) -> None:
        self.running = True
        t0 = pygame.time.get_ticks()
        while self.running:
            self.handle_events()
            t1 = pygame.time.get_ticks()
            self.update((t1 - t0) / 1000)
            self.render()
            t0 = t1

    def initialize(self, starting_level_name: str) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.player = Player()
        self.load_level(starting_level_name)

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
                    self.level.player_interact()
                self.player_movement += change
                self.player.move(self.player_movement)

    def update(self, time_delta: float) -> None:
        self.player.update(time_delta)

    def render_layer(self, layer: TiledTileLayer, offset: Vector2) -> None:
        for x, y, image in layer.tiles():
            pos_x = offset[0] + x * self.level.tile_size
            pos_y = offset[1] + y * self.level.tile_size
            self.screen.blit(image, (pos_x, pos_y))

    def render(self) -> None:
        offset = Vector2()
        offset.x = (SCREEN_SIZE[0] - self.level.map_data.width * self.level.tile_size) // 2
        offset.y = (SCREEN_SIZE[1] - self.level.map_data.height * self.level.tile_size) // 2

        self.screen.fill((0, 0, 0))
        for layer in self.level.map_data.visible_tile_layers:
            self.render_layer(self.level.map_data.layers[layer], offset)
        self.screen.blit(self.player.image, self.player.rect.move(offset.x, offset.y))

        pygame.display.flip()

    def load_level(self, level_name: str) -> None:
        self.level = Game._levels[level_name](self)
        self.level.set_player(self.player, not self.running)
        self.player.level = self.level


class Level:
    _level_name = None
    _action_handlers = {}

    def __init__(self, game: Game):
        self.map_data = pytmx.load_pygame("%s/%s.tmx" % (ASSETS_DIR, self.__class__._level_name))
        self.colliders = pygame.sprite.Group()
        self.interactions = pygame.sprite.Group()
        self.game = game
        self.player = None
        self.tile_size = self.map_data.tilewidth
        self.bounds = pygame.Rect(0, 0, self.tile_size * self.map_data.width, self.tile_size * self.map_data.height)
        assert self.map_data.tilewidth == self.map_data.tileheight

        for group in self.map_data.objectgroups:
            if group.name == "Collision":
                for obj in group:
                    self.colliders.add(MapObject(obj))
            if group.name == "Interaction":
                for obj in group:
                    self.interactions.add(MapObject(obj))

    def set_player(self, player: "Player", on_spawn : bool) -> None:
        self.player = player
        if not on_spawn:
            return
        try:
            spawn = self.map_data.get_object_by_name("Spawn")
            player.position = Vector2(spawn.x, spawn.y)
        except ValueError:
            pass

    def player_interact(self) -> None:
        sprite = pygame.sprite.spritecollideany(self.player, self.interactions, False)
        if sprite is None:
            return
        interacted = sprite.map_object

        if interacted.properties["Action"] == "Teleport":
            level_name = interacted.properties["Level"]
            x = int(interacted.properties["X"])
            y = int(interacted.properties["Y"])
            self.player.position = Vector2(x, y)
            self.player.rect = pygame.Rect(x, y, self.player.rect.width, self.player.rect.height)
            self.game.load_level(level_name)

    def activate_object(self, map_object: TiledObject):
        pass


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
        else:
            self.rect = before


def register_level(name):
    def decorator(level_class):
        print("Register level logic %s -> %s" % (name, str(level_class)))
        Game._levels[name] = level_class
        level_class._level_name = name
        level_class._action_handlers = {}
        return level_class
    return decorator
