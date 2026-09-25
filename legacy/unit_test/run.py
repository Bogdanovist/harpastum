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

home.add_player(Player.Player(message_handler,utility,pitch,50,25))
#home.add_player(Player.Player(message_handler,blocker,pitch,70,20))
#home.add_player(Player.Player(message_handler,blocker,pitch,70,25))
#home.add_player(Player.Player(message_handler,blocker,pitch,70,30))

away.add_player(Player.Player(message_handler,blocker,pitch,85,15))
#away.add_player(Player.Player(message_handler,blocker,pitch,85,20))
#away.add_player(Player.Player(message_handler,blocker,pitch,85,25))
away.add_player(Player.Player(message_handler,blocker,pitch,85,30))


pitch.register_teams(home,away)
pitch.run_game(100.,dt=dt)

