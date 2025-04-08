import re
import itertools
from PIL import Image, ImageDraw
import copy

# ========================
# STEP 1: Parse BFF Format
# ========================
def parse_bff(filepath):
    """
    Parses the input .bff file containing the puzzle configuration.

    Returns:
        - grid_full: the grid with placeholders for lasers and blocks
        - blocks: dictionary containing the count of each block type (A, B, C)
        - lazors: list of lazor starting positions and directions
        - points: list of target points the lazor must pass through
    """
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract and format the grid from the BFF content
    grid_text = re.search(r"GRID START(.*?)GRID STOP", content, re.DOTALL).group(1).strip().split('\n')
    grid_raw = [[c for c in line if c != ' '] for line in grid_text]

    # Expand grid to accommodate lazor movement in half-unit steps
    grid_full = [['x' for _ in range(len(grid_raw[0]) * 2 + 1)] for _ in range(len(grid_raw) * 2 + 1)]
    for i, row in enumerate(grid_raw):
        for j, val in enumerate(row):
            grid_full[2*i+1][2*j+1] = val  # Fill in only valid grid spaces

    # Extract block counts
    blocks = {'A': 0, 'B': 0, 'C': 0}
    for b in blocks:
        match = re.search(rf"{b} (\d+)", content)
        if match:
            blocks[b] = int(match.group(1))

    # Extract lazor data: starting position and direction
    lazors = re.findall(r"L (\d+) (\d+) (-?\d+) (-?\d+)", content)
    lazors = [((int(x), int(y)), (int(dx), int(dy))) for x, y, dx, dy in lazors]

    # Extract target points to be hit by lazors
    points = re.findall(r"P (\d+) (\d+)", content)
    points = [(int(x), int(y)) for x, y in points]

    return grid_full, blocks, lazors, points

# ==============================
# STEP 2: Laser Path Simulation
# ==============================
def reflect_or_refract(pos, dir, block):
    """
    Determines how a lazor reacts to hitting a block.
    Returns list of resulting direction(s).
    """
    dx, dy = dir
    x, y = pos

    if block == 'A':  # Reflective
        if x % 2 == 0:  # Horizontal hit
            return [(-dx, dy)]
        else:  # Vertical hit
            return [(dx, -dy)]
    elif block == 'B':  # Opaque
        return []  # Lazor stops
    elif block == 'C':  # Refractive
        if x % 2 == 0:
            return [(dx, dy), (-dx, dy)]  # Reflect and transmit horizontally
        else:
            return [(dx, dy), (dx, -dy)]  # Reflect and transmit vertically
    return [dir]  # No block: continue straight

def get_block_at(grid, x, y, dx, dy):
    """
    Looks ahead in the lazor direction to determine block type.
    """
    if x % 2 == 0:
        return grid[y][x + dx] if 0 <= x + dx < len(grid[0]) else 'x'
    else:
        return grid[y + dy][x] if 0 <= y + dy < len(grid) else 'x'

def trace(grid, start, direction):
    """
    Traces the lazor path given a start position and direction.
    Handles reflections, refractions, and stops.
    Returns a list of (x, y) positions visited.
    """
    path = []
    queue = [(start, direction)]
    seen = set()

    while queue:
        (x, y), (dx, dy) = queue.pop(0)
        while 0 <= x < len(grid[0]) and 0 <= y < len(grid):
            if ((x, y), (dx, dy)) in seen:
                break  # Avoid infinite loops
            seen.add(((x, y), (dx, dy)))
            path.append((x, y))
            block = get_block_at(grid, x, y, dx, dy)
            interactions = reflect_or_refract((x, y), (dx, dy), block)

            if len(interactions) > 1:
                # Split: refractive block
                queue.append(((x+dx, y+dy), interactions[0]))
                dx, dy = interactions[1]
            elif len(interactions) == 0:
                break  # Blocked
            else:
                dx, dy = interactions[0]
            x += dx
            y += dy
    return path

# ===============================
# STEP 3: Brute Force Permutator
# ===============================
def find_block_positions(grid):
    """
    Returns all positions in the grid where a movable block ('o') can be placed.
    """
    return [(i, j) for i in range(len(grid)) for j in range(len(grid[0])) if grid[i][j] == 'o']

def generate_block_grids(grid, blocks):
    """
    Generator that yields all valid block configurations for given slots.
    Combines all possible permutations and placements of blocks.
    """
    slots = find_block_positions(grid)
    all_blocks = ['A'] * blocks['A'] + ['B'] * blocks['B'] + ['C'] * blocks['C']
    perms = set(itertools.permutations(all_blocks))

    for slot_combo in itertools.combinations(slots, len(all_blocks)):
        for perm in perms:
            g = copy.deepcopy(grid)
            for (i, j), b in zip(slot_combo, perm):
                g[i][j] = b
            yield g

# =====================
# STEP 4: Check & Draw
# =====================
def all_points_hit(path_list, targets):
    """
    Checks if all target points have been hit by any lazor path.
    """
    all_hits = set()
    for p in path_list:
        all_hits.update(p)
    return all(t in all_hits for t in targets)

def draw_solution(grid, lazors, paths, targets, filename):
    """
    Draws and saves the solution as an image (with blocks, paths, and targets).
    """
    size = 40
    w, h = len(grid[0]), len(grid)
    img = Image.new('RGB', (w*size, h*size), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)

    # Colors for each cell type
    colors = {'A': (255,255,255), 'B': (0,0,0), 'C': (0,255,0), 'o': (100,100,100), 'x': (50,50,50)}

    for y in range(h):
        for x in range(w):
            cell = grid[y][x]
            c = colors.get(cell, (30,30,30))
            draw.rectangle([x*size, y*size, (x+1)*size, (y+1)*size], fill=c)

    # Optional: draw lazor paths and target points
    # Uncomment below if desired
    # for path in paths:
    #     for i in range(len(path)-1):
    #         x1, y1 = path[i]
    #         x2, y2 = path[i+1]
    #         draw.line([(x1*size//2, y1*size//2), (x2*size//2, y2*size//2)], fill=(255,0,0), width=3)
    #
    # for x, y in targets:
    #     px = x * size / 2
    #     py = y * size / 2
    #     draw.ellipse([(px - 6, py - 6), (px + 6, py + 6)], fill=(255, 255, 0), outline=(255, 0, 0), width=2)

    img.save(filename)
    print(f"✅ Solution saved to {filename}")

# =====================
# STEP 5: Main Entrypoint
# =====================
def solve_lazor(file_path):
    """
    Main function to solve the Lazor puzzle.
    It parses the BFF file, generates possible block arrangements,
    simulates lazor paths, and checks for success.
    """
    grid, blocks, lazors, targets = parse_bff(file_path)
    for g in generate_block_grids(grid, blocks):
        all_paths = [trace(g, pos, direction) for pos, direction in lazors]
        if all_points_hit(all_paths, targets):
            draw_solution(g, lazors, all_paths, targets, file_path.replace('.bff', '_solution.png'))
            return
    print("❌ No valid solution found.")

# Run script from command line
if __name__ == '__main__':
    path = input("请输入 .bff 文件名（含扩展名）: ").strip()
    solve_lazor(path)
