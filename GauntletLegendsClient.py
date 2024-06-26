import asyncio
import socket
import traceback
from typing import List, Optional

import Patch
import Utils
from BaseClasses import ItemClassification
from CommonClient import ClientCommandProcessor, CommonContext, get_base_parser, gui_enabled, logger, server_loop
from NetUtils import ClientStatus, NetworkItem

from .Arrays import (
    base_count,
    boss_level,
    castle_id,
    characters,
    difficulty_convert,
    inv_dict,
    level_locations,
    mirror_levels,
    spawners,
    timers,
)
from .Items import ItemData, items_by_id
from .Locations import LocationData

SYSTEM_MESSAGE_ID = 0

READ = "READ_CORE_RAM"
WRITE = "WRITE_CORE_RAM"
INV_ADDR = 0xC5BF0
OBJ_ADDR = 0xC5B20
INV_UPDATE_ADDR = 0x56094
INV_LAST_ADDR = 0x56084
ACTIVE_POTION = 0xFD313
ACTIVE_LEVEL = 0x4EFC0
PLAYER_COUNT = 0x127764
PLAYER_LEVEL = 0xFD31B
PLAYER_ALIVE = 0xFD2EB
PLAYER_PORTAL = 0x64A50
PLAYER_BOSSING = 0x64A54
PLAYER_MOVEMENT = 0xFD307
BOSS_ADDR = 0x289C08
TIME = 0xC5B1C
INPUT = 0xC5BCD


class RetroSocket:
    def __init__(self):
        self.host = "localhost"
        self.port = 55355
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    async def write(self, message: str):
        await asyncio.sleep(0)
        self.socket.sendto(message.encode(), (self.host, self.port))

    async def read(self, message) -> Optional[bytes]:
        await asyncio.sleep(0)
        self.socket.sendto(message.encode(), (self.host, self.port))

        self.socket.settimeout(2)
        try:
            data, addr = self.socket.recvfrom(30000)
        except socket.timeout:
            raise Exception("Socket receive timed out. No data received within the specified timeout.")
        except ConnectionResetError:
            raise Exception("Retroarch is not open. Please open Retroarch and load the correct ROM.")
        response = data.decode().split(" ")
        b = b""
        for s in response[2:]:
            if "-1" in s:
                logger.info("-1 response")
                return None
            b += bytes.fromhex(s)
        return b

    def status(self) -> bool:
        message = "GET_STATUS"
        self.socket.sendto(message.encode(), (self.host, self.port))
        try:
            data, addr = self.socket.recvfrom(1000)
        except ConnectionResetError:
            raise Exception("Retroarch not detected. Please make sure your ROM is open in Retroarch.")
        return True


class RamChunk:
    def __init__(self, arr: bytes):
        self.raw = arr
        self.split = []

    def iterate(self, length: int):
        self.split = [self.raw[i: i + length] for i in range(0, len(self.raw), length)]


def type_to_name(arr) -> str:
    target_tuple = tuple(arr)
    return inv_dict.get(target_tuple, None)


def name_to_type(name) -> bytes:
    if name == "Fruit" or name == "Meat":
        return bytes([0x0, 0x1, 0x0])
    for key, value in inv_dict.items():
        if value == name:
            return bytes(key)
    logger.info(f"Invalid Item: {name}")
    raise ValueError("Value not found in the dictionary")


class InventoryEntry:
    def __init__(self, arr=None, index=None):
        if arr is not None:
            self.raw = arr
            self.addr = 0xC5BF0 + (index * 0x10)
            self.on: int = arr[0]
            self.type: bytes = arr[1:4]
            self.name = type_to_name(self.type)
            self.count: int = int.from_bytes(arr[4:8], "little")
            self.n_addr: int = int.from_bytes(arr[12:15], "little")
            self.p_addr: int = int.from_bytes(arr[8:11], "little")
        else:
            self.raw: bytes
            self.addr: int
            self.on = 0
            self.type: bytes
            self.name = ""
            self.count: int
            self.n_addr: int
            self.p_addr: int


class ObjectEntry:
    def __init__(self, arr=None):
        if arr is not None:
            self.raw = arr
        else:
            self.raw: bytes


def message_format(arg: str, params: str) -> str:
    return f"{arg} {params}"


def param_format(adr: int, arr: bytes) -> str:
    return " ".join([hex(adr)] + [f"0x{byte:02X}" for byte in arr])


class GauntletLegendsCommandProcessor(ClientCommandProcessor):
    def __init__(self, ctx: CommonContext):
        super().__init__(ctx)

    async def _cmd_inv(self, *args):
        await self.ctx.inv_update(" ".join(args[:-1]), int(args[-1]))

    def _cmd_connected(self):
        logger.info(f"Retroarch Status: {self.retro_connected}")


class GauntletLegendsContext(CommonContext):
    command_processor = GauntletLegendsCommandProcessor
    game = "Gauntlet Legends"
    items_handling = 0b101

    def __init__(self, server_address, password):
        super().__init__(server_address, password)
        self.difficulty: int = 0
        self.gl_sync_task = None
        self.received_index: int = 0
        self.glslotdata = None
        self.crc32 = None
        self.socket = RetroSocket()
        self.awaiting_rom = False
        self.locations_checked: List[int] = []
        self.inventory: List[InventoryEntry] = []
        self.inventory_raw: RamChunk
        self.item_objects: List[ObjectEntry] = []
        self.obelisk_objects: List[ObjectEntry] = []
        self.chest_objects: List[ObjectEntry] = []
        self.retro_connected: bool = False
        self.level_loading: bool = False
        self.in_game: bool = False
        self.objects_loaded: bool = False
        self.obelisks: List[NetworkItem] = []
        self.item_locations: List[LocationData] = []
        self.obelisk_locations: List[LocationData] = []
        self.chest_locations: List[LocationData] = []
        self.extra_items: int = 0
        self.limbo: bool = False
        self.in_portal: bool = False
        self.scaled: bool = False
        self.offset: int = -1
        self.clear_counts = None
        self.current_level: bytes = b""
        self.movement: int = 0
        self.init_refactor: bool = False
        self.location_scouts: list[NetworkItem] = []
        self.character_loaded: bool = False

    # Return number of items in inventory
    def inv_count(self):
        return len(self.inventory)

    # Update self.inventory to current in-game values
    async def inv_read(self):
        _inv: List[InventoryEntry] = []
        b = RamChunk(await self.socket.read(message_format(READ, f"0x{format(INV_ADDR, 'x')} 3072")))
        if b is None:
            return
        b.iterate(0x10)
        self.inventory_raw = b
        for i, arr in enumerate(b.split):
            _inv += [InventoryEntry(arr, i)]
        for i in range(len(_inv)):
            if _inv[i].p_addr == 0:
                _inv = _inv[i:]
                break
        new_inv: List[InventoryEntry] = []
        new_inv += [_inv[0]]
        addr = new_inv[0].n_addr
        while True:
            if addr == 0:
                break
            new_inv += [inv for inv in _inv if inv.addr == addr]
            addr = new_inv[-1].n_addr
        self.inventory = new_inv

    # Return InventoryEntry if item of name is in inv, else return None
    async def item_from_name(self, name: str) -> InventoryEntry | None:
        await self.inv_read()
        for i in range(0, self.inv_count()):
            if self.inventory[i].name == name:
                return self.inventory[i]
        return None

    # Return True if bitwise and evaluates to non-zero value
    async def inv_bitwise(self, name: str, bit: int) -> bool:
        item = await self.item_from_name(name)
        if item is None:
            return False
        return (item.count & bit) != 0

    # Return pointer of object section of RAM
    async def get_obj_addr(self) -> int:
        return (
            int.from_bytes(await self.socket.read(message_format(READ, f"0x{format(OBJ_ADDR, 'x')} 4")), "little")
        ) & 0xFFFFF

    # Read a subsection of the objects loaded into RAM
    # Objects are 0x3C bytes long
    # Modes: 0 = items, 1 = chests/barrels
    async def obj_read(self, mode=0):
        obj_address = await self.get_obj_addr()
        _obj = []
        if self.offset == -1:
            b = RamChunk(await self.socket.read(message_format(READ, f"0x{format(obj_address, 'x')} 3840")))
            b.iterate(0x3C)
            for i, arr in enumerate(b.split):
                if arr[0] != 0xFF:
                    self.offset = i
                    break
        b: RamChunk
        if mode == 0:
            b = RamChunk(
                await self.socket.read(
                    message_format(
                        READ,
                        f"0x{format(obj_address + (self.offset * 0x3C), 'x')} {(len(self.item_locations) + 10) * 0x3C}",
                    ),
                ),
            )
            b.iterate(0x3C)
            count = 0
            for obj in b.split:
                if obj[0] == 0xFF:
                    count += 1
            self.extra_items = count
        else:
            b = RamChunk(
                await self.socket.read(
                    message_format(
                        READ,
                        f"0x{format(obj_address + ((self.offset + len(self.item_locations) + self.extra_items + len([spawner for spawner in spawners[(self.current_level[1] << 4) + (self.current_level[0] if self.current_level[1] != 1 else castle_id.index(self.current_level[0]) + 1)] if self.difficulty >= spawner])) * 0x3C), 'x')} {(len(self.chest_locations) + 10) * 0x3C}",
                    ),
                ),
            )
            b.iterate(0x3C)
        for arr in b.split:
            _obj += [ObjectEntry(arr)]
        _obj = [obj for obj in _obj if obj.raw[0] != 0xFF]
        if mode == 1:
            _obj = _obj[: len(self.chest_locations)]
            self.chest_objects = _obj
        else:
            _obj = _obj[: len(self.item_locations)]
            self.item_objects = _obj

    # Update item count of an item.
    # If the item is new, add it to your inventory
    async def inv_update(self, name: str, count: int):
        await self.inv_read()
        if "Runestone" in name:
            name = "Runestone"
        if "Fruit" in name or "Meat" in name:
            name = "Health"
        if "Obelisk" in name:
            name = "Obelisk"
        if "Mirror" in name:
            name = "Mirror Shard"
        for item in self.inventory:
            if item.name == name:
                zero = item.count == 0
                if name in timers:
                    count *= 96
                if "Compass" in name:
                    item.count = count
                elif "Health" in name:
                    max = await self.item_from_name("Max")
                    item.count = min(item.count + count, max.count)
                elif "Runestone" in name or "Mirror" in name or "Obelisk" in name:
                    item.count |= count
                else:
                    item.count += count
                await self.write_inv(item)
                if zero:
                    await self.inv_refactor()
                return
        logger.info(f"Adding new item to inv: {name}")
        await self.inv_add(name, count)

    # Rewrite entire inventory in RAM.
    # This is necessary since item entries are not cleared after full use until a level is completed.
    async def inv_refactor(self, new=None):
        await self.inv_read()
        if new is not None:
            self.inventory += [new]
        for i, item in enumerate(self.inventory):
            if item.name is not None:
                if "Potion" in item.name and item.count != 0:
                    await self.socket.write(
                        message_format(
                            WRITE, param_format(ACTIVE_POTION, int.to_bytes(item.type[2] // 0x10, 1, "little")),
                        ),
                    )
            if i == 0:
                item.p_addr = 0
                item.addr = INV_ADDR
                item.n_addr = item.addr + 0x10
                self.inventory[i] = item
                continue
            item.addr = INV_ADDR + (0x10 * i)
            item.p_addr = item.addr - 0x10
            if i == len(self.inventory) - 1:
                item.n_addr = 0
                self.inventory[i] = item
                break
            item.n_addr = item.addr + 0x10
            self.inventory[i] = item

        for item in self.inventory:
            await self.write_inv(item)

        for i, raw in enumerate(self.inventory_raw.split[len(self.inventory):], len(self.inventory)):
            item = InventoryEntry(raw, i)
            if item.type != bytes([0, 0, 0]):
                await self.write_inv(
                    InventoryEntry(
                        bytes([0, 0, 0, 0, 0, 0, 0, 0])
                        + int.to_bytes(item.addr + 0x10, 3, "little")
                        + bytes([0xE0, 0, 0, 0, 0]),
                        i,
                    ),
                )

        await self.socket.write(
            message_format(WRITE, param_format(INV_UPDATE_ADDR, int.to_bytes(self.inventory[-1].addr, 3, "little"))),
        )
        await self.socket.write(
            message_format(WRITE,
                           param_format(INV_LAST_ADDR, int.to_bytes(self.inventory[-1].addr + 0x10, 3, "little"))),
        )

        await self.socket.write(f"{WRITE} 0xC6BF0 0x{format(self.inv_count(), 'x')}")

    # Add new item to inventory
    # Call refactor at the end to write it into ram correctly
    async def inv_add(self, name: str, count: int):
        new = InventoryEntry()
        if name == "Key":
            new.on = 1
        new.count = count
        if name in timers:
            new.count *= 0x96
        new.type = name_to_type(name)
        last = self.inventory[-1]
        last.n_addr = last.addr + 0x10
        new.addr = last.n_addr
        self.inventory[-1] = last
        new.p_addr = last.addr
        new.n_addr = 0
        await self.inv_refactor(new)

    # Write a single item entry into RAM
    async def write_inv(self, item: InventoryEntry):
        b = (
                int.to_bytes(item.on, 1)
                + item.type
                + int.to_bytes(item.count, 4, "little")
                + int.to_bytes(item.p_addr, 3, "little")
        )
        if item.p_addr != 0:
            b += int.to_bytes(0xE0)
        else:
            b += int.to_bytes(0x0)
        b += int.to_bytes(item.n_addr, 3, "little")
        if item.n_addr != 0:
            b += int.to_bytes(0xE0)
        await self.socket.write(message_format(WRITE, param_format(item.addr, b)))

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(GauntletLegendsContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        if cmd in {"Connected"}:
            self.slot = args["slot"]
            self.glslotdata = args["slot_data"]
            if self.socket.status():
                self.retro_connected = True
            else:
                raise Exception("Retroarch not detected. Please open you patched ROM in Retroarch.")
        elif cmd == "Retrieved":
            if "keys" not in args:
                logger.warning(f"invalid Retrieved packet to GLClient: {args}")
                return
            cc = None
            try:
                cc = self.stored_data.get(f"gl_cc_T{self.team}_P{self.slot}", None)
            except Exception:
                logger.info(traceback.format_exc())
            if cc is not None:
                logger.info("Received clear counts from server")
                self.clear_counts = cc
            else:
                self.clear_counts = {}
        elif cmd == "SetReply":
            logger.info(f"Updated: {args['key']} Value: {args['value']}")
        elif cmd == "LocationInfo":
            self.location_scouts = args["locations"]

    # Update inventory based on items received from server
    # Also adds starting items based on a few yaml options
    async def handle_items(self):
        compass = await self.item_from_name("Compass")
        if compass is not None:
            if self.glslotdata["character"] != 0:
                temp = await self.item_from_name(characters[self.glslotdata["character"] - 1])
                if temp is None:
                    await self.inv_update(characters[self.glslotdata["character"] - 1], 50)
            temp = await self.item_from_name("Key")
            if temp is None and self.glslotdata["keys"] == 1:
                await self.inv_update("Key", 9000)
            temp = await self.item_from_name("Speed Boots")
            if temp is None and self.glslotdata["speed"] == 1:
                await self.inv_update("Speed Boots", 2000)
            i = compass.count
            if i - 1 < len(self.items_received):
                for index in range(i - 1, len(self.items_received)):
                    item = self.items_received[index].item
                    await self.inv_update(items_by_id[item].item_name, base_count[items_by_id[item].item_name])
                await self.inv_update("Compass", len(self.items_received) + 1)

    # Read current timer in RAM
    async def read_time(self) -> int:
        return int.from_bytes(await self.socket.read(message_format(READ, f"0x{format(TIME, 'x')} 2")), "little")

    # Read player input values in RAM
    async def read_input(self) -> int:
        return int.from_bytes(await self.socket.read(message_format(READ, f"0x{format(INPUT, 'x')} 1")))

    # Read currently loaded level in RAM
    async def read_level(self) -> bytes:
        return await self.socket.read(message_format(READ, f"0x{format(ACTIVE_LEVEL, 'x')} 2"))

    # Read value that is 1 while a level is currently loading
    async def check_loading(self) -> bool:
        if self.in_portal or self.level_loading:
            return await self.read_time() == 0
        return False

    # Read number of loaded players in RAM
    async def active_players(self) -> int:
        temp = await self.socket.read(message_format(READ, f"0x{format(PLAYER_COUNT, 'x')} 1"))
        return temp[0]

    # Read level of player 1 in RAM
    async def player_level(self) -> int:
        temp = await self.socket.read(message_format(READ, f"0x{format(PLAYER_LEVEL, 'x')} 1"))
        return temp[0]

    # Update value at player count address
    # This directly impacts the difficulty of the level when it is loaded
    async def scale(self):
        level = await self.read_level()
        if self.movement != 0x12:
            level = [0x1, 0xF]
        players = await self.active_players()
        player_level = await self.player_level()
        max_value: int = self.glslotdata["max"]
        scale_value = min(max(((player_level - difficulty_convert[level[1]]) // 5), 0), 3)
        if self.glslotdata["instant_max"] == 1:
            scale_value = max_value
        mountain_value = min(player_level // 10, 3)
        await self.socket.write(
            message_format(WRITE, f"0x{format(PLAYER_COUNT, 'x')} 0x{format(min(players + scale_value, max_value) - mountain_value, 'x')}"),
        )
        self.scaled = True

    # Prepare locations that are going to be in the currently loading level
    async def scout_locations(self, ctx: "GauntletLegendsContext") -> None:
        level = await self.read_level()
        if level in boss_level:
            for i in range(4):
                await self.socket.write(
                    message_format(
                        WRITE,
                        param_format(
                            BOSS_ADDR, bytes([self.glslotdata["shards"][i][1], 0x0, self.glslotdata["shards"][i][0]]),
                        ),
                    ),
                )
        if self.movement != 0x12:
            level = [0x1, 0xF]
        self.current_level = level
        players = await self.active_players()
        if self.clear_counts.get(str(level), 0) != 0:
            self.difficulty = players + (0 if level[1] != 2 else min(await self.player_level() // 10, 3))
        else:
            self.difficulty = players
        _id = level[0]
        if level[1] == 1:
            _id = castle_id.index(level[0]) + 1
        raw_locations = [
            location for location in level_locations.get((level[1] << 4) + _id, []) if self.difficulty >= location.difficulty
        ]
        await ctx.send_msgs(
            [
                {
                    "cmd": "LocationScouts",
                    "locations": [
                        location.id
                        for location in raw_locations
                        if "Chest" not in location.name
                           and ("Barrel" not in location.name or "Barrel of Gold" in location.name)
                    ],
                    "create_as_hint": 0,
                },
            ],
        )
        while len(self.location_scouts) == 0:
            await asyncio.sleep(0.1)
        self.obelisks = [
            item
            for item in self.location_scouts
            if "Obelisk" in items_by_id.get(item.item, ItemData(0, "", ItemClassification.filler)).item_name
               and item.player == self.slot
        ]
        self.obelisk_locations = [
            location for location in raw_locations if location.id in [item.location for item in self.obelisks]
        ]
        self.item_locations = [
            location
            for location in raw_locations
            if "Chest" not in location.name
               and ("Barrel" not in location.name or "Barrel of Gold" in location.name)
               and location not in self.obelisk_locations
        ]
        self.chest_locations = [
            location
            for location in raw_locations
            if "Chest" in location.name
               or ("Barrel" in location.name and "Barrel of Gold" not in location.name)
               and location not in self.obelisk_locations
        ]
        max_value: int = self.glslotdata['max']
        logger.info(
            f"Locations: {len([location for location in self.obelisk_locations + self.item_locations + self.chest_locations if location.difficulty <= max_value and location.id not in self.locations_checked])} Difficulty: {max_value}",
        )

    # Compare values of loaded objects to see if they have been collected
    # Sends locations out to server based on object lists read in obj_read()
    # Local obelisks and mirror shards have special cases
    async def location_loop(self) -> List[int]:
        await self.obj_read()
        await self.obj_read(1)
        acquired = []
        for i, obj in enumerate(self.item_objects):
            if obj.raw[:2] == bytes([0xAD, 0xB]):
                if self.item_locations[i].id not in self.locations_checked:
                    self.locations_checked += [self.item_locations[i].id]
                    acquired += [self.item_locations[i].id]
        for j in range(len(self.obelisk_locations)):
            if await self.inv_bitwise("Obelisk", base_count[items_by_id[self.obelisks[j].item].item_name]):
                self.locations_checked += [self.obelisk_locations[j].id]
                acquired += [self.obelisk_locations[j].id]
        for k, obj in enumerate(self.chest_objects):
            if "Chest" in self.chest_locations[k].name:
                if obj.raw[:2] == bytes([0xAD, 0xB]):
                    if self.chest_locations[k].id not in self.locations_checked:
                        self.locations_checked += [self.chest_locations[k].id]
                        acquired += [self.chest_locations[k].id]
            else:
                if obj.raw[0x33] != 0:
                    if self.chest_locations[k].id not in self.locations_checked:
                        self.locations_checked += [self.chest_locations[k].id]
                        acquired += [self.chest_locations[k].id]
        if await self.dead():
            return []
        return acquired

    # Returns 1 if players are spinning in a portal
    async def portaling(self) -> int:
        temp = await self.socket.read(message_format(READ, f"0x{format(PLAYER_PORTAL, 'x')} 1"))
        return temp[0]

    # Returns a number that shows if the player currently has control or not
    async def limbo_check(self, offset=0) -> int:
        temp = await self.socket.read(message_format(READ, f"0x{format(PLAYER_MOVEMENT + offset, 'x')} 1"))
        return temp[0]

    # Returns True of the player is dead
    async def dead(self) -> bool:
        temp = await self.socket.read(message_format(READ, f"0x{format(PLAYER_ALIVE, 'x')} 1"))
        return temp[0] == 0x0

    # Returns a number that tells if the player is fighting a boss currently
    async def boss(self) -> int:
        temp = await self.socket.read(message_format(READ, f"0x{format(PLAYER_BOSSING, 'x')} 1"))
        return temp[0]

    # Checks if a player is currently exiting a level
    # Checks for both death and completion
    # Resets values since level is no longer being played
    async def level_status(self, ctx: "GauntletLegendsContext") -> bool:
        portaling = await self.portaling()
        dead = await self.dead()
        boss = await self.boss()
        if portaling or dead or (self.current_level in boss_level and boss == 0):
            if self.in_game:
                if portaling or (self.current_level in boss_level and boss == 0):
                    self.clear_counts[str(self.current_level)] = self.clear_counts.get(str(self.current_level), 0) + 1
                    if (self.current_level[1] << 4) + self.current_level[0] in mirror_levels:
                        await ctx.send_msgs(
                            [
                                {
                                    "cmd": "LocationChecks",
                                    "locations": [
                                        location.id
                                        for location in level_locations[
                                            (self.current_level[1] << 4) + self.current_level[0]
                                            ]
                                        if "Mirror" in location.name
                                    ],
                                },
                            ],
                        )
                if dead:
                    if self.current_level == bytes([0x2, 0xF]):
                        self.clear_counts[str([0x1, 0xF])] = max(self.clear_counts.get(str([0x1, 0xF]), 0) - 1, 0)
            self.objects_loaded = False
            self.extra_items = 0
            self.item_locations = []
            self.item_objects = []
            self.chest_locations = []
            self.chest_objects = []
            self.obelisk_locations = []
            self.obelisks = []
            self.in_game = False
            self.level_loading = False
            self.scaled = False
            self.offset = -1
            self.movement = 0
            self.difficulty = 0
            self.location_scouts = []
            return True
        return False

    # Prep arrays with locations and objects
    async def load_objects(self, ctx: "GauntletLegendsContext"):
        await self.scout_locations(ctx)
        await self.obj_read()
        await self.obj_read(1)
        self.objects_loaded = True

    def run_gui(self):
        from kvui import GameManager

        class GLManager(GameManager):
            logging_pairs = [("Client", "Archipelago")]
            base_title = "Archipelago Gauntlet Legends Client"

        self.ui = GLManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")


async def _patch_and_run_game(patch_file: str):
    metadata, output_file = Patch.create_rom_file(patch_file)


# Sends player items from server
# Checks for player status to see if they are in/loading a level
# Checks location status inside of levels
async def gl_sync_task(ctx: GauntletLegendsContext):
    logger.info("Starting N64 connector. Use /n64 for status information")
    while not ctx.exit_event.is_set():
        if ctx.retro_connected:
            cc_str: str = f"gl_cc_T{ctx.team}_P{ctx.slot}"
            try:
                ctx.set_notify(cc_str)
                if not ctx.auth:
                    ctx.retro_connected = False
                    continue
            except Exception:
                logger.info(traceback.format_exc())
            if ctx.limbo:
                try:
                    limbo = await ctx.limbo_check(0x78)
                    if limbo:
                        ctx.limbo = False
                        await asyncio.sleep(4)
                    else:
                        await asyncio.sleep(0.05)
                        continue
                except Exception:
                    logger.info(traceback.format_exc())
            try:
                await ctx.handle_items()
            except Exception:
                logger.info(traceback.format_exc())
            if not ctx.level_loading and not ctx.in_game:
                try:
                    if not ctx.in_portal:
                        ctx.in_portal = await ctx.portaling()
                    if ctx.in_portal and not ctx.init_refactor:
                        await asyncio.sleep(0.1)
                        ctx.movement = await ctx.limbo_check()
                        await ctx.inv_refactor()
                        ctx.init_refactor = True
                    ctx.level_loading = await ctx.check_loading()
                except Exception:
                    logger.info(traceback.format_exc())
            if ctx.level_loading:
                try:
                    ctx.in_portal = False
                    ctx.init_refactor = False
                    if not ctx.scaled:
                        logger.info("Scaling level...")
                        await asyncio.sleep(0.2)
                        await ctx.scale()
                    ctx.in_game = not await ctx.check_loading()
                except Exception:
                    logger.info(traceback.format_exc())
            if ctx.in_game:
                ctx.level_loading = False
                try:
                    if not ctx.objects_loaded:
                        logger.info("Loading Objects...")
                        await ctx.load_objects(ctx)
                        await asyncio.sleep(1)
                    if await ctx.level_status(ctx):
                        try:
                            await ctx.send_msgs(
                                [
                                    {
                                        "cmd": "Set",
                                        "key": cc_str,
                                        "default": {},
                                        "want_reply": True,
                                        "operations": [
                                            {
                                                "operation": "replace",
                                                "value": ctx.clear_counts,
                                            },
                                        ],
                                    },
                                ],
                            )
                        except Exception:
                            logger.info(traceback.format_exc())
                        ctx.limbo = True
                        await asyncio.sleep(0.05)
                        continue
                    checking = await ctx.location_loop()
                    if checking:
                        await ctx.send_msgs([{"cmd": "LocationChecks", "locations": checking}])
                    if not ctx.finished_game and await ctx.inv_bitwise("Hell", 0x100):
                        await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                except Exception:
                    logger.info(traceback.format_exc())
            await asyncio.sleep(0.1)
        else:
            await asyncio.sleep(1)
            continue


def launch():
    Utils.init_logging("GauntletLegendsClient", exception_logger="Client")

    async def main():
        parser = get_base_parser()
        parser.add_argument("patch_file", default="", type=str, nargs="?", help="Path to an APGL file")
        args = parser.parse_args()
        if args.patch_file:
            await asyncio.create_task(_patch_and_run_game(args.patch_file))
        ctx = GauntletLegendsContext(args.connect, args.password)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        ctx.gl_sync_task = asyncio.create_task(gl_sync_task(ctx), name="Gauntlet Legends Sync Task")

        await ctx.exit_event.wait()
        ctx.server_address = None

        await ctx.shutdown()

    import colorama

    colorama.init()

    asyncio.run(main())
    colorama.deinit()
