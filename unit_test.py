
import unittest
import os
import tempfile
from lazors import parse_bff, reflect_or_refract, trace, find_block_positions, generate_block_grids

class TestLazorFunctions(unittest.TestCase):
    def setUp(self):
        # Create a temporary .bff file for testing
        self.test_bff_content = """
        GRID START
        x o o
        o o o
        o o x
        GRID STOP
        B 3
        L 3 0 -1 1
        L 1 6 1 -1
        P 0 3
        """
        self.temp_bff = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.bff')
        self.temp_bff.write(self.test_bff_content)
        self.temp_bff.close()

    def tearDown(self):
        os.remove(self.temp_bff.name)

    # ------------------------------
    # Test 1: Block Position Finder
    # ------------------------------
    def test_find_block_positions(self):
        """Test identification of movable block positions ('o')"""
        grid, _, _, _ = parse_bff(self.temp_bff.name)
        positions = find_block_positions(grid)
        # Expected 'o' positions in the expanded grid
        expected_positions = [(1, 3), (1, 5), (3, 1), (3, 3), (3, 5), (5, 1), (5, 3)]
        self.assertEqual(positions, expected_positions)

    # ------------------------------
    # Test 2: Block Permutations
    # ------------------------------
    def test_generate_block_grids(self):
        """Test generation of valid block configurations"""
        grid, blocks, _, _ = parse_bff(self.temp_bff.name)
        generator = generate_block_grids(grid, blocks)
        first_config = next(generator)
        
        # Verify exactly 3 'B' blocks are placed
        b_count = sum(row.count('B') for row in first_config)
        self.assertEqual(b_count, 3)

    # ------------------------------
    # Test 3: Block Interactions
    # ------------------------------
    def test_reflective_block(self):
        """Test reflective block direction change"""
        new_dirs = reflect_or_refract((2, 3), (1, 0), 'A')  # Horizontal collision
        self.assertEqual(new_dirs, [(-1, 0)])

    def test_refractive_block(self):
        """Test refractive block splits laser"""
        new_dirs = reflect_or_refract((2, 3), (1, 0), 'C')
        self.assertEqual(sorted(new_dirs), sorted([(1, 0), (-1, 0)]))

    # ------------------------------
    # Test 4: Laser Path Tracing
    # ------------------------------
    def test_trace_simple_path(self):
        """Test straight laser path with no blocks"""
        grid = [
            ['x', 'x', 'x', 'x'],
            ['x', 'o', 'o', 'x'],
            ['x', 'x', 'x', 'x']
        ]
        path = trace(grid, (1, 1), (1, 0))  # Start at (1,1), move right
        self.assertEqual(path, [(1, 1), (2, 1), (3, 1)])

    def test_trace_opaque_block(self):
        """Test laser termination at opaque block"""
        grid = [
            ['x', 'x', 'x', 'x'],
            ['x', 'B', 'o', 'x'],
            ['x', 'x', 'x', 'x']
        ]
        path = trace(grid, (1, 1), (1, 0))  # Hits B at (2,1)
        self.assertEqual(path, [(1, 1)])

    # ------------------------------
    # Test 5: Solution Validation
    # ------------------------------
    def test_all_points_hit(self):
        """Check if target points are covered"""
        paths = [[(0, 3), (1, 4)], [(6, 1)]]
        self.assertTrue(all_points_hit(paths, [(0, 3), (6, 1)]))
        self.assertFalse(all_points_hit(paths, [(0, 3), (5, 5)]))

if __name__ == '__main__':
    unittest.main()
