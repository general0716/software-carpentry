import unittest
import os
import tempfile
from lazors import parse_bff, reflect_or_refract, trace, all_points_hit, generate_block_grids, solve_lazor

class TestLazorSolver(unittest.TestCase):
    def setUp(self):
        # Create a temporary .bff file mimicking dark_1.bff
        self.test_bff_content = """
        GRID START
        x o o
        o o o
        o o x
        GRID STOP

        B 3

        L 3 0 -1 1
        L 1 6 1 -1
        L 3 6 -1 -1
        L 4 3 1 -1

        P 0 3
        P 6 1
        """
        self.temp_bff = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.bff')
        self.temp_bff.write(self.test_bff_content)
        self.temp_bff.close()

    def tearDown(self):
        os.remove(self.temp_bff.name)  # Clean up

    # ------------------------------
    # Test 1: BFF Parsing
    # ------------------------------
    def test_parse_dark1_bff(self):
        """Test parsing of dark_1.bff content"""
        grid, blocks, lazors, points = parse_bff(self.temp_bff.name)
        
        # Grid: expanded to 7x7 for half-steps
        expected_grid = [
            ['x'] * 7,
            ['x', 'x', 'x', 'o', 'x', 'o', 'x'],
            ['x'] * 7,
            ['x', 'o', 'x', 'o', 'x', 'o', 'x'],
            ['x'] * 7,
            ['x', 'o', 'x', 'o', 'x', 'x', 'x'],
            ['x'] * 7
        ]
        self.assertEqual(grid, expected_grid)
        self.assertEqual(blocks, {'A': 0, 'B': 3, 'C': 0})
        # Lazors: positions and directions
        self.assertEqual(lazors, [
            ((3, 0), (-1, 1)),
            ((1, 6), (1, -1)),
            ((3, 6), (-1, -1)),
            ((4, 3), (1, -1))
        ])
        self.assertEqual(points, [(0, 3), (6, 1)])

    # ------------------------------
    # Test 2: Opaque Block Behavior
    # ------------------------------
    def test_opaque_block_blocks_lazor(self):
        """Opaque block (B) stops the lazor"""
        grid = [
            ['x', 'x', 'x', 'x', 'x'],
            ['x', 'B', 'x', 'o', 'x'],
            ['x', 'x', 'x', 'x', 'x']
        ]
        path = trace(grid, (1, 1), (1, 0))  # Start at (1,1), move right
        self.assertEqual(path, [(1, 1)])  # Lazor stops immediately at B

    # ------------------------------
    # Test 3: Laser Paths with Opaque Blocks
    # ------------------------------
    def test_trace_with_opaque_blocks(self):
        """Test lazor termination at opaque blocks (B)"""
        grid = [
            ['x', 'x', 'x', 'x'],
            ['x', 'B', 'x', 'x'],
            ['x', 'x', 'x', 'x']
        ]
        path = trace(grid, (1, 1), (1, 0))  # Hits B at (2,1)
        self.assertEqual(path, [(1, 1)])  # Lazor stops at B

    # ------------------------------
    # Test 4: Block Placement Generation
    # ------------------------------
    def test_generate_3B_placements(self):
        """Ensure 3 opaque blocks are placed in 'o' slots"""
        grid, blocks, _, _ = parse_bff(self.temp_bff.name)
        generator = generate_block_grids(grid, blocks)
        first_config = next(generator)
        
        # Count 'B's in the generated grid
        b_count = sum(row.count('B') for row in first_config)
        self.assertEqual(b_count, 3)

    # ------------------------------
    # Test 5: Integration Test (Solve dark_1.bff)
    # ------------------------------
    def test_solve_dark1(self):
        """Test full solution for dark_1.bff"""
        # Ensure dark_1.bff exists in the working directory
        if os.path.exists("dark_1.bff"):
            solve_lazor("dark_1.bff")
            self.assertTrue(os.path.exists("dark_1_solution.png"))
        else:
            self.skipTest("dark_1.bff not found")

if __name__ == '__main__':
    unittest.main()
