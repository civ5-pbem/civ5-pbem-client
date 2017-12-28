# civ5-pbem-client
Python package with a CLI program to interact with [civ5-pbem-server](https://github.com/mcybulsk/civ5-pbem-server) as a client. Although a GUI application is planned for the future, current focus is entirely on perfecting the base package.

## Getting started
### Requirements
The entire code runs on [Python 3](https://www.python.org/about/).
The following packages need to be installed to get civ5-pbem-client up and running:

* [Requests](http://docs.python-requests.org/en/master/)
* [docopt](https://github.com/docopt/docopt)
* [bitstring](https://pythonhosted.org/bitstring/)

Once all of the above are installed, use [git](https://git-scm.com/downloads) to download the repository:
```
git clone https://github.com/civ5-pbem/civ5-pbem-client.git
```
To run the client simply run `cli-client.py` in the command line.

### Usage
#### Set up
Before we can do anything else, we must first register on a server. Get a civ5-pbem-server up and running with your friends and on the client run:
```
./cli-client.py init
```
and complete registration as asked.

#### Joining a game
To play Civ 5 we must find a game we want to join and join it. That can be done simply by:
```
./cli-client.py list
./cli-client.py join <game number>
```
Where `<game number>` is the number of the game from `./cli-client.py list`.
To choose a civilization we should use:
```
./cli-client.py choose-civ <game number> <civilization>
```
Where `<civilization>` is a civilization from a list given by `./cli-client.py list-civs`.
We can check the status and more detailed information about the game with `./cli-client.py info <game number>`.

Once the game starts and our turn comes we should first:
```
./cli-client.py download <game number>
```
That will download the save file and put it into our Civilization 5 hotseat save directory. If a save file has not appeared, please check config.ini, change the `save_path` value appropriately and try again.

Once we load up the save in Civ we must set a password and perform the turn.

After that's done, just overwrite the save file that you downloaded and run:
```
./cli-client.py upload <game number>
```
If everything goes right we will have finished our turn and sent the save over for the next player.

#### Starting a new game
To start a new game we must:
```
./cli-client.py new-game <name> <description> <map size>
```
Possible `<map size>` options are listed with `--help`.
Once we have created a new game we can select AI players and choose their
civilizations. 
To change their type:
```
./cli-client.py change-player-type <game> <player> <player-type>
```
where `<player>` is a player number given by `info <game>` and `<player-type>`
is one of `human`,`ai`, and `closed`.
To change their civilization:
```
./cli-client.py choose-civ <game> <player> <civilization>
```

Once players join like described in [Joining a game](https://github.com/civ5-pbem/civ5-pbem-client#joining-a-game), you will be able to start
the game with:
```
./cli-client start <game>
```
Now set up a hotseat game in Civ as it is described in `info <game>`, play the
first turn, save it as `<name of game>` and run
```
./cli-client upload <game>
```

And it's up!

## Credits
* [Giant Multiplayer Robot](https://github.com/n7software/MRobot.Civilization) team for beautiful and cohesive save file parsing & manipulation research
* [bmaupin](https://github.com/bmaupin/js-civ5save) for working on & gathering research about the Civilization 5 save format
* [rivarolle](https://github.com/rivarolle/civ5-saveparser) for an extremely helpful savefile parsing package
