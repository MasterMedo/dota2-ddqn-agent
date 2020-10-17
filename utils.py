from collections import namedtuple

Creep = namedtuple('creep', 'hp x y xy')
Tower = namedtuple('tower', 'hp x y xy radius')
Stats = namedtuple('stats', 'last_hits denies time salve')
Hero = namedtuple('hero', 'x y xy lvl maxhp hp mana dmg target abilities')
Ability = namedtuple('ability', 'lvl cost dmg cooldown radius distance from_ to')
State = namedtuple('state', 'me opp good_tower bad_tower creeps allies enemies')


def get_entities(state):
    heroes = [Hero(
        lvl=state[i + 1],
        hp=state[i + 2],
        maxhp=state[i + 3],
        mana=state[i + 5],
        x=state[i // 30 * 26 + 26],
        y=state[i // 30 * 26 + 27],
        xy=state[i // 30 * 26 + 26] + state[i // 30 * 26 + 27] * 1j,
        dmg=state[i + 12],
        target=state[i + 18],
        abilities=[
            Ability(
                lvl=state[225 + i // 30 * 42 + j * 7],
                cost=state[225 + i // 30 * 42 + j * 7 + 1],
                dmg=state[225 + i // 30 * 42 + j * 7 + 2],
                cooldown=state[225 + i // 30 * 42 + j * 7 + 4],
                radius=(r := 250 if j < 3 else 1350),
                distance=(d := 200 + 250 * j if j < 3 else 0),
                from_=d - r,
                to=d + r
            ) for j in [0, 1, 2, 5]]
    ) for i in range(0, 56, 30)]

    creeps = [Creep(
        hp=state[i + 1],
        x=state[i + 12],
        y=state[i + 13],
        xy=state[i + 12] + 1j * state[i + 13],
    ) for i in range(85, 225, 14)]

    towers = [Tower(
        hp=state[i],
        x=-1531 if i == 58 else 542,
        y=-1406 if i == 58 else 658,
        xy=-1531 - 1406j if i == 58 else 542 + 658j,
        radius=700) for i in range(58, 70, 6)]

    stats = Stats(state[24], state[25], state[56], state[309] == 1)
    return State(*heroes, *towers, stats, creeps, creeps[:5], creeps[5:])


def get_legal_moves(me, opp, allies, enemies, bad_tower, stats):
    attack_tower = any(
        abs(creep.xy - bad_tower.xy) < bad_tower.radius and
        abs(creep.xy - bad_tower.xy) < abs(me.xy - bad_tower.xy)
        for creep in allies if creep.x != -1 and creep.y != -1)

    legal_actions = [
        1,  # do nothing
        *[1] * 8,  # movement
        *[0] * 4,  # runes
        opp.hp and opp.y < 500,  # att opp
        attack_tower,  # att tower
        *[creep.hp != -1 for creep in enemies],  # att enemy
        *[creep.hp != -1 and creep.hp <= me.dmg for creep in allies],
        *[any(me.abilities[i].from_ < abs(me.xy - enemy.xy) < me.abilities[i].to
          and me.abilities[i].lvl > 0 and enemy.hp > 0 and me.target
          for enemy in enemies + [opp]) for i in range(4)],  # use ability
        stats.salve and me.maxhp - me.hp > 250  # use salve
    ]

    return legal_actions
