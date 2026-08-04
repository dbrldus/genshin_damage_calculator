from dataclasses import dataclass


@dataclass
class Enemy:
    level: int = 90

    # 원소별 기본 내성
    pyro_res:     float = 0.10
    hydro_res:    float = 0.10
    cryo_res:     float = 0.10
    electro_res:  float = 0.10
    anemo_res:    float = 0.10
    geo_res:      float = 0.10
    dendro_res:   float = 0.10
    physical_res: float = 0.10
