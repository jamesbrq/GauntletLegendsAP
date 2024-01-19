import timeit
import zlib
import io
import os

import Utils
import settings
from BaseClasses import MultiWorld, Item, Location
from worlds.Files import APDeltaPatch
from .Arrays import level_locations, level_size, level_address, item_dict


def get_base_rom_as_bytes() -> bytes:
    with open(get_base_rom_path("Gauntlet Legends (U) [!].z64"), "rb") as infile:
        base_rom_bytes = bytes(infile.read())

    return base_rom_bytes

def get_base_rom_path(file_name: str = "") -> str:
    options: settings.Settings = settings.get_settings()
    if not file_name:
        file_name = options["gl_options"]["rom_file"]
    if not os.path.exists(file_name):
        file_name = Utils.user_path(file_name)
    return file_name


class GLDeltaPatch(APDeltaPatch):
    game = "Gauntlet Legends"
    hash = "9cb963e8b71f18568f78ec1af120362e"
    patch_file_ending = ".apgl"
    result_file_ending = ".z64"

    @classmethod
    def get_source_data(cls) -> bytes:
        return get_base_rom_as_bytes()


def zdec(data):
    """
    Decompresses zlib archives used in Midway titles.
    """
    decomp = zlib.decompressobj(-zlib.MAX_WBITS)
    output = bytearray()
    for i in range(0, len(data), 256):
        print("looping")
        output.extend(decomp.decompress(data[i:i + 256]))
    print("flushing")
    output.extend(decomp.flush())
    print("returning")
    return output


def zenc(data):
    """
    Headerless zlib encoding scheme used across games.
    Note you get much better compression routing through gzip
    and stripping off the header and CRC.
    """
    compress = zlib.compressobj(zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, -zlib.MAX_WBITS)
    output = bytearray()
    for i in range(0, len(data), 256):
        output.extend(compress.compress(data[i:i + 256]))
    output.extend(compress.flush())
    return output


class Rom:
    def __init__(self, world: MultiWorld, player: int):
        with open("Gauntlet Legends (U) [!].z64", 'rb') as file:
            content = file.read()
        self.random = world.per_slot_randoms[player]
        self.stream = io.BytesIO(content)
        self.world = world
        self.player = player

    def crc32(self, chunk_size=1024):
        crc32_checksum = 0
        while True:
            chunk = self.stream.read(chunk_size)
            if not chunk:
                break
            crc32_checksum = zlib.crc32(chunk, crc32_checksum)
        return format(crc32_checksum& 0xFFFFFFFF, 'x')

    def write_items(self):
        for i, level in enumerate(level_locations.values()):
            self.stream.seek(level_address[i], 0)
            data = io.BytesIO(zdec(self.stream.read(level_size[i])))
            data.seek(0x62, 0)
            for location in level:
                location = self.world.get_location(location.name, self.player)
                data.write(bytes(item_dict[location.item.code]))
                data.seek(10, 1)
            self.stream.seek(level_address[i], 0)
            self.stream.write(zenc(data.getvalue()))

    def close(self, path):
        print("closing")
        output_path = os.path.join(path,
                                   f"AP_{self.world.seed_name}_P{self.player}_{self.world.player_name[self.player]}.z64")
        with open(output_path, 'wb') as outfile:
            outfile.write(self.stream.getvalue())
        patch = GLDeltaPatch(os.path.splitext(output_path)[0] + ".apgl", player=self.player,
                             player_name=self.world.player_name[self.player], patched_path=output_path)
        patch.write()
        os.unlink(output_path)
        self.stream.close()
