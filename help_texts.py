helptxt_title = "명령어 모음 | COMMAND DESCRIPTION"
helptxt_desc = """
**ver. 2.20201221**
변수는 *기울여서* 표기하고
= 꼭 필요한 변수는 <>로 감싸서
= 그렇지 않은 변수는 ()로 감싸서
= 여러 형태가 될 수 있는 변수는 |로 구분하고 밑줄을 쳐서
표기합니다.

<this parameter is necessary>
(this parameter is optional)
__choose|one|of|these|parameters__
""".strip()

helptxt_forscrim_name = "\u200b\n\n*스크림 관련 | For scrim*"
helptxt_forscrim_desc1 = """
**m;make**
매치를 만듭니다.


**m;__teamadd|t__ <*팀이름*>**
*팀이름*으로 팀을 추가합니다.


**m;__teamremove|tr__ <*팀이름*>**
*팀이름* 이름을 가진 팀을 삭제합니다.
(팀에 있던 플레이어는 자동으로 나가집니다)


**m;in <*팀이름*>**
*팀이름* 팀에 참가합니다.


**m;out**
자신이 속한 팀에서 나갑니다.


**m;map __<*맵정보*|*맵별명*>__**
맵을 불러옵니다.

*맵정보*는 "아티스트 - 제목 (제작자) [난이도명]" 형식이어야 합니다.
예 : `TUYU - Doro no Bunzai de Watashi dake no Taisetsu o Ubaouda Nante (SnowNiNo_) [Estrangement]`

*맵별명*은 봇 전용 시트(`m;sheetslink`)에 Special열에 등록되어 있는 단어여야 합니다.
예 : `practice24;NM1`


**m;__mapmode|mm__ <*모드*>**
맵 모드를 등록합니다. NM, HR, FM 등으로 정해주세요


**m;__maptime|mt__ <*숫자*>**
맵 시간을 설정합니다. `m;start` 명령어를 사용할 때 필수로 설정해야 합니다.


**m;__mapscore|ms__ __<*숫자*|auto>__ (*filepath*)**
*숫자*를 입력하면 이 맵의 오토 점수를 등록합니다.
이 때 *filepath*는 입력하지 않아도 됩니다. (V2 계산에 사용)

auto를 입력하면 내장된 오토 점수 자동 계산 프로그램으로 계산하여 등록합니다.
이 때 *filepath*는 입력해야 합니다. (봇 오너 불러라)


**m;__score|sc__ <*점수*> (*확도*) (*미스*)**
수동으로 점수를 입력해야 할 경우 사용합니다.


**m;__scoreremove|scr__**
수동으로 점수를 삭제해야 할 경우 사용합니다.


**m;end**
스크림을 끝내고 초기화합니다.
""".strip()

helptxt_forscrim_desc2 = """
**m;__mapmoderule|mr__ <*숫자들1*> <*숫자들2*> <*숫자들3*> <*숫자들4*> <*숫자들5*> <*숫자들6*>**
모드(NM, HD, HR 등) 당 가능한 모드(None, Hidden, HardRock 등)를 설정합니다.
*숫자들1~6*은 각각 NM, HD, HR, DT, FM, TB 모드일 때의 가능한 모드 숫자를 ','으로 구분하여 적어야 하며,
모드 숫자는 다음에 해당하는 숫자를 모두 더해 사용합니다.
```'None': 0,
'Hidden': 1,
'HardRock': 2,
'DoubleTime': 4,
'NoFail': 8,
'HalfTime': 16,
'NightCore': 32,
'Easy': 64```

예 : 기본 모드 룰은 다음 명령어를 실행한 것과 같습니다.
`m;mapmoderule 0,8 2,10 1,9 4,5,12,13 0,1,2,3,8,9,10,11 0,1,2,3,8,9,10,11`


**m;__onlineload|l__ (*숫자*)**
온라인 기록을 자동으로 불러옵니다.
m;bind를 사용하지 않은 사람은 불러오지 않습니다.
제목이나 난이도명이 다른 기록, `m;map`, `m;mapmode` 등으로 모드가 정해진 경우 `m;mapmoderule`에 따라 조건에 맞지 않는 기록은 불러오지 않습니다.

*숫자*에 특정 수를 입력하여, 일부분만 검사하여 기록을 불러올 수 있습니다.
다음에 해당하는 숫자를 더하여 *숫자*에 입력하세요. (입력이 없을 시 모두 더한 값 31을 사용)
아티스트:1 / 제목:2 / 제작자:4 / 난이도:8 / 모드:16
만약 정보가 알려지지 않은 경우는 검사하지 않습니다.

`m;form`을 사용한 경우, 난이도에서 추출한 정보만을 가지고 기록을 불러옵니다. (*숫자*는 무시됨)
예 : `m;form [number] title [diff]`로 모드, 제목, 난이도명만 추출했는데 아티스트를 검사하고자 하는 경우)
""".strip()

helptxt_forscrim_desc3 = """
**m;form <*형식*>**
스크림시 원본 맵 대신 따로 맵풀을 짜서 사용하는 경우, 난이도명에 각 맵의 정보가 들어있을 때 꼭 사용합니다.
다음에 해당하는 단어를 활용하여 난이도명의 형식을 *형식*에 입력합니다.
모드:number / 제목:title / 아티스트:artist / 제작자:author / 난이도명:diff

예 : **모든 맵**의 난이도명이 `[FM1] Everybody Falls [Neli's Eliminated]`, `[NM5] encounter [LGV's Constellation]`와 같이 되어 있으면
`[number] title [diff]`가 됩니다.

토씨 하나라도 틀리게 되면 `m;onlineload`에서 기록을 불러오지 않을 수 있습니다.
예 : `[number] title [diff]` 대신 `[number]title[diff]`, `[numbur] title [diff]` 등을 사용하면 기록을 불러올 수 없습니다.


**m;bind <*숫자*>**
*숫자*에 스크림에 사용할 계정의 UID를 입력하세요.


**m;submit __(nero2|jet2|osu2)__**
점수를 계산하여 결과를 보여줍니다.
아무 입력 없이 `m;submit`만 하면 V1으로 계산합니다.

nero2 = osu!droid (International) 디스코드 서버에서 토너먼트에 사용되는 V2 계산식입니다.
V2점수 = 반올림({(점수/오토점수) x 600,000 + (확도/100)^4 x 400,000} x (1 - 0.003 x 미스))

jet2 = Nelitoru(제토넷#8729)가 만든 V2 계산식입니다.
V2점수 = 반올림((점수/오토점수) x 500,000 + (max(확도-80, 0)/20)^2 * 500,000))

osu2 = osu!에서 사용하는 V2 계산식입니다.
V2점수 = 반올림((점수/오토점수) x 700,000 + (확도/100)^10 * 300,000)
\u200b
"""
helptxt_forscrim_desc4 = """
**m;start**
현재 저장된 맵 정보를 가지고 다음을 자동으로 실행합니다.
1. 맵 시간만큼 기다립니다. (`m;maptime` 필수)
2. 이후 30초를 추가로 기다립니다.
3. 온라인 기록을 자동으로 불러오고 결과를 nero V2로 집계합니다.


**m;abort**
현재 진행중인 매치를 중지합니다.

\u200b
""".strip()

helptxt_other_name = "\u200b\n\n그 외 | Others"
helptxt_other_desc = """
**m;ping**
Pong! 핑을 알려줍니다.

**m;timer <*숫자*> (*이름*)**
*숫자*만큼 타이머를 작동합니다.
*이름*을 설정하지 않을 시 자동으로 숫자로 설정됩니다. (0, 1, 2, ...)

**m;roll <*숫자11*d*숫자12*> (*숫자21*d*숫자22*) (*숫자31*d*숫자32*) ...**
1~*숫자n2*가 적힌 주사위를 *숫자n1*번 굴립니다. 
""".strip()

helptxt_admin = """
m;teamforceadd (tf) <not yet>
m;teamforceremove (tfr) <not yet>
m;say
m;sayresult
m;run
""".strip()

if __name__ == '__main__':
    print(len(helptxt_forscrim_desc1))
    print(len(helptxt_forscrim_desc2))
    print(len(helptxt_forscrim_desc3))
    print(len(helptxt_forscrim_desc4))