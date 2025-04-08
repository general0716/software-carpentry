import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sympy.utilities.iterables import multiset_permutations
import itertools
import copy
import time
import os
from math import factorial
from tqdm import tqdm
from itertools import combinations

# ======================
# File Parsing and Full Grid Generation
# ======================

def parse_bff_file(filename):
    """
    Reads a .bff puzzle file and returns a dictionary with:
      - grid: the small grid (list of lists) from between GRID START/STOP (each cell is one character)
      - blocks: a dict of available blocks, e.g. {'A': 2, 'B': 0, 'C': 1}
      - lazors: a list of lasers, each as ((x,y), (dx,dy))
      - points: a list of target points, each as (x,y)
    Comments (lines starting with '#') are ignored.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found")
    
    with open(filename, 'r') as f:
        lines = []
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                # Remove inline comments if any
                if '#' in stripped:
                    stripped = stripped.split('#')[0].strip()
                lines.append(stripped)
    
    grid = []
    blocks = {'A': 0, 'B': 0, 'C': 0}
    lazors = []
    points = []
    grid_mode = False

    for line in lines:
        if line.upper() == 'GRID START':
            grid_mode = True
            continue
        if line.upper() == 'GRID STOP':
            grid_mode = False
            continue
        
        if grid_mode:
            cleaned = line.replace(' ', '')
            if cleaned:
                grid.append(list(cleaned))
        elif line.startswith('A'):
            blocks['A'] = int(line.split()[1])
        elif line.startswith('B'):
            blocks['B'] = int(line.split()[1])
        elif line.startswith('C'):
            blocks['C'] = int(line.split()[1])
        elif line.startswith('L'):
            parts = line.split()
            lazors.append(((int(parts[1]), int(parts[2])), (int(parts[3]), int(parts[4]))))
        elif line.startswith('P'):
            parts = line.split()
            points.append((int(parts[1]), int(parts[2])))

    # Validate grid characters
    valid_chars = {'A', 'B', 'C', 'o', 'x'}
    for row in grid:
        for char in row:
            if char not in valid_chars:
                raise ValueError(f"Invalid grid character: {char}")

    return {
        'grid': grid,          # small grid from file
        'blocks': blocks,
        'lazors': lazors,
        'points': points
    }

def generate_full_grid(grid_origin):
    """
    Generate the full grid from the original small grid.
    For a grid of size rows x cols, the full grid has dimensions (2*rows+1) x (2*cols+1)
    where playable block positions occur at odd indices.
    """
    rows = len(grid_origin)
    cols = len(grid_origin[0])
    full_rows = 2 * rows + 1
    full_cols = 2 * cols + 1
    full_grid = []
    for i in range(full_rows):
        row = []
        if i % 2 == 0:
            row = ['x'] * full_cols
        else:
            original_row = grid_origin[(i - 1) // 2]
            for j in range(full_cols):
                if j % 2 == 0:
                    row.append('x')
                else:
                    row.append(original_row[(j - 1) // 2])
        full_grid.append(row)
    return full_grid

# ======================
# Block and Lazor Interaction
# ======================

class Block:
    def __init__(self, block_type):
        if block_type not in ('A', 'B', 'C'):
            raise ValueError(f"Invalid block type: {block_type}")
        self.type = block_type

    def interact(self, direction, point):
        return self.calculate_interaction(direction, point)

    def calculate_interaction(self, direction, collision_point):
        """
        In the full grid the playable block cells are at odd,odd coordinates.
        For block A (reflective): reflect by negating the component corresponding
        to the side hit. For block C (refractive): return both the transmitted
        (same) direction and a reflected direction. Block B stops the laser.
        We use a heuristic: if the x-coordinate of the collision point is even,
        assume a vertical edge was hit; if odd, assume horizontal.
        """
        dx, dy = direction
        x, y = collision_point

        if self.type == 'A':  # Reflective
            if x % 2 == 0:
                return [(-dx, dy)]
            else:
                return [(dx, -dy)]
        elif self.type == 'B':  # Opaque: stop laser
            return []
        elif self.type == 'C':  # Refractive: both transmit and reflect
            if x % 2 == 0:
                return [(dx, dy), (-dx, dy)]
            else:
                return [(dx, dy), (dx, -dy)]
        return [direction]

class Lazor:
    """
    A simple laser simulation in the full grid.
    Lasers start at a given coordinate with direction (dx, dy) (each component is ±1)
    and travel until they leave the grid. When hitting a block (A or C), the block’s interact()
    method is applied; opaque blocks (B) stop the beam.
    """
    def __init__(self, grid, start, direction, max_steps=200):
        self.grid = grid
        self.start = start  # (x, y) in full grid coordinates
        self.direction = direction  # (dx, dy)
        self.max_steps = max_steps

    def trace(self):
        path = []
        visited = set()
        queue = [(self.start, self.direction)]
        steps = 0
        height = len(self.grid)
        width = len(self.grid[0])
        
        while queue and steps < self.max_steps:
            (x, y), (dx, dy) = queue.pop(0)
            if ((x, y), (dx, dy)) in visited:
                continue
            visited.add(((x, y), (dx, dy)))
            path.append((x, y))
            new_x = x + dx
            new_y = y + dy

            if not (0 <= new_x < width and 0 <= new_y < height):
                steps += 1
                continue

            cell = self.grid[new_y][new_x]  # note: grid[y][x] with y as row index
            if cell in ('A', 'B', 'C'):
                block_obj = Block(cell)
                new_dirs = block_obj.interact((dx, dy), (new_x, new_y))
                for ndx, ndy in new_dirs:
                    queue.append(((new_x, new_y), (ndx, ndy)))
            else:
                queue.append(((new_x, new_y), (dx, dy)))
            steps += 1

        return path

# ======================
# Solver Core
# ======================

def solve_puzzle(puzzle_data, max_attempts=100000):
    """
    Brute-force over candidate placements in the full grid.
    Candidate positions come from the original grid:
      For each cell (i,j) in puzzle_data['grid'] that is 'o',
      the corresponding full grid coordinate is (2*i+1, 2*j+1).
    For each combination of candidate positions (of size total_blocks) and
    each permutation of block types, fill those positions and simulate all lasers.
    If the union of laser hit points covers every target, return the solution grid.
    """
    grid_origin = puzzle_data['grid']   # small grid from file
    blocks = puzzle_data['blocks']
    lazors = puzzle_data['lazors']
    targets = set(puzzle_data['points'])
    
    full_grid = generate_full_grid(grid_origin)
    
    # Candidate positions in full grid for placing blocks are the positions where the small grid has 'o'.
    candidate_positions = []
    for i in range(len(grid_origin)):
        for j in range(len(grid_origin[0])):
            if grid_origin[i][j] == 'o':
                candidate_positions.append((2 * i + 1, 2 * j + 1))
    
    total_blocks = sum(blocks.values())
    block_types = ['A'] * blocks['A'] + ['B'] * blocks['B'] + ['C'] * blocks['C']
    
    empty_combos = list(combinations(candidate_positions, total_blocks))
    num_empty_combos = len(empty_combos)
    num_block_perms = factorial(len(block_types)) // (factorial(blocks['A']) * factorial(blocks['B']) * factorial(blocks['C']))
    total_attempts = num_empty_combos * num_block_perms

    attempt_iter = itertools.product(empty_combos, multiset_permutations(block_types))
    progress = tqdm(itertools.islice(attempt_iter, max_attempts), total=min(max_attempts, total_attempts))
    
    for slots, perm in progress:
        test_grid = copy.deepcopy(full_grid)
        # Place each block (from perm) at the candidate full grid coordinates (from slots)
        for (r, c), block_letter in zip(slots, perm):
            test_grid[r][c] = block_letter
        
        all_hits = set()
        for start, direction in lazors:
            laz = Lazor(test_grid, start, direction, max_steps=200)
            path = laz.trace()
            all_hits.update(path)
        
        if all(p in all_hits for p in targets):
            print(f"\nSolution found after {progress.n} attempts!")
            return test_grid

    return None

# ======================
# Visualization
# ======================

def visualize_solution(solution, puzzle_data, filename):
    """
    Draw the full grid solution.
    Blocks and boundaries are drawn as squares, with colors depending on the cell:
      - 'x': boundary (black)
      - 'o': empty space (white)
      - 'A': reflective (blue)
      - 'B': opaque (gray)
      - 'C': refractive (green)
    Laser paths (as defined in the puzzle file) are drawn in red.
    """
    full_grid = solution
    height = len(full_grid)
    width = len(full_grid[0])
    
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    
    for i in range(height):
        for j in range(width):
            cell = full_grid[i][j]
            if cell == 'x':
                color = 'black'
            elif cell == 'o':
                color = 'white'
            elif cell == 'A':
                color = '#4682B4'
            elif cell == 'B':
                color = '#708090'
            elif cell == 'C':
                color = '#32CD32'
            else:
                color = 'white'
            rect = patches.Rectangle((j, i), 1, 1, facecolor=color, edgecolor='gray', linewidth=0.5)
            ax.add_patch(rect)
    
    # Draw laser paths for each laser defined in the puzzle file.
    lazors = puzzle_data['lazors']
    for start, direction in lazors:
        laz = Lazor(solution, start, direction, max_steps=200)
        path = laz.trace()
        x_coords = [pt[0] for pt in path]
        y_coords = [pt[1] for pt in path]
        ax.plot(x_coords, y_coords, 'r-', linewidth=2, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f"{filename}_solution.png")
    plt.close()
    print(f"Solution image saved to {filename}_solution.png")

# ======================
# Main Execution
# ======================

if __name__ == "__main__":
    input_file =  "dark_1.bff" 
    output_image = "solution"
    max_attempts = 50000  # Adjust if needed

    try:
        print(f"Loading puzzle: {input_file}")
        puzzle_data = parse_bff_file(input_file)
        print("\nPuzzle Parameters:")
        print(f"Small grid size: {len(puzzle_data['grid'])} x {len(puzzle_data['grid'][0])}")
        print(f"Blocks available: A={puzzle_data['blocks']['A']}  B={puzzle_data['blocks']['B']}  C={puzzle_data['blocks']['C']}")
        print(f"Number of lasers: {len(puzzle_data['lazors'])}")
        print(f"Target points: {puzzle_data['points']}")
        
        start_time = time.time()
        solution = solve_puzzle(puzzle_data, max_attempts)
        solve_time = time.time() - start_time
        
        if solution:
            print(f"\nSolution found in {solve_time:.2f} seconds!")
            visualize_solution(solution, puzzle_data, output_image)
        else:
            print(f"\nNo solution found after {max_attempts} attempts")
    except Exception as e:
        print(f"Error: {str(e)}")
