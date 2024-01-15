import typing

from BaseClasses import Item, ItemClassification


class ItemData(typing.NamedTuple):
    code: int
    itemName: str
    progression: ItemClassification


class GLItem(Item):
    game: str = "Sonic Adventure DX"


itemList: typing.List[ItemData] = [
    ItemData(77780000, "Key", ItemClassification.progression),
    ItemData(77780001, "Lightning Potion", ItemClassification.useful),
    ItemData(77780002, "Light Potion", ItemClassification.useful),
    ItemData(77780003, "Acid Potion", ItemClassification.useful),
    ItemData(77780004, "Fire Potion", ItemClassification.useful),
    ItemData(77780005, "Acid Breath", ItemClassification.filler),
    ItemData(77780006, "Electric Breath", ItemClassification.filler),
    ItemData(77780007, "Fire Breath", ItemClassification.filler),
    ItemData(77780008, "Light Amulet", ItemClassification.filler),
    ItemData(77780009, "Acid Amulet", ItemClassification.filler),
    ItemData(77780010, "Electric Amulet", ItemClassification.filler),
    ItemData(77780011, "Fire Amulet", ItemClassification.filler),
    ItemData(77780012, "Electric Shield", ItemClassification.useful),
    ItemData(77780013, "Fire Shield", ItemClassification.useful),
    ItemData(77780014, "Invisibility", ItemClassification.useful),
    ItemData(77780015, "Levitate", ItemClassification.filler),
    ItemData(77780016, "Speed Boots", ItemClassification.useful),
    ItemData(77780017, "3-Way Shot", ItemClassification.filler),
    ItemData(77780018, "5-Way Shot", ItemClassification.useful),
    ItemData(77780019, "Rapid Fire", ItemClassification.filler),
    ItemData(77780020, "Reflect Shot", ItemClassification.filler),
    ItemData(77780021, "Reflect Shield", ItemClassification.filler),
    ItemData(77780022, "Super Shot", ItemClassification.filler),
    ItemData(77780023, "Timestop", ItemClassification.useful),
    ItemData(77780024, "Phoenix Familiar", ItemClassification.filler),
    ItemData(77780025, "Growth", ItemClassification.filler),
    ItemData(77780026, "Shrink", ItemClassification.filler),
    ItemData(77780027, "Thunder Hammer", ItemClassification.useful),
    ItemData(77780028, "Anti-Death Halo", ItemClassification.filler),
    ItemData(77780029, "Invulnerability", ItemClassification.filler),
    ItemData(77780030, "Fruit", ItemClassification.filler),
    ItemData(77780031, "Meat", ItemClassification.filler),
    ItemData(77780032, "Runestone", ItemClassification.progression),
    ItemData(77780033, "Mirror Piece", ItemClassification.progression),
    ItemData(77780034, "Ice Axe of Untar", ItemClassification.progression),
    ItemData(77780035, "Flame of Tarkana", ItemClassification.progression),
    ItemData(77780036, "Scimitar of Decapitation", ItemClassification.progression),
    ItemData(77780037, "Marker's Javelin", ItemClassification.progression),
    ItemData(77780038, "Soul Savior", ItemClassification.progression),
]

item_table: typing.Dict[str, ItemData] = {item.itemName: item for item in itemList}
items_by_id: typing.Dict[int, ItemData] = {item.code: item for item in itemList}
