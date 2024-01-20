import typing

from BaseClasses import MultiWorld, Region, Entrance
from .Locations import GLLocation, valleyOfFire, daggerPeak, cliffsOfDesolation, lostCave, volcanicCavern \
    , dragonsLair, castleCourtyard, dungeonOfTorment, towerArmory \
    , castleTreasury, chimerasKeep, poisonedFields, hauntedCemetery \
    , venomousSpire, toxicAirShip, arcticDocks, frozenCamp \
    , crystalMine, eruptingFissure, desecratedTemple \
    , battleTrenches, battleTowers, infernalFortress \
    , gatesOfTheUnderworld


def create_regions(world: MultiWorld, player: int):
    menu_region = Region("Menu", player, world)
    world.regions.append(menu_region)

    mountain1_region = create_region(world, player, "Valley of Fire", valleyOfFire)
    world.regions.append(mountain1_region)

    mountain2_region = create_region(world, player, "Dagger Peak", daggerPeak)
    world.regions.append(mountain2_region)

    mountain3_region = create_region(world, player, "Cliffs of Desolation", cliffsOfDesolation)
    world.regions.append(mountain3_region)

    mountain4_region = create_region(world, player, "Lost Cave", lostCave)
    world.regions.append(mountain4_region)

    mountain5_region = create_region(world, player, "Volcanic Caverns", volcanicCavern)
    world.regions.append(mountain5_region)

    mountain6_region = create_region(world, player, "Dragon's Lair", dragonsLair)
    world.regions.append(mountain6_region)

    castle1_region = create_region(world, player, "Castle Courtyard", castleCourtyard)
    world.regions.append(castle1_region)

    castle2_region = create_region(world, player, "Dungeon of Torment", dungeonOfTorment)
    world.regions.append(castle2_region)

    castle3_region = create_region(world, player, "Tower Armory", towerArmory)
    world.regions.append(castle3_region)

    castle4_region = create_region(world, player, "Castle Treasury", castleTreasury)
    world.regions.append(castle4_region)

    castle5_region = create_region(world, player, "Chimera's Keep", chimerasKeep)
    world.regions.append(castle5_region)

    town1_region = create_region(world, player, "Poisonous Fields", poisonedFields)
    world.regions.append(town1_region)

    town2_region = create_region(world, player, "Haunted Cemetery", hauntedCemetery)
    world.regions.append(town2_region)

    town3_region = create_region(world, player, "Venomous Spire", venomousSpire)
    world.regions.append(town3_region)

    town4_region = create_region(world, player, "Toxic Air Ship", toxicAirShip)
    world.regions.append(town4_region)

    ice1_region = create_region(world, player, "Arctic Docks", arcticDocks)
    world.regions.append(ice1_region)

    ice2_region = create_region(world, player, "Frozen Camp", frozenCamp)
    world.regions.append(ice2_region)

    ice3_region = create_region(world, player, "Crystal Mine", crystalMine)
    world.regions.append(ice3_region)

    ice4_region = create_region(world, player, "Erupting Fissure", eruptingFissure)
    world.regions.append(ice4_region)

    temple_region = create_region(world, player, "Desecrated Temple", desecratedTemple)
    world.regions.append(temple_region)

    battle1_region = create_region(world, player, "Battle Trenches", battleTrenches)
    world.regions.append(battle1_region)

    battle2_region = create_region(world, player, "Battle Towers", battleTowers)
    world.regions.append(battle2_region)

    battle3_region = create_region(world, player, "Infernal Fortress", infernalFortress)
    world.regions.append(battle3_region)

    underworld_region = create_region(world, player, "Gates of the Underworld", gatesOfTheUnderworld)
    world.regions.append(underworld_region)

def runestoneCount(state, player):
    count = 0
    for i in range(1, 14):
        if state.has(f"Runestone {i}", player):
            count += 1
    return count


def connect_regions(world: MultiWorld, player: int):
    names: typing.Dict[str, int] = {}

    connect(world, player, names, "Menu", "Valley of Fire")
    connect(world, player, names, "Menu", "Dagger Peak")
    connect(world, player, names, "Menu", "Cliffs of Desolation")
    connect(world, player, names, "Menu", "Lost Cave")
    connect(world, player, names, "Menu", "Volcanic Caverns")
    connect(world, player, names, "Menu", "Dragon's Lair")
    connect(world, player, names, "Dragon's Lair", "Castle Courtyard", lambda state: runestoneCount(state, player) >= 3)
    connect(world, player, names, "Castle Courtyard", "Dungeon of Torment")
    connect(world, player, names, "Castle Courtyard", "Tower Armory")
    connect(world, player, names, "Castle Courtyard", "Castle Treasury")
    connect(world, player, names, "Castle Courtyard", "Chimera's Keep")
    connect(world, player, names, "Chimera's Keep", "Poisonous Fields", lambda state: runestoneCount(state, player) >= 6)
    connect(world, player, names, "Poisonous Fields", "Haunted Cemetery")
    connect(world, player, names, "Poisonous Fields", "Venomous Spire")
    connect(world, player, names, "Poisonous Fields", "Toxic Air Ship")
    connect(world, player, names, "Toxic Air Ship", "Arctic Docks", lambda state: runestoneCount(state, player) >= 9)
    connect(world, player, names, "Arctic Docks", "Frozen Camp")
    connect(world, player, names, "Arctic Docks", "Crystal Mine")
    connect(world, player, names, "Arctic Docks", "Erupting Fissure")
    connect(world, player, names, "Erupting Fissure", "Desecrated Temple", lambda state: runestoneCount(state, player) >= 12)
    connect(world, player, names, "Desecrated Temple", "Battle Trenches")
    connect(world, player, names, "Desecrated Temple", "Battle Towers")
    connect(world, player, names, "Desecrated Temple", "Infernal Fortress")
    connect(world, player, names, "Infernal Fortress", "Gates of the Underworld",
            lambda state: state.has("Runestone 1", player) and state.has("Runestone 2", player)
            and state.has("Runestone 3", player) and state.has("Runestone 4", player)
            and state.has("Runestone 5", player) and state.has("Runestone 6", player)
            and state.has("Runestone 7", player) and state.has("Runestone 8", player)
            and state.has("Runestone 9", player) and state.has("Runestone 10", player)
            and state.has("Runestone 11", player) and state.has("Runestone 12", player)
            and state.has("Runestone 13", player))


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
