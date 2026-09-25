import Pitch
import Player
import Team 
import MessageHandler
import Role
import pdb as debug

xsize=100.
ysize=50.
dt=0.1

message_handler=MessageHandler.MessageHandler(dt)

pitch = Pitch.Pitch(message_handler,xsize,ysize)

home=Team.Team(message_handler,1)
away=Team.Team(message_handler,-1)

utility=Role.Role()
blocker=Role.BlockerRole()
rx=Role.RxRole()
defender=Role.DefenderRole()

home.add_player(Player.Player(message_handler,blocker,pitch,60,15))
home.add_player(Player.Player(message_handler,blocker,pitch,60,20))
home.add_player(Player.Player(message_handler,blocker,pitch,60,25))
home.add_player(Player.Player(message_handler,blocker,pitch,60,30))
home.add_player(Player.Player(message_handler,defender,pitch,20,35))
home.add_player(Player.Player(message_handler,defender,pitch,20,15))
home.add_player(Player.Player(message_handler,rx,pitch,60,5))
home.add_player(Player.Player(message_handler,rx,pitch,60,45))
home.add_player(Player.Player(message_handler,utility,pitch,50,15))
home.add_player(Player.Player(message_handler,utility,pitch,50,25))
home.add_player(Player.Player(message_handler,utility,pitch,50,35))

away.add_player(Player.Player(message_handler,blocker,pitch,65,15))
away.add_player(Player.Player(message_handler,blocker,pitch,65,20))
away.add_player(Player.Player(message_handler,blocker,pitch,65,25))
away.add_player(Player.Player(message_handler,blocker,pitch,65,30))
away.add_player(Player.Player(message_handler,defender,pitch,80,35))
away.add_player(Player.Player(message_handler,defender,pitch,80,15))
away.add_player(Player.Player(message_handler,rx,pitch,65,5))
away.add_player(Player.Player(message_handler,rx,pitch,65,45))
away.add_player(Player.Player(message_handler,utility,pitch,75,15))
away.add_player(Player.Player(message_handler,utility,pitch,75,25))
away.add_player(Player.Player(message_handler,utility,pitch,75,35))


pitch.register_teams(home,away)
pitch.run_game(100.,dt=dt)

