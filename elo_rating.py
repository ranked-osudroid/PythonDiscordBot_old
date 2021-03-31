import decimal
d = decimal.Decimal

ELO_MID_RATING = d('1500')

class EloRating:
    def __init__(self, player_rating: d = ELO_MID_RATING, opponent_rating: d = ELO_MID_RATING, k=40, stdv=400):
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

    def update(self, player_win_rate: d, give_bonus: bool = False):
        playerbefr = self.player_rating
        oppontbefr = self.opponent_rating
        self.player_rating += self.k * (player_win_rate - self.estimated_chance(playerbefr, oppontbefr))
        self.opponent_rating += self.k * (1 - player_win_rate - self.estimated_chance(oppontbefr, playerbefr))
        if give_bonus:
            self.player_rating -= (playerbefr - ELO_MID_RATING) / d('200')
            self.opponent_rating -= (oppontbefr - ELO_MID_RATING) / d('200')

    def get_ratings(self):
        return self.player_rating, self.opponent_rating


if __name__ == '__main__':
    p = d('1500')
    q = d('1800')

    g = EloRating(p, q)
    res = g.get_ratings()
    print(f"초기값 (P1 vs P2) : {res[0]} vs {res[1]}\n")
    for i in range(9):
        s = 1 - d('.125') * i
        g.update(s)
        res = g.get_ratings()
        print(f"승률 {s}일 때   : {res[0]} vs {res[1]}")
        g.set_player_rating(p)
        g.set_opponent_rating(q)
