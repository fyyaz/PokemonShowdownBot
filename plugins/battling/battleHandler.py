import re
import json
from random import randint

from plugins.battling.battle import Battle, Pokemon

class BattleHandler:
    def __init__(self, ws, name):
        self.ws = ws
        self.botName = name
        self.activeBattles = {}

    def respond(self, battle, msg):
        self.ws.send('{room}|{msg}'.format(room = battle, msg = msg))

    def getSpecies(self, details):
        return details.split(',')[0]

    def parse(self, battle, msg):
        if not msg: return
        if battle in self.activeBattles and 'init' in msg: return
        msg = msg.split('|')
        if 'init' == msg[1] and 'battle' == msg[2]:
            self.activeBattles[battle] = Battle(battle)
            self.respond(battle, '/timer')
        elif 'request' == msg[1]:
            # This is where all the battle picking happen
            request = json.loads(msg[2])
            if 'rqid' in request:
                self.activeBattles[battle].rqid = request['rqid']
            sidedata = request['side']
            for poke in sidedata['pokemon']:
                self.activeBattles[battle].me.updateTeam(
                    Pokemon(self.getSpecies(poke['details']),poke['details'],poke['condition'],poke['active'],
                            poke['stats'],poke['moves'],poke['baseAbility'],poke['item'],poke['canMegaEvo']))
        elif 'poke' == msg[1]:
            if not self.activeBattles[battle].me.id == msg[2]:
                pass        
        elif 'player' == msg[1]:
            if msg[3] == self.botName:
                self.activeBattles[battle].setMe(msg[3], msg[2])
            else:
                self.activeBattles[battle].setOther(msg[3], msg[2])
        elif 'teampreview' == msg[1]:
            self.respond(battle, '/team {nr}|{rqid}'.format(nr = randint(0,6), rqid = self.activeBattles[battle].rqid))
        elif 'turn' == msg[1]:
            move = self.activeBattles[battle].me.active.moves[randint(0,3)]
            self.respond(battle, '/choose move {name}|{rqid}'.format(name = move, rqid = self.activeBattles[battle].rqid))
        elif 'switch' == msg[1]:
            btl = self.activeBattles[battle]
            if msg[2].startswith(btl.me.id):
                btl.me.setActive(btl.me.getPokemon(self.getSpecies(msg[3])))
            else:
                btl.other.setActive(btl.other.getPokemon(self.getSpecies(msg[3])))
        elif msg[1] in ['win', 'tie']:
            if msg[2] == self.botName:
                self.respond(battle, 'O-oh, I won? Sorry :(')
            else:
                self.respond(battle, "It's okay, you're better than me :>")
            self.respond(battle, '/leave')