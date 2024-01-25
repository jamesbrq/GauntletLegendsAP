import typing

from BaseClasses import MultiWorld, Region, Entrance
from worlds.AutoWorld import World
from .Locations import GLLocation, valleyOfFire, daggerPeak, cliffsOfDesolation, lostCave, volcanicCavern \
    , dragonsLair, castleCourtyard, dungeonOfTorment, towerArmory \
    , castleTreasury, chimerasKeep, poisonedFields, hauntedCemetery \
    , venomousSpire, toxicAirShip, arcticDocks, frozenCamp \
    , crystalMine, eruptingFissure, desecratedTemple \
    , battleTrenches, battleTowers, infernalFortress \
    , gatesOfTheUnderworld


def create_regions(world: "World"):
    world.multiworld.regions.append(Region("Menu", world.player, world.multiworld))

    create_region(world, "Valley of Fire", valleyOfFire)

    create_region(world, "Dagger Peak", daggerPeak)

    create_region(world, "Cliffs of Desolation", cliffsOfDesolation)

    create_region(world, "Lost Cave", lostCave)

    create_region(world, "Volcanic Caverns", volcanicCavern)

    create_region(world, "Dragon's Lair", dragonsLair)

    create_region(world, "Castle Courtyard", castleCourtyard)

    create_region(world, "Dungeon of Torment", dungeonOfTorment)

    create_region(world, "Tower Armory", towerArmory)

    create_region(world, "Castle Treasury", castleTreasury)

    create_region(world, "Chimera's Keep", chimerasKeep)

    create_region(world, "Poisonous Fields", poisonedFields)

    create_region(world, "Haunted Cemetery", hauntedCemetery)

    create_region(world, "Venomous Spire", venomousSpire)

    create_region(world, "Toxic Air Ship", toxicAirShip)

    create_region(world, "Arctic Docks", arcticDocks)

    create_region(world, "Frozen Camp", frozenCamp)

    create_region(world, "Crystal Mine", crystalMine)

    create_region(world, "Erupting Fissure", eruptingFissure)

    create_region(world, "Desecrated Temple", desecratedTemple)

    create_region(world, "Battle Trenches", battleTrenches)

    create_region(world, "Battle Towers", battleTowers)

    create_region(world, "Infernal Fortress", infernalFortress)

    create_region(world, "Gates of the Underworld", gatesOfTheUnderworld)

def runestoneCount(state, player):
    count = 0
    for i in range(1, 14):
        if state.has(f"Runestone {i}", player):
            count += 1
    return count


def connect_regions(world: "World"):
    names: typing.Dict[str, int] = {}

    connect(world, names, "Menu", "Valley of Fire")
    connect(world, names, "Menu", "Dagger Peak")
    connect(world, names, "Menu", "Cliffs of Desolation")
    connect(world, names, "Menu", "Lost Cave")
    connect(world, names, "Menu", "Volcanic Caverns")
    connect(world, names, "Menu", "Dragon's Lair")
    connect(world, names, "Dragon's Lair", "Castle Courtyard", lambda state: runestoneCount(state, world.player) >= 3)
    connect(world, names, "Castle Courtyard", "Dungeon of Torment")
    connect(world, names, "Castle Courtyard", "Tower Armory")
    connect(world, names, "Castle Courtyard", "Castle Treasury")
    connect(world, names, "Castle Courtyard", "Chimera's Keep")
    connect(world, names, "Chimera's Keep", "Poisonous Fields", lambda state: runestoneCount(state, world.player) >= 6)
    connect(world, names, "Poisonous Fields", "Haunted Cemetery")
    connect(world, names, "Poisonous Fields", "Venomous Spire")
    connect(world, names, "Poisonous Fields", "Toxic Air Ship")
    connect(world, names, "Toxic Air Ship", "Arctic Docks", lambda state: runestoneCount(state, world.player) >= 9)
    connect(world, names, "Arctic Docks", "Frozen Camp")
    connect(world, names, "Arctic Docks", "Crystal Mine")
    connect(world, names, "Arctic Docks", "Erupting Fissure")
    connect(world, names, "Erupting Fissure", "Desecrated Temple", lambda state: runestoneCount(state, world.player) >= 12)
    connect(world, names, "Desecrated Temple", "Battle Trenches")
    connect(world, names, "Desecrated Temple", "Battle Towers")
    connect(world, names, "Desecrated Temple", "Infernal Fortress")
    connect(world, names, "Infernal Fortress", "Gates of the Underworld",
            lambda state: state.has("Runestone 1", world.player) and state.has("Runestone 2", world.player)
            and state.has("Runestone 3", world.player) and state.has("Runestone 4", world.player)
            and state.has("Runestone 5", world.player) and state.has("Runestone 6", world.player)
            and state.has("Runestone 7", world.player) and state.has("Runestone 8", world.player)
            and state.has("Runestone 9", world.player) and state.has("Runestone 10", world.player)
            and state.has("Runestone 11", world.player) and state.has("Runestone 12", world.player)
            and state.has("Runestone 13", world.player))


def create_region(world: "World", name, locations):
    ret = Region(name, world.player, world.multiworld)
    for location in locations:
        loc = GLLocation(world.player, location.name, location.id, ret)
        ret.locations.append(loc)
    world.multiworld.regions.append(ret)


def connect(world: "World", used_names: typing.Dict[str, int], source: str, target: str,
            rule: typing.Optional[typing.Callable] = None):
    source_region = world.multiworld.get_region(source, world.player)
    target_region = world.multiworld.get_region(target, world.player)

    if target not in used_names:
        used_names[target] = 1
        name = target
    else:
        used_names[target] += 1
        name = target + (' ' * used_names[target])

    connection = Entrance(world.player, name, source_region)

    if rule:
        connection.access_rule = rule

    source_region.exits.append(connection)
    connection.connect(target_region)
