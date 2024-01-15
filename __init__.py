import threading

from BaseClasses import Tutorial
from ..AutoWorld import WebWorld, World
from .Locations import all_locations, location_table
from .Items import GLItem, itemList, item_table
from .Regions import create_regions, connect_regions
from .Rom import Rom


class GauntletLegendsWebWorld(WebWorld):
    settings_page = "games/SADX/info/en"
    theme = 'partyTime'
    tutorials = [
        Tutorial(
            tutorial_name='Setup Guide',
            description='A guide to playing Sonic Adventure DX',
            language='English',
            file_name='setup_en.md',
            link='setup/en',
            authors=['jamesbrq']
        )
    ]


class GauntletLegendsWorld(World):
    """
    MLSS funny haha
    """
    game = "Gauntlet Legends"
    web = GauntletLegendsWebWorld()
    data_version = 1
    item_name_to_id = {name: data.code for name, data in item_table.items()}
    location_name_to_id = {loc_data.name: loc_data.id for loc_data in all_locations}
    required_client_version = (0, 4, 3)
    crc32: str = None
    output_complete: threading.Event = threading.Event()

    excluded_locations: []

    def create_regions(self) -> None:
        create_regions(self.multiworld, self.player)
        connect_regions(self.multiworld, self.player)

    def fill_slot_data(self) -> dict:
        self.output_complete.wait()
        return {
            "crc32": self.crc32
        }

    def create_items(self) -> None:
        for _ in all_locations:
            self.multiworld.itempool.append(self.create_item("Key"))


    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = \
            lambda state: state.can_reach("Mountain2", "Region", self.player)

    def create_item(self, name: str) -> GLItem:
        item = item_table[name]
        return GLItem(item.itemName, item.progression, item.code, self.player)

    def generate_output(self, output_directory: str) -> None:
        rom = Rom(self.multiworld, self.player)
        self.crc32 = rom.crc32()
        rom.close(output_directory)
        self.output_complete.set()
