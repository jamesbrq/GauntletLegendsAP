import typing

from BaseClasses import MultiWorld, Region, Entrance
from .Locations import GLLocation, valleyOfFire, daggerPeak


def create_regions(world: MultiWorld, player: int):
    menu_region = Region("Menu", player, world)
    world.regions.append(menu_region)

    mountain1_region = create_region(world, player, "Mountain1", valleyOfFire)
    world.regions.append(mountain1_region)

    mountain2_region = create_region(world, player, "Mountain2", daggerPeak)
    world.regions.append(mountain2_region)


def connect_regions(world: MultiWorld, player: int):
    names: typing.Dict[str, int] = {}

    connect(world, player, names, "Menu", "Mountain1")
    connect(world, player, names, "Mountain1", "Mountain2", lambda state: state.has("Key", player))


def create_region(world, player, name, locations):
    ret = Region(name, player, world)
    for location in locations:
        print(location.name)
        loc = GLLocation(player, location.name, location.id, ret)
        ret.locations.append(loc)
    return ret


def connect(world: MultiWorld, player: int, used_names: typing.Dict[str, int], source: str, target: str,
            rule: typing.Optional[typing.Callable] = None):
    source_region = world.get_region(source, player)
    target_region = world.get_region(target, player)

    if target not in used_names:
        used_names[target] = 1
        name = target
    else:
        used_names[target] += 1
        name = target + (' ' * used_names[target])

    connection = Entrance(player, name, source_region)

    if rule:
        connection.access_rule = rule

    source_region.exits.append(connection)
    connection.connect(target_region)
