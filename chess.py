from dataclasses import dataclass, asdict
from typing import NamedTuple
import re

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

# This string contains a Forsyth-Edwards Notation representation of a 
# particular board position in a chess game. In this case, this string
# represents the starting position of a game.
# 
# There are 6 fields in FEN notation:
#
# 1. Piece placement (from white's persepctive). Each rank is described, 
#    starting with rank 8 and ending with rank 1. Within each rank, the
#    contents of each square are described from file 'a' through 'h'. 
#    Following the Standard Algebraic Notation (SAN), each piece gets
#    identified by a single letter. White pieces are identified using
#    upper-case letters (PNBRQK) and black pieces are identified using 
#    lower-case letters (pnbrqk). Empty squares are noted using digits 
#    1 through 8 (the number of empty squares). '/' separates ranks.
# 2. Active color - 'w' means white moves next, 'b' means black.
# 3. Castling availability. 
#    '-' neither side can castle. 
#    'K' White can castle kingside
#    'W' White can castle queenside
#    'k' Black can castle kingside
#    'w' Black can castle queenside
# 4. En passant target square in algebraic notation. If no square, this 
#    is '-'. If a pawn has just made a two square move, this is the
#    position "behind" the pawn.
# 5. Halfmove clock. This is the number of halfmoves since the last capture
#    or pawn advance. This is ued to determine if a draw can be claimed under
#    the fifty move rule.
# 6. Fullmove number. The number of the full move. It starts at 1 and is 
#    incremented after Black's move.

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

@dataclass
class Piece:
    type: str 
    color: str 

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
class Squares:
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

# HACKHACK generate a copy of SQUARES as a dict
# I use this to see if a key exists
SQUARES = Squares()
SQUARES_dict = asdict(SQUARES)

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

# TODO: figure out if there's a better data structure
# numpy array? that I should be using instead of a list

board = [None] * 128

# Global state variables for the game

kings = {'w': EMPTY, 'b': EMPTY}
turn = WHITE
castling = {'w': 0, 'b': 0}
ep_square = EMPTY
half_moves = 0
move_number = 1
history = []
header = {}

def update_setup(fen):
    if len(history) > 0:
        return

    if fen != DEFAULT_POSITION:
        header['SetUp'] = '1'
        header['FEN'] = fen
    else:
        if 'SetUp' in header.keys():
            del header['SetUp']
        if 'FEN' in header.keys():
            del header['FEN']

def generate_fen():
    empty = 0
    fen = ''

    # Iterate over all of the squares in the board data structure
    i = SQUARES.a8
    while i <= SQUARES.h1:
        if board[i] is None:
            empty += 1
        else:
            # We have found a piece on the row, so write out the number
            # of empty squares before proceeding
            if empty > 0:
                fen += str(empty)
                empty = 0

            color = board[i].color
            piece = board[i].type 

            # White pieces are uppercase, black pieces are lowercase
            if color == WHITE:
                fen += piece.upper()
            else:
                fen += piece.lower()

        # When we roll off the right hand side of the board data structure
        # we need to write out the number of empties (if needed) followed
        # by a row terminator character, and then skip to the next row in 
        # the board data structure.
        if (i + 1) & 0x88:
            if empty > 0:
                fen += str(empty)
            
            if i != SQUARES.h1:
                fen += '/'
            
            empty = 0
            i += 8 
            
        i += 1
    
    # Compute allowable castling states
    cflags = ''
    if castling[WHITE] & BITS.KSIDE_CASTLE:
        cflags += 'K'
    if castling[WHITE] & BITS.QSIDE_CASTLE:
        cflags += 'Q'
    if castling[BLACK] & BITS.KSIDE_CASTLE:
        cflags += 'k'
    if castling[BLACK] & BITS.QSIDE_CASTLE:
        cflags += 'q'

    if cflags == '':
        cflags = '-'

    # Compute en passant state
    if ep_square == EMPTY:
        epflags = '-'
    else:
        epflags = algebraic(ep_square)

    return ' '.join([fen, turn, cflags, epflags, str(half_moves), str(move_number)])

def clear():
    board = [None] * 128
    kings = {'w': EMPTY, 'b': EMPTY}
    turn = WHITE
    castling = {'w': 0, 'b': 0}
    ep_square = EMPTY
    half_moves = 0
    move_number = 1
    history = []
    header = {}
    update_setup(generate_fen())

def get_rank(i):
    return i >> 4

def get_file(i):
    return i & 0xF

def algebraic(i):
    f = get_file(i) 
    r = get_rank(i) 
    return "abcdefgh"[f] + "87654321"[r]
    
# Piece is a dictionary with type and color fields
def put(piece: Piece, square):
    # Is type of piece valid?
    if SYMBOLS.find(piece.type.lower()) == -1:
        return False

    # Is square valid?
    if not square in SQUARES_dict:
        return False

    index = SQUARES_dict[square]
    
    if piece.type == KING and not (kings[piece.color] == EMPTY or kings[piece.color] == index):
        return False

    board[index] = piece
    if piece.type == KING:
        kings[piece.color] = index

    # TODO: These calls to generate_fen() and update_setup() seem really inefficient
    update_setup(generate_fen())
    return True

# Get a piece from the board
def get(square):
    return board[SQUARES_dict[square]]

# Remove a piecd from the board
def remove(square):
    piece = get(square)
    board[SQUARES_dict[square]] = None
    if piece is not None and piece.type == KING:
        kings[piece.color] = EMPTY

    update_setup(generate_fen())
    return piece

def load(fen):
    tokens = re.split(r'\s+', fen)
    position = tokens[0]
    square = 0

    if not validate_fen(fen).valid:
        return false

    clear()

    # initialize board position
    for i in range(len(position)):
        piece = position[i]

        if piece == '/':
            # end of line, skip 8 squares
            square += 8
        elif piece.isnumeric():
            # empty squares, skip the specified number
            square += int(piece)
        else:
            if piece.islower():
                color = BLACK
            else:
                color = WHITE
            
            put(Piece(piece.lower(), color), algebraic(square))
            square += 1

    # initialize turn state
    turn = tokens[1]

    # initialize castling state
    if tokens[2].find('K') > -1:
        castling[WHITE] |= BITS.KSIDE_CASTLE
    if tokens[2].find('Q') > -1:
        castling[WHITE] |= BITS.QSIDE_CASTLE
    if tokens[2].find('k') > -1:
        castling[BLACK] |= BITS.KSIDE_CASTLE
    if tokens[2].find('q') > -1:
        castling[BLACK] |= BITS.QSIDE_CASTLE

    # initialize en passant state
    if tokens[3] == '-':
        ep_square = EMPTY
    else:
        ep_square = SQUARES_dict[tokens[3]]

    # initialize move counters
    half_moves = int(tokens[4])
    move_number = int(tokens[5])

    return True

def reset():
    load(DEFAULT_POSITION)

# TODO: Consider turning this into a class with a property getter for error
# and moving the errors dict into the namespace of this class
class ValidationResult(NamedTuple):
    valid: bool
    error_number: int
    error: str

# Regular expression validators
en_passant_validator = re.compile('^(-|[abcdefgh][36])$')
castle_string_validator = re.compile('^(KQ?k?q?|Qk?q?|kq?|q|-)$')
white_black_validator = re.compile('^(w|b)$')
piece_validator = re.compile('^[prnbqkPRNBQK]$')

# Function to validate a FEN string
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
        return ValidationResult(False, 1, errors[1])

    # 2nd criterion: 6th field, move number field, is an integer value > 0
    elif not tokens[5].isnumeric() or int(tokens[5]) <= 0:
        return ValidationResult(False, 2, errors[2])

    # 3rd criterion: 5th field, half move counter, is an integer >= 0
    elif not tokens[4].isnumeric() or int(tokens[4]) < 0:
        return ValidationResult(False, 3, errors[3])

    # 4th criterion: 4th field is a valid en passant-string
    elif en_passant_validator.match(tokens[3]) is None:
        return ValidationResult(False, 4, errors[4])

    # 5th criterion: 3rd field is a valid castle-string
    elif castle_string_validator.match(tokens[2]) is None:
        return ValidationResult(False, 5, errors[5])

    # 6th criterion: 2nd field is "w" (white) or "b" (black)
    elif white_black_validator.match(tokens[1]) is None:
        return ValidationResult(False, 6, errors[6])

    # 7th criterion: 1st field contains 8 rows
    else:
        rows = tokens[0].split('/')
        if len(rows) != 8:
            return ValidationResult(False, 7, errors[7])

        # 8th criterion: check validity of every row
        for row in rows:
            sum_fields = 0
            previous_was_number = False

            for char in row:
                if char.isnumeric():
                    # 9th criterion: cannot have consecutive numbrers
                    if previous_was_number:
                        return ValidationResult(False, 8, errors[8])
                    sum_fields += int(char)
                    previous_was_number = True
                else:
                    # 10th criterion: cannot have invalid piece identifiers
                    if piece_validator.match(char) is None:
                        return ValidationResult(False, 9, errors[9])
                    sum_fields += 1
                    previous_was_number = False

            # 11th criterion: row is too large (> 8 fields in row)
            if sum_fields != 8:
                return ValidationResult(False, 10, errors[10])

    # 12th criterion: en-passant squares can only appear in certain rows
    if tokens[3][0] == '3' and tokens[1] == 'w' or tokens[3][0] == '6' and tokens[1] == 'b':
       return ValidationResult(False, 11, errors[11])

    return ValidationResult(True, 0, errors[0])

fen = None

if fen is None:
    load(DEFAULT_POSITION)
else:
    load(fen)
