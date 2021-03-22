import decimal
d = decimal.Decimal

class EloRating:
    def __init__(self, player_rating: d, opponent_rating: d, k=20, stdv=400):
        self.player_rating = player_rating
        self.opponent_rating = opponent_rating
        self.k = k
        self.stdv = stdv

    def set_player_rating(self, v: d):
        self.player_rating = v

    def set_opponent_rating(self, v: d):
        self.opponent_rating = v

    def estimated_chance(self, a: d, b: d):
        return 1 / (10 ** ((b - a) / self.stdv) + 1)

    def update(self, is_player_win: bool):
        playerbefr = self.player_rating
        oppontbefr = self.opponent_rating
        self.player_rating += self.k * (int(is_player_win) - self.estimated_chance(playerbefr, oppontbefr))
        self.opponent_rating += self.k * (int(not is_player_win) - self.estimated_chance(oppontbefr, playerbefr))

    def get_ratings(self):
        return self.player_rating, self.opponent_rating


if __name__ == '__main__':
    p = d('1500')
    q = d('1500')

    g = EloRating(p, q)
    print(g.get_ratings())
    g.update(True)
    print(g.get_ratings())
