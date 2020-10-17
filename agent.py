import json
import requests
from flask import Flask, request
from utils import get_entities, get_legal_moves
from collections import deque
from ddqn import Agent

agent_ip = '192.168.0.20'
agent_port = 8086
breezy_ip = '192.168.0.15'
breezy_port = 8085

app = Flask(__name__)
last4states = deque(maxlen=4)
action = 1

agent = Agent()


def reward(state1, state2):
    if state2.me.hp == -1:  # I am dead
        return -1

    lh = state1.stats.last_hits - state2.stats.last_hits
    d = state1.stats.denies - state2.stats.denies
    dmg_done = state1.opp.hp - state2.opp.hp
    hp_lost = state1.me.hp - state2.me.hp
    time = state2.stats.time
    return ((lh + d) * 1000 + dmg_done - hp_lost + time) / 1000


def fitness(result):
    duration = result['duration']
    win = result['winner'] == 'Radiant'
    kills = result['radiantKills']
    deaths = result['deaths']
    return 2000 * win + 50 * (kills - deaths) + duration


@app.route('/connect', methods=['GET'])
def connect():
    return {'response': 'the agent is ready'}


@app.route('/update', methods=['POST'])
def update():
    """
    request.json = {
        'id': 'db56098d-824a-46a5-a138-ccf79a3059f3',
        'size': 1,
        'startTime': 'Thu Apr 02 09:03:35 CEST 2020',
        'endTime': 'Thu Apr 02 09:04:35 CEST 2020',     or key: webhook
        'duration': 59552,
        'status': 'DONE',                               or val: 'WAITING'
        'progress': 1,
        'gameIds': ['09:04:037942'],
        'winner': 'Dire',
        'direKills': 2,
        'radiantKills': 0,
        'deaths': 2}
    """
    if 'webhook' in request.json:  # proceed to the next game
        url = f'http://{breezy_ip}:{breezy_port}{request.json["webhook"]}'
        response = requests.get(url=url)

    else:  # start a new set of games or end session
        fitness(request.json)
        url = f'http://{breezy_ip}:{breezy_port}/run/'
        data = json.dumps({'agent': 'medo', 'size': 1})
        response = requests.post(url=url, data=data)
        print(response)

    return {'fitness': fitness(request.json)}


@app.route('/relay', methods=['POST'])
def relay():
    """ request.json = [int/float]*310 """
    global action
    state = get_entities(request.json)
    me, opp, good_tower, bad_tower, stats, creeps, allies, enemies = state
    d = 2000
    current_observation = [
        *[abs(me.x - e.x) / d for e in [opp, good_tower, bad_tower] + creeps],
        *[abs(me.y - e.y) / d for e in [opp, good_tower, bad_tower] + creeps],
        *[abs(creep.x - bad_tower.x) / d for creep in allies],
        *[abs(creep.y - bad_tower.y) / d for creep in allies],
        me.hp / me.maxhp,
        me.mana / me.abilities[0].cost,
        opp.hp / opp.maxhp,
        *[creep.hp / me.dmg for creep in creeps]
    ]
    observations, states = list(zip(last4states))
    observation = [i for j in observations for i in j]

    last4states.append((current_observation, state))

    if stats.time < 10 or abs(me.xy - good_tower.xy) > d:
        return {'actionCode': 1}

    legal_actions = get_legal_moves(me, opp, allies, enemies, bad_tower, stats)
    observations, states = list(zip(last4states))
    observation_ = [i for j in observations for i in j]
    r = reward(*states[-2:])
    agent.memory.append((observation, action, r, obeservation_))
    action = agent.predict(last4states, legal_actions)}
    return {'actionCode': action}


if __name__ == '__main__':
    # tell breezy server to start the games
    url = f'http://{breezy_ip}:{breezy_port}/run/'
    data = json.dumps({'agent': 'medo', 'size': 2})
    response = requests.post(url=url, data=data)
    # start the agent server
    app.run(host=agent_ip, port=agent_port, debug=True)

# vim: ts=4 fdm=expr fde=Fde_paragraph() fdl=0
