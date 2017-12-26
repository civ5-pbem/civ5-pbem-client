"""
This module contains functions that interpret .Civ5Save files to find in-game
information, such as whose turn it is or if anyone lost.
"""

# Credit goes to Hussein Kaddoura for his work in civ5-saveparser
# https://github.com/rivarolle/civ5-saveparser
# without him this module would have taken an insufferably long time 
# to research and write

# TODO:
# time played - compressed

from bitstring import ConstBitStream

class SaveReader():
    """Class designed to retrieve basic data from files."""

    def __init__(self, file_name):
        self.file = open(file_name, 'r')
        self.stream = ConstBitStream(self.file)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.file.close()

    def read_bytes(self, count):
        """Read a number of bytes and return a bitstring."""
        return self.stream.read(count*8)

    def find_blocks(self):
        """Find all data blocks and return a tuple of their offsets."""
        return tuple(self.stream.findall('0x40000000', bytealigned=True))

    def read_int(self):
        """Read a 4 byte little endian int."""
        return self.stream.read(32).intle

    def read_ints(self, count):
        """Return a tuple of ints."""
        return tuple(map(lambda x: x.read(32).intle, 
                         self.read_bytes(count*4).cut(32)))

    def read_string(self):
        """Read a string with the length given in the first 4 bytes."""
        return self.stream.read(
            'bytes:{}'.format(self.read_int())).decode("utf-8", 'replace')
        
def parse_file(file_name):
    """
    Parses savefile and returns the turn number, current player number, 
    number of set passwords and the number of dead players.
    """
    with SaveReader(file_name) as sr:
        # Current turn
        sr.stream.pos = 64
        sr.read_string()
        sr.read_string()
        current_turn = sr.read_int()

        block_positions = sr.find_blocks()
        # Number of players
        sr.stream.pos = block_positions[2] + 32
        player_statuses = sr.read_ints(22) # Maximum number is 22 players
        # 1 is AI
        # 2 is Dead/Closed
        # 3 is Human
        # 4 is Missing, i.e. too small map
        dead_number = len(tuple(filter(lambda x: x == 2,
                                       player_statuses)))

        # Current player
        sr.stream.pos = block_positions[8] - 32 * 4
        current_player = sr.read_int()

        # Number of passwords
        sr.stream.pos = block_positions[11] + 32
        password_number = 0
        for i in range(22):
            if sr.read_string():
                password_number += 1

    return current_turn, current_player, password_number, dead_number
