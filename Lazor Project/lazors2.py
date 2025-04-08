import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw
from sympy.utilities.iterables import multiset_permutations
import itertools
import copy
import time
import os
from math import factorial
from tqdm import tqdm
from itertools import combinations

# ======================
# Core Game Logic
# ======================

class Block:
    def __init__(self, block_type):
        if block_type not in ('A', 'B', 'C'):
            raise ValueError(f"Invalid block type: {block_type}")
        self.type = block_type

    def interact(self, direction, point):
        return self.calculate_interaction(direction, point)

    def calculate_interaction(self, direction, collision_point):
        dx, dy = direction
        x, y = collision_point

        if self.type == 'A':  # Reflect block
            if x % 2 == 0:  # Vertical surface
                return [(-dx, dy)]
            else:  # Horizontal surface
                return [(dx, -dy)]
        elif self.type == 'B':  # Opaque block
            return []
        elif self.type == 'C':  # Refract block
            if x % 2 == 0:  # Vertical surface
                return [(dx, dy), (-dx, dy)]
            else:  # Horizontal surface
                return [(dx, dy), (dx, -dy)]
        return [direction]

# ======================
# File I/O and Parsing
# ======================

def parse_bff_file(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found")

    with open(filename, 'r') as f:
        lines = []
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
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
            if not cleaned:
                continue
            grid.append(list(cleaned))
        elif line.startswith('A'):
            blocks['A'] = int(line.split()[1])
        elif line.startswith('B'):
            blocks['B'] = int(line.split()[1])
        elif line.startswith('C'):
            blocks['C'] = int(line.split()[1])
        elif line.startswith('L'):
            parts = line.split()
            lazors.append(((int(parts[1]), int(parts[2])), 
                          (int(parts[3]), int(parts[4])))
        elif line.startswith('P'):
            parts = line.split()
            points.append((int(parts[1]), int(parts[2])))

    # Validation
    valid_chars = {'A', 'B', 'C', 'o', 'x'}
    for row in grid:
        for char in row:
            if char not in valid_chars:
                raise ValueError(f"Invalid grid character: {char}")

    return {
        'grid': grid,
        'blocks': blocks,
        'lazors': lazors,
        'points': points
    }

# ======================
# Laser Simulation
# ======================

def trace_laser(grid, start_pos, start_dir, max_steps=100):
    path = []
    visited = set()
    queue = [(start_pos, start_dir)]
    steps = 0

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    while queue and steps < max_steps:
        (x, y), (dx, dy) = queue.pop(0)
        if ((x, y), (dx, dy)) in visited:
            continue
        visited.add(((x, y), (dx, dy)))

        path.append((x, y))
        row = y // 2
        col = x // 2

        if 0 <= row < height and 0 <= col < width:
            block = grid[row][col]
        else:
            block = None

        if block == 'B':
            break
        elif block in ('A', 'C'):
            block_obj = Block(block)
            new_dirs = block_obj.interact((dx, dy), (x, y))
            for ndx, ndy in new_dirs:
                new_x = x + ndx
                new_y = y + ndy
                if 0 <= new_x < width*2 and 0 <= new_y < height*2:
                    queue.append(((new_x, new_y), (ndx, ndy)))
        else:
            new_x = x + dx
            new_y = y + dy
            if 0 <= new_x < width*2 and 0 <= new_y < height*2:
                queue.append(((new_x, new_y), (dx, dy)))

        steps += 1

    return path

# ======================
# Solver Core
# ======================

def solve_puzzle(data, max_attempts=100000):
    grid = data['grid']
    targets = set(data['points'])
    lazors = data['lazors']
    blocks = data['blocks']
    
    fixed_blocks = set((i, j) 
                      for i in range(len(grid)) 
                      for j in range(len(grid[0])) 
                      if grid[i][j] in ['A', 'B', 'C'])
    
    empty_slots = [(i, j) 
                  for i in range(len(grid)) 
                  for j in range(len(grid[0])) 
                  if grid[i][j] == 'o']
    
    total_blocks = sum(blocks.values())
    
    block_types = ['A']*blocks['A'] + ['B']*blocks['B'] + ['C']*blocks['C']
    
    progress = tqdm(
        itertools.islice(itertools.product(
            combinations(empty_slots, total_blocks),
            multiset_permutations(block_types)
        ), max_attempts),
        total=min(max_attempts, 
                 factorial(len(block_types)) // 
                 (factorial(blocks['A'])*factorial(blocks['B'])*factorial(blocks['C'])) 
                 * len(list(combinations(empty_slots, total_blocks))))
    )

    for slots, perm in progress:
        temp_grid = copy.deepcopy(grid)
        for (i, j), block in zip(slots, perm):
            temp_grid[i][j] = block

        all_hits = set()
        valid = True
        for start, dir in lazors:
            path = trace_laser(temp_grid, start, dir)
            all_hits.update((x, y) for (x, y) in path)
            if not all(p in all_hits for p in targets):
                valid = False
                break

        if valid:
            print(f"\nSolution found after {progress.n} attempts!")
            return temp_grid

    return None

# ======================
# Visualization
# ======================

def visualize_solution(solution, data, filename):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)
    
    # Grid drawing logic
    for i in range(len(solution)):
        for j in range(len(solution[0])):
            rect = patches.Rectangle(
                (j, i), 1, 1,
                facecolor='white' if solution[i][j] != 'x' else 'black',
                edgecolor='gray',
                linewidth=0.5
            )
            ax.add_patch(rect)
    
    # Block coloring
    block_colors = {
        'A': ('#4682B4', 'white'),
        'B': ('#708090', 'white'),
        'C': ('#32CD32', 'black')
    }
    
    for i in range(len(solution)):
        for j in range(len(solution[0])):
            cell = solution[i][j]
            if cell in block_colors:
                ax.add_patch(patches.Rectangle(
                    (j, i), 1, 1,
                    facecolor=block_colors[cell][0],
                    edgecolor='black',
                    linewidth=1
                ))
                ax.text(j + 0.5, i + 0.5, cell,
                        ha='center', va='center',
                        fontsize=14, color=block_colors[cell][1])
    
    # Laser paths
    for start, dir in data['lazors']:
        path = trace_laser(solution, start, dir)
        x = [p[0]/2 for p in path]
        y = [p[1]/2 for p in path]
        ax.plot(x, y, 'r-', linewidth=2, alpha=0.7)
    
    plt.savefig(f"{filename}_solution.png")
    plt.close()

# ======================
# Main Execution
# ======================

if __name__ == "__main__":
    input_file = "mad_1.bff"
    output_image = "solution"
    max_attempts = 50000

    try:
        print(f"Loading puzzle: {input_file}")
        puzzle_data = parse_bff_file(input_file)
        
        print("\nPuzzle Parameters:")
        print(f"Grid size: {len(puzzle_data['grid'])}x{len(puzzle_data['grid'][0])}")
        print(f"Blocks needed: A={puzzle_data['blocks']['A']} B={puzzle_data['blocks']['B']} C={puzzle_data['blocks']['C']}")
        
        start_time = time.time()
        solution = solve_puzzle(puzzle_data, max_attempts)
        solve_time = time.time() - start_time
        
        if solution:
            print(f"\nSolution found in {solve_time:.2f} seconds!")
            visualize_solution(solution, puzzle_data, output_image)
            print(f"Solution saved to {output_image}_solution.png")
        else:
            print(f"\nNo solution found after {max_attempts} attempts")

    except Exception as e:
        print(f"Error: {str(e)}")