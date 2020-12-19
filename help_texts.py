helptxt_title = "명령어 모음 | COMMAND DESCRIPTION"
helptxt_desc = """
**ver. 2.202012119**\n
변수는 *기울여서* 표기하고\n'
= 꼭 필요한 변수는 <>로 감싸서\n'
= 그렇지 않은 변수는 ()로 감싸서\n'
= 여러 형태가 될 수 있는 변수는 |로 구분하고 밑줄을 쳐서\n'
표기합니다.\n\n'
<this parameter is necessary>\n'
(this parameter is optional)\n'
__choose|one|of|these|parameters__'
""".strip()

helptxt_forscrim_name = "*스크림 관련 | For scrim*"
helptxt_forscrim_desc = """
**m;__participate|p__**
지금 열리고 잇는 스크림에 참가합니다.


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
예 : TUYU - Doro no Bunzai de Watashi dake no Taisetsu o Ubaouda Nante (SnowNiNo_) [Estrangement]

*맵별명*은 봇 전용 시트(`m;sheetslink`)에 Special열에 등록되어 있는 단어여야 합니다.
예 : practice24;NM1


**m;mapmode <*모드*>**
맵 모드를 등록합니다. NM, HR, FM 등으로 정해주세요


**m;mapscore __<*숫자*|auto>__ (*filepath*)**
*숫자*를 입력하면 이 맵의 오토 점수를 등록합니다.
이 때 *filepath*는 입력하지 않아도 됩니다. (V2 계산에 사용)

auto를 입력하면 내장된 오토 점수 자동 계산 프로그램으로 계산하여 등록합니다.
이 때 *filepath*는 입력해야 합니다. (봇 오너 불러라)


**m;__onlineload|l__ (*숫자*)**
온라인 기록을 자동으로 불러옵니다.
m;bind를 사용하지 않은 사람은 불러오지 않습니다.
`m;map`, `m;mapmode` 등으로 모드가 정해진 경우 토너먼트 규칙에 따라 모드에 맞지 않는 기록은 불러오지 않습니다.
제목, 난이도 등이 다른 경우 또한 불러오지 않습니다.

*숫자*에 특정 수를 입력하여, 일부분만 검사하여 기록을 불러올 수 있습니다.
다음에 해당하는 숫자를 더하여 *숫자*에 입력하세요. (입력이 없을 시 모두 더한 값 31을 사용)
제목:1 / 아티스트:2 / 난이도:4 / 제작자:8 / 모드:16

`m;form`을 사용한 경우, 난이도에서 추출한 정보만을 가지고 기록을 불러옵니다. (*숫자*가 필요 없음)
검사하는 정보 종류를 결정하는 것은 *숫자*가 우선이므로, 추출하지 못한 정보를 검사하고자 하면 문제가 일어날 수 있습니다.
예 : `m;form [number] title [diff]로 모드, 제목, 난이도명만 추출했는데 아티스트를 검사하고자 하는 경우)


**m;form <*형식*>**
스크림시 원본 맵 대신 따로 맵풀을 짜서 사용하는 경우, 난이도명에 각 맵의 정보가 들어있을 때 꼭 사용합니다.
다음에 해당하는 단어를 활용하여 난이도명의 형식을 *형식*에 입력합니다.
모드:number / 제목:title / 아티스트:artist / 제작자:author / 난이도명:diff

예 : **모든 맵**의 난이도명이 "[FM1] Everybody Falls [Neli's Eliminated]", "[NM5] encounter [LGV's Constellation]"와 같이 되어 있으면
"[number] title [diff]"가 됩니다.

토씨 하나라도 틀리게 되면 `m;onlineload`에서 기록을 불러오지 않을 수 있습니다.
예 : "[number] title [diff]" 대신 "[number]title[diff]", "[numbur] title [diff]" 등을 사용하면 기록을 불러올 수 없습니다.


**m;bind <*숫자*>**
*숫자*에 스크림에 사용할 계정의 UID를 입력하세요.
`m;onlineload`를 사용하려면 필수입니다.


**m;submit __(nero2|jet2|osu2)__**
점수를 계산하여 결과를 보여줍니다.
아무 입력 없이 `m;submit`만 하면 V1으로 계산합니다.

nero2 = osu!droid (International) 디스코드 서버에서 토너먼트에 사용되는 V2 계산식입니다.
V2SCORE = roundHalfUp({(score/maxscore) x 600,000 + (acc/100)^4 x 400,000} x (1 - 0.003 x miss))

jet2 = Nelitoru(제토넷#8729)가 만든 V2 계산식입니다.
V2SCORE = roundHalfUp((score/maxscore) x 500,000 + (max(acc-80, 0)/20)^2 * 500,000))

osu2 = osu!에서 사용하는 V2 계산식입니다.
V2SCORE = roundHalfUp((score/maxscore) x 700,000 + (acc/100)^10 * 300,000)


**m;__score|sc__ <*점수*> (*확도*) (*미스*)**
수동으로 점수를 입력해야 할 경우 사용합니다.


**m;__scoreremove|scr__**
수동으로 점수를 삭제해야 할 경우 사용합니다.
""".strip()

helptxt_other_name = "그 외 | Others"
helptxt_other_desc = """
**m;ping**
Pong! 핑을 알려줍니다.

**m;timer <*숫자*> (*이름*)**
*숫자*만큼 타이머를 작동합니다.
*이름*을 설정하지 않을 시 자동으로 숫자로 설정됩니다. (0, 1, 2, ...)

**m;roll <*숫자11*d*숫자12*> (*숫자21*d*숫자22) (*숫자31*d*숫자32*) ...**
1~*숫자n2*가 적힌 주사위를 *숫자n1*번 굴립니다. 
""".strip()

helptxt_admin = """
m;teamforceadd (tf)
m;teamforceremove (tfr)
m;say
m;sayresult
m;run
""".strip()