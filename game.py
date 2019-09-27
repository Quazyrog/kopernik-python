from game_util import Player, Game, Level, register_level


class MyPlayer(Player):
    def __init__(self):
        super().__init__()


@register_level("Main")
class MainLevel(Level):
    def __init__(self, game):
        super().__init__(game)


@register_level("North")
class MainLevel(Level):
    def __init__(self, game):
        super().__init__(game)


game = Game()
game.initialize("Main")
game.main_loop()
