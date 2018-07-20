import unittest
import chess

class TestChess(unittest.TestCase):
    def test_default_fen(self):
        fen = chess.DEFAULT_POSITION
        result = chess.validate_fen(fen)
        self.assertEqual(0, result.error_number)

    def test_roundtrip_fen(self):
        fen = chess.DEFAULT_POSITION
        result = chess.load(fen)
        self.assertTrue(result)
        new_fen = chess.generate_fen()
        self.assertEqual(fen, new_fen)

if __name__ == '__main__':
    unittest.main()