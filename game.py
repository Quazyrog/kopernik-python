from game_util import Player, Game, Level
from pygame import Vector2


class MyGame(Game):
    def __init__(self):
        super().__init__()
        self.levels = {}

    def initialize(self):
        super().initialize()
        self.player = Player()
        self.level = MainLevel(self)
        self.level.set_player(self.player, True)

    def activate_object(self, map_object):
        print(map_object)
        

class MainLevel(Level):
    def __init__(self, game):
        super().__init__("Main", game)


game = MyGame()
game.start()
