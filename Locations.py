import typing

from BaseClasses import Location


class LocationData:
    name: str = ""
    id: int = 0x00

    def __init__(self, name, id_, difficulty):
        self.name = name
        self.id = id_
        self.difficulty = difficulty


class GLLocation(Location):
    game: str = "Gauntlet Legends"


valleyOfFire: typing.List[LocationData] = [
    LocationData("Valley of Fire - Scroll 1", 88870001, 1),
    LocationData("Valley of Fire - Key 1", 88870002, 1),
    LocationData("Valley of Fire - Key 2", 88870003, 1),
    LocationData("Valley of Fire - Key 3", 88870004, 1),
    LocationData("Valley of Fire - Key 4", 88870005, 1),
    LocationData("Valley of Fire - Fire Amulet", 88870006, 1),
    LocationData("Valley of Fire - Key 5", 88870007, 1),
    LocationData("Valley of Fire - Key 6", 88870008, 1),
    LocationData("Valley of Fire - Key 7", 88870009, 1),
    LocationData("Valley of Fire - Fruit 1", 88870010, 1),
    LocationData("Valley of Fire - Key 8", 88870011, 1),
    LocationData("Valley of Fire - Key 9", 88870012, 1),
    LocationData("Valley of Fire - Fire Potion 1", 88870013, 1),
    LocationData("Valley of Fire - Thunder Hammer", 88870014, 1),
    LocationData("Valley of Fire - Fire Potion 2", 88870015, 1),
    LocationData("Valley of Fire - Large Gold Pile", 88870016, 1),
    LocationData("Valley of Fire - Small Gold Pile 1", 88870017, 1),
    LocationData("Valley of Fire - Meat Slab", 88870018, 1),
    LocationData("Valley of Fire - Drumstick", 88870019, 1),
    LocationData("Valley of Fire - Fruit 2", 88870020, 1),
    LocationData("Valley of Fire - Key 10", 88870021, 1),
    LocationData("Valley of Fire - Small Gold Pile 2", 88870022, 1)
]

daggerPeak: typing.List[LocationData] = [
    LocationData("Dagger Peak - Growth", 88870023, 1),
    LocationData("Dagger Peak - Runestone", 88870024, 1),
    LocationData("Dagger Peak - Key 1", 88870025, 1),
    LocationData("Dagger Peak - Speed Boots", 88870026, 1),
    LocationData("Dagger Peak - Key 2", 88870027, 1),
    LocationData("Dagger Peak - Key 3", 88870028, 1),
    LocationData("Dagger Peak - Key 4", 88870029, 1),
    LocationData("Dagger Peak - Key 5", 88870030, 1),
    LocationData("Dagger Peak - Key 6", 88870031, 1),
    LocationData("Dagger Peak - Large Pile of Gold 1", 88870032, 1),
    LocationData("Dagger Peak - Large Pile of Gold 2", 88870033, 1),
    LocationData("Dagger Peak - Full Barrel of Gold", 88870034, 1),
    LocationData("Dagger Peak - Small Pile of Gold 1", 88870035, 1),
    LocationData("Dagger Peak - Small Pile of Gold 2", 88870036, 1),
    LocationData("Dagger Peak - Small Pile of Gold 3", 88870037, 1),
    LocationData("Dagger Peak - Fire  1", 88870038, 1),
    LocationData("Dagger Peak - Fruit", 88870039, 1),
    LocationData("Dagger Peak - Key 7", 88870040, 1),
    LocationData("Dagger Peak - Key 8", 88870041, 1),
    LocationData("Dagger Peak - Half Barrel of Gold", 88870042, 1),
    LocationData("Dagger Peak - Key 9", 88870043, 1),
    LocationData("Dagger Peak - Fire Potion 2", 88870044, 1),
    LocationData("Dagger Peak - Poison Fruit", 88870045, 1),
    LocationData("Dagger Peak - Key 10", 88870046, 1),
    LocationData("Dagger Peak - Key 11", 88870047, 1),
    LocationData("Dagger Peak - Key 12", 88870048, 1),
    LocationData("Dagger Peak - Key 13", 88870049, 1),
    LocationData("Dagger Peak - Key 14", 88870050, 1),
    LocationData("Dagger Peak - Fire Potion 3", 88870051, 1),
    LocationData("Dagger Peak - Meat 1", 88870052, 1),
    LocationData("Dagger Peak - Key 15", 88870053, 1),
    LocationData("Dagger Peak - Key 16", 88870054, 1),
    LocationData("Dagger Peak - Key 17", 88870055, 1),
    LocationData("Dagger Peak - Meat 2", 88870056, 1),
    LocationData("Dagger Peak - Key 18", 88870057, 1)
]

all_locations: typing.List[LocationData] = valleyOfFire + daggerPeak

location_table: typing.Dict[str, int] = {locData.name: locData.id for locData in all_locations}
