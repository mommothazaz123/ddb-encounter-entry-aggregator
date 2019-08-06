import collections
import json

import aiohttp

API_BASE = "https://www.dndbeyond.com/character/"
STANDARD_ARRAY = {8, 10, 12, 13, 14, 15}
REQUIRED_LEVEL = 3
ALLOWED_RACES = [
    'Dragonborn', 'Mountain Dwarf', 'Hill Dwarf', 'High Elf', 'Wood Elf', 'Rock Gnome', 'Half-Elf',
    'Stout Halfling', 'Lightfoot Halfling', 'Half-Orc', 'Human', 'Variant Human', 'Tiefling'
]
ALLOWED_CLASSES = [
    'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter', 'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer', 'Warlock',
    'Wizard'
]
ALLOWED_SUBCLASSES = [
    'Path of the Berserker', 'College of Lore', 'Life Domain', 'Circle of the Land', 'Champion', 'Way of the Open Hand',
    'Oath of Devotion', 'Hunter', 'Thief', 'Draconic Bloodline', 'The Fiend', 'School of Evocation'
]
ALLOWED_FEATS = ["Grappler"]
ALLOWED_BACKGROUNDS = ["Acolyte", "Criminal / Spy", "Folk Hero", "Noble", "Sage", "Soldier", "Custom"]
with open('spells.json') as f:
    ALLOWED_SPELLS = json.load(f)


async def validate_character(char_id):
    character = None
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}{char_id}/json") as resp:
            print(resp.status)
            if resp.status == 200:
                character = await resp.json()
            else:
                raise ExternalImportError(f"{resp.status} - {resp.reason}")

    warnings = []
    # stats
    stats = set(s['value'] for s in character['stats'])
    if not stats == STANDARD_ARRAY:
        warnings.append(f"Stats not standard array: {[s['value'] for s in character['stats']]}")

    # race
    race = character['race']['fullName']
    if race not in ALLOWED_RACES:
        warnings.append(f"Disallowed race: {race}")

    # class
    classes = []
    levels = collections.defaultdict(lambda: 0)
    for _class in character.get('classes', []):
        class_name = level_name = _class.get('definition', {}).get('name')
        subclass_name = None
        if _class['subclassDefinition']:
            subclass_name = _class['subclassDefinition']['name']
            level_name = f"{level_name} ({subclass_name})"
        levels[level_name] += _class.get('level')
        classes.append(f"{level_name} {_class.get('level')}")
        if class_name not in ALLOWED_CLASSES:
            warnings.append(f"Disallowed class: {class_name}")
        if subclass_name and not any(subclass_name.startswith(a) for a in ALLOWED_SUBCLASSES):
            warnings.append(f"Disallowed subclass: {subclass_name}")

    # level
    level = sum(levels.values())
    if level != REQUIRED_LEVEL:
        warnings.append(f"Incorrect level: {level}")

    # background
    if not character['background']['definition']:
        background = None
    elif not character['background']['hasCustomBackground']:
        background = character['background']['definition']['name']
    else:
        background = "Custom"
    if background not in ALLOWED_BACKGROUNDS:
        warnings.append(f"Disallowed background: {background}")

    # feats (if any)
    for feat in character['feats']:
        if feat['definition']['name'] not in ALLOWED_FEATS:
            warnings.append(f"Disallowed feat: {feat['definition']['name']}")

    # spells (if any)
    spellnames = []
    for src in character['classSpells']:
        spellnames.extend(s['definition']['name'].replace('\u2019', "'") for s in src['spells'] if
                          s['prepared'] or s['alwaysPrepared'])
    for src in character['spells'].values():
        spellnames.extend(s['definition']['name'].replace('\u2019', "'") for s in src)

    for value in spellnames:
        if value not in ALLOWED_SPELLS:
            warnings.append(f"Disallowed spell: {value}")

    info = [
        f"Level: {level}",
        f"Race: {race}",
        f"Classes: {'/'.join(classes)}",
        f"Background: {background}"
    ]
    return warnings, info


class ExternalImportError(Exception):
    pass
