from typing import List
from .Locations import LocationData, valleyOfFire, daggerPeak, cliffsOfDesolation, lostCave, volcanicCavern \
    , dragonsLair, castleCourtyard, dungeonOfTorment, towerArmory \
    , castleTreasury, chimerasKeep, poisonedFields, hauntedCemetery \
    , venomousSpire, toxicAirShip, arcticDocks, frozenCamp \
    , crystalMine, eruptingFissure, desecratedTemple \
    , battleTrenches, battleTowers, infernalFortress \
    , gatesOfTheUnderworld

inv_dict: dict[tuple, str] = {
    (0x0, 0x2, 0x0): "Strength",
    (0x0, 0x3, 0x0): "Speed",
    (0x0, 0x4, 0x0): "Armour",
    (0x0, 0x5, 0x0): "Speed",
    (0x0, 0x6, 0x0): "Gold",
    (0x0, 0x7, 0x0): "Key",
    (0x0, 0xA, 0x0): "Level",
    (0x0, 0x8, 0x10): "Lightning Potion",
    (0x0, 0x8, 0x20): "Light Potion",
    (0x0, 0x8, 0x30): "Acid Potion",
    (0x0, 0x8, 0x40): "Fire Potion",
    (0x28, 0x80, 0x4): "Acid Breath",
    (0x28, 0xF0, 0x4): "Lightning Breath",
    (0x28, 0x60, 0x4): "Fire Breath",
    (0x18, 0x70, 0x8): "Light Amulet",
    (0x18, 0x80, 0x8): "Acid Amulet",
    (0x18, 0xF0, 0x8): "Lightning Amulet",
    (0x18, 0x60, 0x8): "Fire Amulet",
    (0x14, 0xF0, 0xC): "Lightning Shield",
    (0x14, 0x60, 0xC): "Fire Shield",
    (0x10, 0xE0, 0x0): "Invisibility",
    (0x10, 0x30, 0x0): "Levitate",
    (0x10, 0x73, 0x1): "Speed Boots",
    (0x50, 0x20, 0x0): "3-Way Shot",
    (0x20, 0x60, 0x1): "5-Way Shot",
    (0x10, 0x50, 0x0): "Rapid Fire",
    (0x18, 0x40, 0x8): "Reflective Shot",
    (0x14, 0x40, 0xC): "Reflective Shield",
    (0x28, 0xB0, 0x8): "Super Shot",
    (0x10, 0xD0, 0x0): "Timestop",
    (0x10, 0x10, 0x1): "Phoenix Familiar",
    (0x10, 0x20, 0x1): "Growth",
    (0x10, 0x30, 0x1): "Shrink",
    (0x28, 0x40, 0x9): "Thunder Hammer",
    (0x11, 0xA0, 0x0): "Anti-Death Halo",
    (0x11, 0xC0, 0x0): "Invulnerability",
    (0x0, 0x1, 0x0): "Fruit",
    (0x0, 0x1, 0x0): "Meat",
    (0x0, 0x10, 0x82): "Runestone",
    (0x0, 0x60, 0x82): "Mirror Piece",
    (0x22, 0xC0, 0x1): "Ice Axe of Untar",
    (0x22, 0xD0, 0x1): "Flame of Tarkana",
    (0x22, 0xE0, 0x1): "Scimitar of Decapitation",
    (0x22, 0xF0, 0x1): "Marker's Javelin",
    (0x22, 0x0, 0x2): "Soul Savior",
    (0x0, 0x4A, 0x80): "Mountain",
    (0x0, 0x1A, 0x80): "Castle",
    (0x0, 0x7A, 0x80): "Ice",
    (0x0, 0x8A, 0x80): "Town",
    (0x0, 0x9A, 0x80): "Temple",
    (0x0, 0xDA, 0x80): "Battlefield",
    (0x0, 0xEA, 0x80): "Skorne",
    (0x0, 0xFA, 0x80): "Secret",  # I have no clue if this is correct
    (0x0, 0xC, 0x80): "Obelisk"
}

item_dict: dict[int, bytes] = {
    77780000: [0x0, 0x0],
    77780001: [0x1, 0x1],
    77780002: [0x1, 0x2],
    77780003: [0x1, 0x3],
    77780004: [0x1, 0x4],
    77780005: [0x2, 0x12],
    77780006: [0x2, 0x11],
    77780007: [0x2, 0x10],
    77780008: [0x2, 0x9],
    77780009: [0x2, 0xA],
    77780010: [0x2, 0x8],
    77780011: [0x2, 0x7],
    77780012: [0x2, 0x18],
    77780013: [0x2, 0x17],
    77780014: [0x2, 0x5],
    77780015: [0x2, 0xD],
    77780016: [0x2, 0x0],
    77780017: [0x2, 0x4],
    77780018: [0x2, 0xE],
    77780019: [0x2, 0x1A],
    77780020: [0x2, 0x2],
    77780021: [0x2, 0x16],
    77780022: [0x2, 0x3],
    77780023: [0x2, 0xC],
    77780024: [0x2, 0x13],
    77780025: [0x2, 0x14],
    77780026: [0x2, 0x15],
    77780027: [0x2, 0x19],
    77780028: [0x2, 0x0],  #
    77780029: [0x2, 0x6],
    77780030: [0x4, 0x1],
    77780031: [0x4, 0x3],
    77780032: [0x15, 0x1],
    77780033: [0x15, 0x2],
    77780034: [0x15, 0x3],
    77780035: [0x15, 0x4],
    77780036: [0x15, 0x5],
    77780037: [0x15, 0x6],
    77780038: [0x15, 0x7],
    77780039: [0x15, 0x8],
    77780040: [0x15, 0x9],
    77780041: [0x15, 0xA],
    77780042: [0x15, 0xB],
    77780043: [0x15, 0xC],
    77780044: [0x15, 0xD],
    77780045: [0x29, 0x1],
    77780046: [0x29, 0x2],
    77780047: [0x29, 0x3],
    77780048: [0x29, 0x4],
    77780049: [0x29, 0x5],
    77780050: [0x3, 0x2]
}

timers = [
    "Light Amulet",
    "Acid Amulet",
    "Lightning Amulet",
    "Fire Amulet",
    "Lightning Shield",
    "Fire Shield",
    "Invisibility",
    "Levitate",
    "Speed Boots",
    "3-Way Shot",
    "5-Way Shot",
    "Rapid Fire",
    "Reflect Shot",
    "Reflect Shield",
    "Timestop",
    "Phoenix Familiar",
    "Growth",
    "Shrink",
    "Anti-Death Halo",
    "Invulnerability"
]

base_count: dict[str, int] = {
    "Key": 1,
    "Lightning Potion": 1,
    "Light Potion": 1,
    "Acid Potion": 1,
    "Fire Potion": 1,
    "Acid Breath": 5,
    "Lightning Breath": 5,
    "Fire Breath": 5,
    "Light Amulet": 30,
    "Acid Amulet": 30,
    "Lightning Amulet": 30,
    "Fire Amulet": 30,
    "Lightning Shield": 10,
    "Fire Shield": 10,
    "Invisibility": 30,
    "Levitate": 30,
    "Speed Boots": 30,
    "3-Way Shot": 30,
    "5-Way Shot": 30,
    "Rapid Fire": 30,
    "Reflect Shot": 30,
    "Reflect Shield": 30,
    "Super Shot": 3,
    "Timestop": 15,
    "Phoenix Familiar": 30,
    "Growth": 30,
    "Shrink": 30,
    "Thunder Hammer": 3,
    "Anti-Death Halo": 30,
    "Invulnerability": 30,
    "Fruit": 50,
    "Meat": 100,
    "Runestone 1": 1,
    "Runestone 2": 2,
    "Runestone 3": 4,
    "Runestone 4": 8,
    "Runestone 5": 16,
    "Runestone 6": 32,
    "Runestone 7": 64,
    "Runestone 8": 128,
    "Runestone 9": 256,
    "Runestone 10": 512,
    "Runestone 11": 1024,
    "Runestone 12": 2048,
    "Runestone 13": 4096,
    "Mirror Piece": 1,
    "Ice Axe of Untar": 1,
    "Flame of Tarkana": 1,
    "Scimitar of Decapitation": 1,
    "Marker's Javelin": 1,
    "Soul Savior": 1
}

levels: dict[int, str] = {
    0x1: "Castle",
    0x2: "Mountain",
    0x7: "Town",
    0x8: "Hell",
    0x9: "Ice",
    0xF: "Boss",
    0x11: "Battlefield"
}

castle_id = [1, 6, 3, 4, 5]

level_locations: dict[int, List[LocationData]] = {
    0x11: castleCourtyard,
    0x12: dungeonOfTorment,
    0x13: towerArmory,
    0x14: castleTreasury,
    0x15: chimerasKeep,
    0x21: valleyOfFire,
    0x22: daggerPeak,
    0x23: cliffsOfDesolation,
    0x24: lostCave,
    0x25: volcanicCavern,
    0x26: dragonsLair,
    0x71: poisonedFields,
    0x72: hauntedCemetery,
    0x73: venomousSpire,
    0x74: toxicAirShip,
    0x81: gatesOfTheUnderworld,
    0x91: arcticDocks,
    0x92: frozenCamp,
    0x93: crystalMine,
    0x94: eruptingFissure,
    0xF1: desecratedTemple,
    0x111: battleTrenches,
    0x112: battleTowers,
    0x113: infernalFortress
}

level_size = [0x9E0, 0x5E0, 0x740, 0x8A0, 0x90, 0x3B0, 0x5A0, 0x890, 0x670, 0x7D0, 0x90, 0xCE0, 0xA50, 0xA30, 0x8E0,
              0x760, 0xE90, 0xE40, 0xE00, 0xCD0, 0x3F0, 0xB00, 0xA30, 0xB30]

level_address = [0xF939B0,
                 0xF958B0,
                 0xF945B0,
                 0xF94EE0,
                 0xF84CC0,
                 0xF910B0,
                 0xF915B0,
                 0xF91D00,
                 0xF92710,
                 0xF92F40,
                 0xF84B70,
                 0xF84FA0,
                 0xF85EB0,
                 0xF86B60,
                 0xF877C0,
                 0xF901C0,
                 0xF884E0,
                 0xF89370,
                 0xF8A5F0,
                 0xF8B760,
                 0xF90B50,
                 0xF8D960,
                 0xF8E6E0,
                 0xF8F110]

difficulty_convert: dict[int, int] = {
    0x7: 20,
    0x2: 0,
    0x1: 10,
    0x8: 60,
    0x9: 30,
    0xF: 40,
    0x11: 50
}
