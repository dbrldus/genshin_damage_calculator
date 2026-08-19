from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool, ask_multi_choice


class ScrollOfTheHeroOfCinderCity(Artifact):
    """잿더미성 용사의 두루마리
    2세트: 효과 없음
    4세트: 장착 캐릭터가 상응하는 원소 타입 관련 반응 발동 후, 
    주변에 있는 파티 내 모든 캐릭터의 해당 원소 반응과 관련된 원소 피해 보너스가 12% 증가한다. 지속 시간: 15초. 
    해당 효과 발동 시 장착 캐릭터가 밤혼 가호 상태일 경우, 추가로 주변 에 있는 파티 내 모든 캐릭터의 해당 원소 반응과 관련된 원소 피해 보너스가 28% 증가한다. 
    지속 시간: 20초. 장착 캐릭터가 대기 상태일 때도 상술한 효과를 발동할 수 있다. 동명의 성유물 세트가 생성한 피해 보너스 효과는 중첩되지 않는다.
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        pass

    def apply_4set(self, all_hits, wearer) -> None:
        # 반응 참여 원소는 2개로 고정되지 않는다 — 적에게 여러 원소가 동시에 부착된 상태에서
        # (예: 감전으로 물·번개가 함께 붙은 머리) 착용자가 결정 반응을 여러 번 일으키면
        # 물결정·번개결정이 모두 발생해 물·번개·바위 등 3원소 이상의 피해 보너스가 함께 켜진다.
        # 그래서 개수 제한 없이 참여 원소를 다중 선택한다.
        options = ['불', '물', '얼음', '번개', '바람', '바위', '풀']
        fields = [
            "pyro_dmg_bonus",
            "hydro_dmg_bonus",
            "cryo_dmg_bonus",
            "electro_dmg_bonus",
            "anemo_dmg_bonus",
            "geo_dmg_bonus",
            "dendro_dmg_bonus",
        ]
        selected = ask_multi_choice(
            "[잿더미성 용사의 두루마리 4세트] 반응에 참여한 원소 (여러 개 선택 가능)", options
        )
        if not selected:
            return

        is_nightsouls_blessing = ask_bool("[잿더미성 용사의 두루마리 4세트] 밤혼 가호 상태?")

        # 동명 세트의 피해 보너스는 중첩되지 않는다 — 다만 착용자마다 반응 참여 원소가
        # 다를 수 있으므로 두 번째 착용자를 통째로 무시하면 안 된다. 원소 필드별로
        # 최댓값을 잡도록 apply_unique_buff에 맡긴다. 밤혼 가호 증가분까지 합산한
        # 최종 값을 한 번에 제출해야 최댓값 비교가 쪼개지지 않는다.
        source = (self.artifact_set, 4)
        bonus  = 0.12 + (0.28 if is_nightsouls_blessing else 0.0)
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                for idx in selected:
                    hit.apply_unique_buff(source, fields[idx], bonus)

    def apply_4set_dependent(self, all_hits, wearer):
        pass