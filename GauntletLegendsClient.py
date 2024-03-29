import asyncio
import multiprocessing
import os
import socket
import subprocess
import traceback
import typing
import zipfile

import bsdiff4

import Patch
import Utils
from CommonClient import CommonContext, server_loop, gui_enabled, ClientCommandProcessor, logger, \
    get_base_parser
from typing import List, cast, Dict, Optional, Any

from NetUtils import NetworkItem, ClientStatus
from worlds.gauntlet_legends.Arrays import inv_dict, timers, base_count, levels, castle_id, level_locations, \
    difficulty_convert
from worlds.gauntlet_legends.Rom import get_base_rom_path
from worlds.gauntlet_legends.Items import items_by_id
from worlds.gauntlet_legends.Locations import LocationData

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
PLAYER_MOVEMENT = 0xFD307
TIME = 0xC5B1C
INPUT = 0xC5BCD


class RetroSocket:
    def __init__(self):
        self.host = "localhost"
        self.port = 55355
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, message: str):
        self.socket.sendto(message.encode(), (self.host, self.port))

    def read(self, message) -> bytes | None:
        self.socket.sendto(message.encode(), (self.host, self.port))

        self.socket.settimeout(2)
        try:
            data, addr = self.socket.recvfrom(30000)
        except socket.timeout:
            raise Exception("Socket receive timed out. No data received within the specified timeout.")
        except ConnectionResetError:
            raise Exception("Retroarch is not open. Please open Retroarch and load the correct ROM.")
        response = data.decode().split(' ')
        b = bytes()
        for s in response[2:]:
            if "-1" in s:
                logger.info("-1 response")
                return None
            b += bytes.fromhex(s)
        return b

    def crc32(self):
        message = "GET_STATUS"
        self.socket.sendto(message.encode(), (self.host, self.port))
        try:
            data, addr = self.socket.recvfrom(1000)
        except ConnectionResetError:
            raise Exception("Retroarch not detected. Please make sure your ROM is open in Retroarch.")
        data = data.decode()
        return data[data.find("crc32=") + len("crc32="):-1]


class RamChunk:
    def __init__(self, arr: bytes):
        self.raw = arr
        self.split = []

    def iterate(self, length: int):
        self.split = [self.raw[i:i + length] for i in range(0, len(self.raw), length)]


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
            self.count: int = int.from_bytes(arr[4:8], 'little')
            self.n_addr: int = int.from_bytes(arr[12:15], 'little')
            self.p_addr: int = int.from_bytes(arr[8:11], 'little')
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


def MessageFormat(arg: str, params: str) -> str:
    return f"{arg} {params}"


def ParamFormat(adr: int, arr: bytes) -> str:
    return ' '.join([hex(adr)] + [f'0x{byte:02X}' for byte in arr])


class GauntletLegendsCommandProcessor(ClientCommandProcessor):
    def __init__(self, ctx: CommonContext):
        super().__init__(ctx)

    def _cmd_n64(self):
        """Check NES Connection State"""
        if isinstance(self.ctx, GauntletLegendsContext):
            logger.info(f"N64 Status: {True}")

    def _cmd_inv(self, *args):
        self.ctx.inv_update(' '.join(args[:-1]), int(args[-1]))

    def _cmd_connected(self):
        logger.info(f"Retroarch Status: {self.ctx.retro_connected}")


class GauntletLegendsContext(CommonContext):
    command_processor = GauntletLegendsCommandProcessor
    game = 'Gauntlet Legends'
    items_handling = 0b101  # full remote

    def __init__(self, server_address, password):
        super().__init__(server_address, password)
        self.gl_sync_task = None
        self.received_index: int = 0
        self.glslotdata = None
        self.crc32 = None
        self.socket = RetroSocket()
        self.awaiting_rom = False
        self.inventory: List[InventoryEntry] = []
        self.inventory_raw: RamChunk = None
        self.current_objects: List[ObjectEntry] = []
        self.retro_connected: bool = False
        self.level_loading: bool = False
        self.in_game: bool = False
        self.objects_loaded: bool = False
        self.current_locations: List[LocationData] = []
        self.checked_locations_arr: List[LocationData] = []
        self.limbo: bool = False
        self.in_portal: bool = False
        self.scaled: bool = False
        self.offset: int = -1
        self.clear_counts = None
        self.current_level: bytes = bytes()
        self.movement: int = 0
        self.init_refactor: bool = False

    def inv_count(self):
        return len(self.inventory)

    def inv_read(self):
        _inv: List[InventoryEntry] = []
        b = RamChunk(self.socket.read(MessageFormat(READ, f"0x{format(INV_ADDR, 'x')} 1024")))
        if b is None:
            return
        b.iterate(0x10)
        self.inventory_raw = b
        for i, arr in enumerate(b.split):
            _inv += [InventoryEntry(arr, i)]
        new_inv: List[InventoryEntry] = []
        new_inv += [_inv[0]]
        addr = new_inv[0].n_addr
        while True:
            if addr == 0:
                break
            new_inv += [inv for inv in _inv if inv.addr == addr]
            addr = new_inv[-1].n_addr
        self.inventory = new_inv

    def item_from_name(self, name: str) -> InventoryEntry | None:
        self.inv_read()
        for i in range(0, self.inv_count()):
            if self.inventory[i].name == name:
                return self.inventory[i]
        return None

    def inv_bitwise(self, name: str, bit: int) -> bool:
        item = self.item_from_name(name)
        if item is None:
            return False
        return item.count & bit != 0

    def get_obj_addr(self) -> int:
        return (int.from_bytes(self.socket.read(MessageFormat(READ, f"0x{format(OBJ_ADDR, 'x')} 4")), 'little') + (0x3C * 0x2A)) & 0xFFFFF

    def obj_read(self) -> List[ObjectEntry]:
        obj_address = self.get_obj_addr()
        _obj = []
        b = RamChunk(self.socket.read(MessageFormat(READ, f"0x{format(obj_address + ((0 if self.offset == -1 else self.offset) * 0x3C), 'x')} 6720")))
        b.iterate(0x3C)
        for i, arr in enumerate(b.split):
            if self.offset != -1:
                if arr[0] != 0xFF:
                    _obj += [ObjectEntry(arr)]
                continue
            if arr[0] != 0xFF:
                if self.offset == -1:
                    self.offset = i
                _obj += [ObjectEntry(arr)]
        return _obj

    def inv_update(self, name: str, count: int):
        self.inv_read()
        if "Runestone" in name:
            name = "Runestone"
        if "Fruit" in name or "Meat" in name:
            name = "Health"
        for item in self.inventory:
            if item.name == name:
                zero = item.count == 0
                if name in timers:
                    count *= 96
                if "Compass" in name:
                    item.count = count
                elif "Health" in name:
                    item.count = min(item.count + count, self.item_from_name("Max").count)
                elif "Runestone" in name:
                    item.count |= count
                else:
                    item.count += count
                self.write_inv(item)
                if zero:
                    self.inv_refactor()
                return
        logger.info(f"Adding new item to inv: {name}")
        self.inv_add(name, count)

    def inv_refactor(self, new=None):
        self.inv_read()
        if new is not None:
            self.inventory += [new]
        for i, item in enumerate(self.inventory):
            if item.name is not None:
                if "Potion" in item.name and item.count != 0:
                    self.socket.write(MessageFormat(WRITE, ParamFormat(ACTIVE_POTION,
                                                                       int.to_bytes(item.type[2] // 0x10, 1,
                                                                                    'little'))))
            if i == 0:
                item.p_addr = 0
                item.n_addr = item.addr + 0x10
                item.addr = INV_ADDR
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

        self.socket.write(MessageFormat(WRITE, ParamFormat(INV_UPDATE_ADDR,
                                                           int.to_bytes(self.inventory[-1].addr, 3,
                                                                        'little'))))
        self.socket.write(
            MessageFormat(WRITE, ParamFormat(INV_LAST_ADDR, int.to_bytes(self.inventory[-1].addr + 0x10, 3, 'little'))))

        for item in self.inventory:
            self.write_inv(item)
        for i, raw in enumerate(self.inventory_raw.split[len(self.inventory):], len(self.inventory)):
            item = InventoryEntry(raw, i)
            if item.type != bytes([0, 0, 0]):
                self.write_inv(InventoryEntry(bytes([0, 0, 0, 0, 0, 0, 0, 0]) + int.to_bytes(item.addr + 0x10, 3, 'little') + bytes([0xE0, 0, 0, 0, 0]), i))


        self.socket.write(f"{WRITE} 0xC6BF0 0x{format(self.inv_count(), 'x')}")

    def inv_add(self, name: str, count: int):
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
        self.inv_refactor(new)

    def write_inv(self, item: InventoryEntry):
        b = int.to_bytes(item.on, 1) + item.type + int.to_bytes(item.count, 4, 'little') + int.to_bytes(item.p_addr, 3,
                                                                                                     'little')
        if item.p_addr != 0:
            b += int.to_bytes(0xE0)
        else:
            b += int.to_bytes(0x0)
        b += int.to_bytes(item.n_addr, 3, 'little')
        if item.n_addr != 0:
            b += int.to_bytes(0xE0)
        self.socket.write(MessageFormat(WRITE, ParamFormat(item.addr, b)))

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(GauntletLegendsContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        if cmd in {"Connected"}:
            self.slot = args['slot']
            self.glslotdata = args['slot_data']
            if self.glslotdata["crc32"] == self.socket.crc32():
                self.retro_connected = True
            else:
                logger.info(self.glslotdata["crc32"])
                logger.info(self.socket.crc32())
                raise Exception("The loaded ROM is incorrect. Please load your patched ROM of Gauntlet Legends")
        elif cmd == "Retrieved":
            if "keys" not in args:
                logger.warning(f"invalid Retrieved packet to GLClient: {args}")
                return
            cc = None
            try:
                cc = self.stored_data.get(f"gl_cc_T{self.team}_P{self.slot}", None)
            except Exception as e:
                logger.info(traceback.format_exc())
            if cc is not None:
                logger.info("Received clear counts from server")
                self.clear_counts = cc
            else:
                self.clear_counts = {}
        elif cmd == "SetReply":
            logger.info(f"Updated: {args['key']} Value: {args['value']}")

    def handle_items(self):
        item = self.item_from_name("Compass")
        if item is not None:
            i = item.count
            if i - 1 != len(self.items_received):
                for index in range(i - 1, len(self.items_received)):
                    item = self.items_received[index].item
                    self.inv_update(items_by_id[item].itemName, base_count[items_by_id[item].itemName])
            j = self.item_from_name("Compass")
            if j is not None:
                j = j.count
                if j == i:
                    self.inv_update("Compass", len(self.items_received) + 1)
            else:
                return

    def read_time(self) -> int:
        return int.from_bytes(self.socket.read(MessageFormat(READ, f"0x{format(TIME, 'x')} 2")), "little")

    def read_input(self) -> int:
        return int.from_bytes(self.socket.read(MessageFormat(READ, f"0x{format(INPUT, 'x')} 1")))

    def read_level(self) -> bytes:
        return self.socket.read(MessageFormat(READ, f"0x{format(ACTIVE_LEVEL, 'x')} 2"))

    def check_loading(self) -> bool:
        if self.in_portal or self.level_loading:
            return self.read_time() == 0
        return False

    def active_players(self) -> int:
        return self.socket.read(MessageFormat(READ, f"0x{format(PLAYER_COUNT, 'x')} 1"))[0]

    def player_level(self) -> int:
        return self.socket.read(MessageFormat(READ, f"0x{format(PLAYER_LEVEL, 'x')} 1"))[0]

    def scale(self):
        level = self.read_level()
        if self.movement is not 0x12:
            level = [0x1, 0xF]
        players = self.active_players()
        player_level = self.player_level()
        scale_value = min(self.clear_counts.get(str(level), 0), 3) if self.glslotdata["scale"] == 1 else min(max(((player_level - difficulty_convert[level[1]]) // 5), 0), 3)
        if level[1] == 2 and self.clear_counts.get(str(level), 0) != 0:
            scale_value -= min(player_level // 10, 3)
        self.socket.write(MessageFormat(WRITE, f"0x{format(PLAYER_COUNT, 'x')} 0x{format(min(players + scale_value, 4), 'x')}"))
        self.scaled = True

    def scout_locations(self) -> List[LocationData]:
        level = self.read_level()
        if self.movement is not 0x12:
            level = [0x1, 0xF]
        self.current_level = level
        if self.clear_counts.get(str(level), 0) != 0:
            difficulty = self.active_players() + (0 if level[1] != 2 else min(self.player_level() // 10, 3))
        else:
            difficulty = self.active_players()
        _id = level[0]
        if level[1] == 1:
            _id = castle_id.index(level[0]) + 1
        raw_locations = level_locations.get((level[1] << 4) + _id, [])
        locations = []
        for location in raw_locations:
            if location.difficulty <= difficulty:
                locations += [location]
        logger.info(f"Locations: {len(locations)} Difficulty: {difficulty}")
        return locations

    def location_loop(self) -> List[int]:
        new_objects = self.obj_read()[:len(self.current_locations)]
        acquired = []
        for i, obj in enumerate(new_objects):
            if obj.raw[:2] == bytes([0xAD, 0xB]):
                if self.current_locations[i] not in self.locations_checked:
                    self.locations_checked.add(self.current_locations[i].id)
                    acquired += [self.current_locations[i].id]
        if self.dead():
            return []
        return acquired

    def portaling(self) -> int:
        return self.socket.read(MessageFormat(READ, f"0x{format(PLAYER_PORTAL, 'x')} 1"))[0]

    def limbo_check(self, offset=0) -> int:
        return self.socket.read(MessageFormat(READ, f"0x{format(PLAYER_MOVEMENT + offset, 'x')} 1"))[0]

    def dead(self) -> bool:
        return self.socket.read(MessageFormat(READ, f"0x{format(PLAYER_ALIVE, 'x')} 1"))[0] == 0x0

    def level_status(self) -> bool:
        portaling = self.portaling()
        dead = self.dead()
        if portaling or dead:
            if self.in_game:
                if portaling:
                    self.clear_counts[str(self.current_level)] = self.clear_counts.get(str(self.current_level), 0) + 1
                if dead:
                    if self.current_level == bytes([0x2, 0xF]):
                        self.clear_counts[str([0x1, 0xF])] = max(self.clear_counts.get(str([0x1, 0xF]), 0) - 1, 0)
            self.objects_loaded = False
            self.current_objects = []
            self.current_locations = []
            self.in_game = False
            self.level_loading = False
            self.scaled = False
            self.offset = -1
            self.movement = 0
            return True
        return False

    def load_objects(self):
        self.current_locations = self.scout_locations()
        self.current_objects = self.obj_read()
        self.objects_loaded = True

    def run_gui(self):
        from kvui import GameManager

        class GLManager(GameManager):
            logging_pairs = [
                ("Client", "Archipelago")
            ]
            base_title = "Archipelago Gauntlet Legends Client"

        self.ui = GLManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")


async def _patch_and_run_game(patch_file: str):
    metadata, output_file = Patch.create_rom_file(patch_file)


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
            except Exception as e:
                logger.info(traceback.format_exc())
            if ctx.limbo:
                try:
                    limbo = ctx.limbo_check(0x78)
                    if limbo:
                        ctx.limbo = False
                        await asyncio.sleep(4)
                    else:
                        await asyncio.sleep(.05)
                        continue
                except Exception as e:
                    logger.info(traceback.format_exc())
            try:
                ctx.handle_items()
            except Exception as e:
                logger.info(traceback.format_exc())
            if not ctx.level_loading and not ctx.in_game:
                try:
                    if not ctx.in_portal:
                        ctx.in_portal = ctx.portaling()
                    if ctx.in_portal and not ctx.init_refactor:
                        await asyncio.sleep(.1)
                        ctx.movement = ctx.limbo_check()
                        ctx.inv_refactor()
                        ctx.init_refactor = True
                    ctx.level_loading = ctx.check_loading()
                except Exception as e:
                    logger.info(traceback.format_exc())
            if ctx.level_loading:
                try:
                    ctx.in_portal = False
                    ctx.init_refactor = False
                    if not ctx.scaled:
                        logger.info("Scaling level...")
                        await asyncio.sleep(.2)
                        ctx.scale()
                    ctx.in_game = not ctx.check_loading()
                except Exception as e:
                    logger.info(traceback.format_exc())
            if ctx.in_game:
                ctx.level_loading = False
                try:
                    if not ctx.objects_loaded:
                        logger.info("Loading Objects...")
                        ctx.load_objects()
                        await asyncio.sleep(1)
                    if ctx.level_status():
                        try:
                            await ctx.send_msgs([{
                                "cmd": "Set",
                                "key": cc_str,
                                "default": {},
                                "want_reply": True,
                                "operations": [{
                                    "operation": "replace",
                                    "value": ctx.clear_counts,
                                }],
                            }])
                        except Exception as e:
                            logger.info(traceback.format_exc())
                        ctx.limbo = True
                        await asyncio.sleep(.05)
                        continue
                    checking = ctx.location_loop()
                    if checking:
                        await ctx.send_msgs([{"cmd": "LocationChecks", "locations": checking}])
                    if not ctx.finished_game and ctx.inv_bitwise("Hell", 0x100):
                        await ctx.send_msgs([{
                            "cmd": "StatusUpdate",
                            "status": ClientStatus.CLIENT_GOAL
                        }])
                except Exception as e:
                    logger.info(traceback.format_exc())
            await asyncio.sleep(.1)
        else:
            await asyncio.sleep(1)
            continue


def launch():
    Utils.init_logging("GLClient", exception_logger="Client")

    async def main():
        parser = get_base_parser()
        parser.add_argument("patch_file", default="", type=str, nargs="?",
                            help="Path to an APGL file")
        args = parser.parse_args()
        if args.patch_file:
            asyncio.create_task(_patch_and_run_game(args.patch_file))
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
