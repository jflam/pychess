from dataclasses import dataclass

#
# Chess AI - this is initially a port of the chess.js codebase so that I have a
# reasonable baseline of code to start from.
#

# Define a set of constants -- in the JS version this code is all scoped to a 
# namespace. Will refactor the code later to clean this up (and when I learn how!)

# Constants that define the pieces and their board positions

BLACK = 'b'
WHITE = 'w'

EMPTY = -1

PAWN = 'p'
KNIGHT = 'n'
BISHOP = 'b'
ROOK = 'r'
QUEEN = 'q'
KING = 'k'

SYMBOLS = 'pnbrqkPNBRQK'

# This string is game state serialized into a compact string representation
# lower case is black, upper case is white. The structure has the following 
# properties:
#
# There are six space-separated fields
# 1st field contains the positions of all of the pieces on the board
# 6th field contains the current move number and must be > 0


DEFAULT_POSITION = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

POSSIBLE_RESULTS = ['1-0', '0-1', '1/2-1/2', '*']

PAWN_OFFSETS = {
    BLACK: [16, 32, 17, 15],
    WHITE: [-16, -32, -17, -15]
}

PIECE_OFFSETS = {
    KNIGHT: [-18, -33, -31, -14,  18, 33, 31,  14],
    BISHOP: [-17, -15,  17,  15],
    ROOK: [-16,   1,  16,  -1],
    QUEEN: [-17, -16, -15,   1,  17, 16, 15,  -1],
    KING: [-17, -16, -15,   1,  17, 16, 15,  -1]
}

ATTACKS = [
    20, 0, 0, 0, 0, 0, 0, 24,  0, 0, 0, 0, 0, 0,20, 0,
    0, 20, 0, 0, 0, 0, 0, 24,  0, 0, 0, 0, 0,20, 0, 0,
    0,  0,20, 0, 0, 0, 0, 24,  0, 0, 0, 0,20, 0, 0, 0,
    0,  0, 0,20, 0, 0, 0, 24,  0, 0, 0,20, 0, 0, 0, 0,
    0,  0, 0, 0,20, 0, 0, 24,  0, 0,20, 0, 0, 0, 0, 0,
    0,  0, 0, 0, 0,20, 2, 24,  2,20, 0, 0, 0, 0, 0, 0,
    0,  0, 0, 0, 0, 2,53, 56, 53, 2, 0, 0, 0, 0, 0, 0,
    24,24,24,24,24,24,56,  0, 56,24,24,24,24,24,24, 0,
    0,  0, 0, 0, 0, 2,53, 56, 53, 2, 0, 0, 0, 0, 0, 0,
    0,  0, 0, 0, 0,20, 2, 24,  2,20, 0, 0, 0, 0, 0, 0,
    0,  0, 0, 0,20, 0, 0, 24,  0, 0,20, 0, 0, 0, 0, 0,
    0,  0, 0,20, 0, 0, 0, 24,  0, 0, 0,20, 0, 0, 0, 0,
    0,  0,20, 0, 0, 0, 0, 24,  0, 0, 0, 0,20, 0, 0, 0,
    0, 20, 0, 0, 0, 0, 0, 24,  0, 0, 0, 0, 0,20, 0, 0,
    20, 0, 0, 0, 0, 0, 0, 24,  0, 0, 0, 0, 0, 0,20
]

RAYS = [
    17, 0,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0,  0,  0, 15, 0,
    0, 17,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0,  0, 15,  0, 0,
    0,  0, 17,  0,  0,  0,  0, 16,  0,  0,  0,  0, 15,  0,  0, 0,
    0,  0,  0, 17,  0,  0,  0, 16,  0,  0,  0, 15,  0,  0,  0, 0,
    0,  0,  0,  0, 17,  0,  0, 16,  0,  0, 15,  0,  0,  0,  0, 0,
    0,  0,  0,  0,  0, 17,  0, 16,  0, 15,  0,  0,  0,  0,  0, 0,
    0,  0,  0,  0,  0,  0, 17, 16, 15,  0,  0,  0,  0,  0,  0, 0,
    1,  1,  1,  1,  1,  1,  1,  0, -1, -1,  -1,-1, -1, -1, -1, 0,
    0,  0,  0,  0,  0,  0,-15,-16,-17,  0,  0,  0,  0,  0,  0, 0,
    0,  0,  0,  0,  0,-15,  0,-16,  0,-17,  0,  0,  0,  0,  0, 0,
    0,  0,  0,  0,-15,  0,  0,-16,  0,  0,-17,  0,  0,  0,  0, 0,
    0,  0,  0,-15,  0,  0,  0,-16,  0,  0,  0,-17,  0,  0,  0, 0,
    0,  0,-15,  0,  0,  0,  0,-16,  0,  0,  0,  0,-17,  0,  0, 0,
    0,-15,  0,  0,  0,  0,  0,-16,  0,  0,  0,  0,  0,-17,  0, 0,
  -15,  0,  0,  0,  0,  0,  0,-16,  0,  0,  0,  0,  0,  0,-17
]

SHIFTS = { 
    PAWN: 0, 
    KNIGHT: 1,
    BISHOP: 2,
    ROOK: 3, 
    QUEEN: 4, 
    KING: 5 
}

# This is better captured as a dictionary based on usage
FLAGS = {
    'NORMAL': 'n',
    'CAPTURE': 'c',
    'BIG_PAWN': 'b',
    'EP_CAPTURE': 'e',
    'PROMOTION': 'p',
    'KSIDE_CASTLE': 'k',
    'QSIDE_CASTLE': 'q'
}

@dataclass
class BITS:
    NORMAL: int = 1
    CAPTURE: int = 2
    BIG_PAWN: int = 4
    EP_CAPTURE: int = 8
    PROMOTION: int = 16
    KSIDE_CASTLE: int = 32
    QSIDE_CASTLE: int = 64

RANK_1 = 7
RANK_2 = 6
RANK_3 = 5
RANK_4 = 4
RANK_5 = 3
RANK_6 = 2
RANK_7 = 1
RANK_8 = 0

# This dataclass maps board positions to offsets in the board. The board is
# represented as a 1-dimensional vector, and this is used to map

@dataclass
class SQUARES:
    a8: int = 0
    b8: int = 1
    c8: int = 2
    d8: int = 3
    e8: int = 4
    f8: int = 5
    g8: int = 6
    h8: int = 7
    a7: int = 16
    b7: int = 17
    c7: int = 18
    d7: int = 19
    e7: int = 20
    f7: int = 21
    g7: int = 22
    h7: int = 23
    a6: int = 32
    b6: int = 33
    c6: int = 34
    d6: int = 35
    e6: int = 36
    f6: int = 37
    g6: int = 38
    h6: int = 39
    a5: int = 48
    b5: int = 49
    c5: int = 50
    d5: int = 51
    e5: int = 52
    f5: int = 53
    g5: int = 54
    h5: int = 55
    a4: int = 64
    b4: int = 65
    c4: int = 66
    d4: int = 67
    e4: int = 68
    f4: int = 69
    g4: int = 70
    h4: int = 71
    a3: int = 80
    b3: int = 81
    c3: int = 82
    d3: int = 83
    e3: int = 84
    f3: int = 85
    g3: int = 86
    h3: int = 87
    a2: int = 96
    b2: int = 97
    c2: int = 98
    d2: int = 99
    e2: int = 100
    f2: int = 101
    g2: int = 102
    h2: int = 103
    a1: int = 112
    b1: int = 113
    c1: int = 114
    d1: int = 115
    e1: int = 116
    f1: int = 117
    g1: int = 118
    h1: int = 119

ROOKS = {
    WHITE: [
        {'square': SQUARES.a1, 'flag': BITS.QSIDE_CASTLE},
        {'square': SQUARES.h1, 'flag': BITS.KSIDE_CASTLE}
    ],
    BLACK: [
        {'square': SQUARES.a8, 'flag': BITS.QSIDE_CASTLE},
        {'square': SQUARES.h8, 'flag': BITS.KSIDE_CASTLE}
    ]
}

# State variable for the chess board. There are 8 rows 
# of 16 columns that represent the state of the board
# Based on the SQAURES dictionary above, I take it that
# only the left half of the board is used to represent
# the game position.

board = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
]

# Global state variables for the game

kings = {'w': EMPTY, 'b': EMPTY}
turn = WHITE
castling = {'w': 0, 'b': 0}
ep_square = EMPTY
half_moves = 0
move_number = 1
history = []
header = {}

import re
fen = DEFAULT_POSITION
tokens = re.split('\s+', fen)
print(tokens)
position = tokens[0]
square = 0

# function to validate a fen
# TODO: should this return a dataclass instead of a dict? Probably

def validate_fen(fen):
    errors = {
        0: 'No errors.',
        1: 'FEN string must contain six space-delimited fields.',
        2: '6th field (move number) must be a positive integer.',
        3: '5th field (half move counter) must be a non-negative integer.',
        4: '4th field (en-passant square) is invalid.',
        5: '3rd field (castling availability) is invalid.',
        6: '2nd field (side to move) is invalid.',
        7: '1st field (piece positions) does not contain 8 \'/\'-delimited rows.',
        8: '1st field (piece positions) is invalid [consecutive numbers].',
        9: '1st field (piece positions) is invalid [invalid piece].',
        10: '1st field (piece positions) is invalid [row too large].',
        11: 'Illegal en-passant square',
    }

    # 1st criterion: 6 space-seperated fields? 
    tokens = re.split('\s+', fen)
    if len(tokens) != 6:
        return {
            "valid": False,
            "error_number": 1,
            "error": errors[1]
        }

    if not tokens[5].isnumeric() or int(tokens[5]) <= 0:
        return {
            "valid": False, 
            "error_number": 2, 
            "error": errors[2]
        }
    else:
        return { 
            "valid": True,
            "error_number": 0,
            "error": errors[0]
        }
