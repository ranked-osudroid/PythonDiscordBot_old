from friend_import import *

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

    def update(self, player_win_rate: d, extra_adjust: bool = False):
        playerbefr = self.player_rating
        oppontbefr = self.opponent_rating
        dplayerr = self.k * (player_win_rate - self.estimated_chance(playerbefr, oppontbefr))
        dopponentr = self.k * (1 - player_win_rate - self.estimated_chance(oppontbefr, playerbefr))
        if extra_adjust:
            dplayerr -= get_elo_rank_entry_cost(playerbefr)
            dopponentr -= get_elo_rank_entry_cost(oppontbefr)
        self.player_rating += dplayerr
        self.opponent_rating += dopponentr
        return dplayerr, dopponentr

    def get_ratings(self):
        return self.player_rating, self.opponent_rating


if __name__ == '__main__':
    p = d('1500')
    q = d('1999')

    g = EloRating(p, q, 50, 2500)
    res = g.get_ratings()
    print(f"초기값 (P1 vs P2) : player {res[0]} vs opponent {res[1]}")
    print(f"k = {g.k} / stdv = {g.stdv}\n")
    N = 16
    for i in range(N+1):
        s = (1 - i / d(N)).quantize(d('.0001'))
        res = g.update(s, True)
        g.get_ratings()
        print(f"승률 {s}일 때 : player {res[0].quantize(d('.0001'), rounding=decimal.ROUND_FLOOR)} "
              f"& opponent {res[1].quantize(d('.0001'), rounding=decimal.ROUND_FLOOR)}")
        g.set_player_rating(p)
        g.set_opponent_rating(q)
