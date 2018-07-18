import unittest
import chess

class TestChess(unittest.TestCase):
    def test_default_fen(self):
        fen = chess.DEFAULT_POSITION
        result = chess.validate_fen(fen)
        self.assertEqual(0, result.error_number)

if __name__ == '__main__':
    unittest.main()