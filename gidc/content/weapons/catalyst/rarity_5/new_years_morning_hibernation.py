from gidc.core.weapon import Weapon
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool


class NewYearsMorningHibernation(Weapon):
    """나른한 새해 (New Year's Morning Hibernation) | 법구 | 5성
    패시브: 온천과 매 그리고 나루카미
    - 확산 반응 발동 후 6초 동안, 원소 마스터리가 120/150/180/210/240pt 증가한다.
    - 원소전투 스킬이 적에게 명중 후 9초 동안, 원소 마스터리가 96/120/144/168/192pt 증가한다.
    - 원소폭발이 적에게 명중 후 30초 동안, 원소 마스터리가 32/40/48/56/64pt 증가한다
    """

    _SWIRL_EM = [120, 150, 180, 210, 240]
    _SKILL_EM = [96, 120, 144, 168, 192]
    _BURST_EM = [32, 40, 48, 56, 64]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.ELEMENTAL_MASTERY,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 나른한 새해"
        hits  = all_hits[wearer].values()

        # 세 효과는 트리거도 지속 시간도 따로다(확산 6초 / E 9초 / Q 30초). 서로를 함의하지
        # 않으므로 배타적 선택이 아니라 독립된 질문 셋이고, 켜진 만큼 합산된다.
        # 붉은 달의 형상이 ask_choice 하나로 받은 것과 갈리는 자리다 — 거기는 뒤 단계가 앞
        # 단계를 함의해서 따로 물으면 모순 입력이 생겼다.
        #
        # 확산은 「누가 발동한 확산인가」를 문구가 밝히지 않는다. 착용자여야 한다면 바람
        # 캐릭터 전용이 되는데, 뒤 두 줄이 「원소전투 스킬/폭발이 적에게 명중」으로 착용자를
        # 가리키는 것과 달리 이 줄만 주어가 없다. 파티 확산일 가능성을 닫지 않도록 착용자
        # 원소로 걸러 내지 않고 묻는다(등방울꽃의 애가와 같은 판단).
        buffs = (
            ("확산 반응 발동 후 6초 이내",        self._SWIRL_EM[r], "확산"),
            ("원소전투 스킬 명중 후 9초 이내",     self._SKILL_EM[r], "원소전투 스킬"),
            ("원소폭발 명중 후 30초 이내",        self._BURST_EM[r], "원소폭발"),
        )
        for question, amount, note in buffs:
            if not ask_bool(f"[나른한 새해] {question} 여부 (원소 마스터리 +{amount})"):
                continue
            for hit in hits:
                # 꼬리표 없는 평범한 원소 마스터리다. em_from_pct_share는 「EM을 %로 나눠
                # 받은 지분」에만 붙는 것이고(설탕·나히다), 무기가 주는 실수치 EM은 카즈하
                # 같은 EM→% 변환의 재료가 되는 게 맞다.
                hit.add("em_from_flat", amount, label, note=note)
