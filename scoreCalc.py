import re, decimal

class scoreCalc:
    def __init__(self, path):
        self.file = open(path, mode='r', encoding='utf-8')

    def close(self):
        self.file.close()
    
    def getAutoScore(self):
        halfup = lambda d_num: d_num.quantize(decimal.Decimal('1.'), rounding=decimal.ROUND_HALF_UP)
        dec = decimal.Decimal
        l = self.file.readline().rstrip()
        while l != "[Difficulty]":
            l = self.file.readline().rstrip()
        sv = 0
        st = 0
        hp = 0
        od = 0
        cs = 0
        i = self.file.readline().rstrip()
        r = re.compile(r'(.*):[ ]?(\d+[.]?\d*)')
        while i:
            m = r.match(i)
            if m:
                md, value = m.groups()
                if md == 'HPDrainRate':
                    hp = dec(value)
                elif md == 'CircleSize':
                    cs = dec(value)
                elif md == 'OverallDifficulty':
                    od = dec(value)
                elif md == 'SliderMultiplier':
                    sv = dec(value)
                elif md == 'SliderTickRate':
                    st = dec(value)
            i = self.file.readline().rstrip()
        l = self.file.readline().rstrip()
        while l != "[TimingPoints]":
            l = self.file.readline().rstrip()
        t = self.file.readline().rstrip()
        timings = []
        while t:
            t = t.split(',')
            offset = dec(t[0])
            secPerbit = dec(t[1])
            speed = 1
            if secPerbit < 0:
                secPerbit, speed = dec(timings[-1][1]), (dec(-100) / secPerbit).\
                    quantize(dec('.0001'), rounding=decimal.ROUND_HALF_UP)
            timings.append((offset, secPerbit, speed))
            t = self.file.readline().rstrip()
        l = self.file.readline().rstrip()
        while l != "[HitObjects]":
            l = self.file.readline().rstrip()
        score = 0
        combo = 0
        tindex = 0
        tL = len(timings)
        mapdiff = 1 + hp / 10 + od / 10 + (cs - 3) / 4
        rps = 2 + od / 5
        d = self.file.readline().rstrip()
        totaladdscore = 0
        while d:
            totaladdscore = 0
            d = d.split(',')
            time = int(d[2])
            while tindex < tL:
                if time >= timings[tindex][0]:
                    tindex += 1
                else:
                    break
            _type = int(d[3]) % 16
            if _type == 1 or _type == 5:
                pass
            elif _type == 2 or _type == 6:
                repeat = int(d[6])
                length = dec(d[7]).quantize(dec('.0001'), rounding=decimal.ROUND_HALF_UP)
                beats = (length / (sv * timings[tindex - 1][2] * 100) * st). \
                    quantize(dec('1'), rounding=decimal.ROUND_UP)
                totaladdscore += 30 * repeat
                totaladdscore += 10 * (beats - 1) * repeat
                combo += beats * repeat
            else:
                spintime = int(d[5]) - time
                needspin = rps * spintime // 1000
                if spintime < 50:
                    needspin = 0.1
                flag = False
                spinnedtime = 0
                while spinnedtime <= spintime:
                    spinnedtime += 200
                    needspin -= 1
                    if flag:
                        totaladdscore += 1000
                    else:
                        totaladdscore += 100
                    if needspin <= 0:
                        flag = True
            totaladdscore += halfup(300 + 12 * combo * mapdiff)
            score += totaladdscore
            combo += 1
            d = self.file.readline().rstrip()
        return combo - 1, score

if __name__ == '__main__':
    p = "songs/Various Artist - Practice Pool 10/" \
        "Various Artist - Practice Pool 10 (Various Mapper) [[HD1] SELF CONTROL!! (ktgster) [Special]].osu"
    s = scoreCalc(p)
    print(s.getAutoScore())
    s.close()
