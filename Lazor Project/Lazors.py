import matplotlib.pyplot as plt
import matplotlib.patches as patches
import itertools
import copy
from math import factorial
from tqdm import tqdm
import time
import os
from itertools import combinations

# --------------------------
# Block class
# --------------------------
class Block:
    def __init__(self, block_type):
        if block_type not in ('A', 'B', 'C'):
            raise ValueError(f"未知方块类型: {block_type}")
        self.type = block_type

    def interact(self, direction, point):
        return calculate_interaction(self.type, direction, point)


# --------------------------
# 文件解析
# --------------------------
def parse_bff_file(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"文件 {filename} 不存在")

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
            if grid_mode:
                raise ValueError("重复的GRID START标记")
            grid_mode = True
            continue
        if line.upper() == 'GRID STOP':
            if not grid_mode:
                raise ValueError("无匹配的GRID START标记")
            grid_mode = False
            continue

        if grid_mode:
            cleaned = line.replace(' ', '').replace('\t', '')
            if not cleaned:
                continue
            if grid and len(cleaned) != len(grid[0]):
                raise ValueError(f"网格行长度不一致: {len(grid[0])} vs {len(cleaned)}")
            grid.append(list(cleaned))
        elif line[0].upper() == 'A':
            parts = line.split()
            blocks['A'] = int(parts[1])
        elif line[0].upper() == 'B':
            parts = line.split()
            blocks['B'] = int(parts[1])
        elif line[0].upper() == 'C':
            parts = line.split()
            blocks['C'] = int(parts[1])
        elif line[0].upper() == 'L':
            parts = line.split()
            lazors.append(((int(parts[1]), int(parts[2])), (int(parts[3]), int(parts[4]))))
        elif line[0].upper() == 'P':
            parts = line.split()
            points.append((int(parts[1]), int(parts[2])))

    if not grid:
        raise ValueError("网格数据为空")
    if not lazors:
        raise ValueError("未定义激光路径")
    if not points:
        raise ValueError("未定义目标点")

    return {
        'grid': grid,
        'blocks': blocks,
        'lazors': lazors,
        'points': points
    }


# --------------------------
# 激光追踪逻辑
# --------------------------
def get_block(grid, point):
    x, y = point
    if x < 0 or y < 0:
        return None
    if x % 2 == 1 and y % 2 == 1:
        return None

    row = y // 2
    col = x // 2
    if row >= len(grid) or col >= len(grid[0]):
        return None
    return grid[row][col]


def calculate_interaction(block_type, direction, collision_point):
    dx, dy = direction
    x, y = collision_point

    if block_type == 'A':  # 反射块
        if x % 2 == 0 and y % 2 == 1:
            return [(-dx, dy)]
        elif x % 2 == 1 and y % 2 == 0:
            return [(dx, -dy)]
        else:
            return []

    elif block_type == 'B':  # 阻挡块
        return []

    elif block_type == 'C':  # 折射块
        if x % 2 == 0 and y % 2 == 1:
            return [(dx, dy), (-dx, dy)]
        elif x % 2 == 1 and y % 2 == 0:
            return [(dx, dy), (dx, -dy)]
        else:
            return [(dx, dy)]

    return [direction]


def trace_laser(grid, start_pos, start_dir, max_reflections=50):
    path = []
    visited = set()
    queue = [(start_pos, start_dir)]
    step_counter = 0  # 用于路径编号

    while queue and len(visited) < max_reflections:
        pos, dir = queue.pop(0)
        if (pos, dir) in visited:
            continue
        visited.add((pos, dir))

        x, y = pos
        dx, dy = dir

        while True:
            # 边界判断，若越界则立即终止该路径
            if x < 0 or y < 0 or x >= len(grid[0]) * 2 or y >= len(grid) * 2:
                break

            path.append(((x, y), step_counter))
            step_counter += 1
            block = get_block(grid, (x, y))

            if block in ['A', 'B', 'C']:
                new_dirs = calculate_interaction(block, (dx, dy), (x, y))
                for ndx, ndy in new_dirs:
                    queue.append(((x + ndx, y + ndy), (ndx, ndy)))
                break

            x += dx
            y += dy

    return path



# --------------------------
# 穷举求解器
# --------------------------
def solve_with_bruteforce(data, max_attempts=100000):
    grid = data['grid']
    targets = set(data['points'])
    lazors = data['lazors']
    blocks = data['blocks']

    fixed_blocks = set((i, j) for i in range(len(grid)) for j in range(len(grid[0])) if grid[i][j] in ['A', 'B', 'C'])
    empty_slots = [(i, j) for i in range(len(grid)) for j in range(len(grid[0])) if grid[i][j] == 'o']
    total_blocks = sum(blocks.values())

    if total_blocks == 0:
        print("无需放置方块，检查原始配置")
        return None
    if len(empty_slots) < total_blocks:
        print(f"错误：需要{total_blocks}个方块，但只有{len(empty_slots)}个空位")
        return None

    block_types = ['A'] * blocks['A'] + ['B'] * blocks['B'] + ['C'] * blocks['C']
    total_perms = factorial(len(block_types)) // (
            factorial(blocks['A']) * factorial(blocks['B']) * factorial(blocks['C']))

    print(f"总排列组合数: {total_perms} (最多尝试{min(max_attempts, total_perms)}次)")
    slot_combinations = list(combinations(empty_slots, total_blocks))
    print(f"空位组合数: {len(slot_combinations)}")

    progress = tqdm(
        itertools.islice(itertools.product(slot_combinations, set(itertools.permutations(block_types))), max_attempts),
        total=min(max_attempts, len(slot_combinations) * total_perms)
    )

    for slots, perm in progress:
        temp_grid = copy.deepcopy(grid)
        for (i, j), block in zip(slots, perm):
            temp_grid[i][j] = block

        all_hits = set()
        valid = True
        for start, dir in lazors:
            path = trace_laser(temp_grid, start, dir)
            all_hits.update(path)
            if not all(p in all_hits for p in targets):
                valid = False
                break

        if valid:
            print(f"\n找到解！尝试次数: {progress.n}")
            return temp_grid

    print(f"\n已尝试{min(max_attempts, len(slot_combinations) * total_perms)}次，未找到解")
    return None


# --------------------------
# 可视化模块
# --------------------------
def visualize_solution(grid, data, save_path=None):
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)

    ax.set_xlim(0, len(grid[0]))
    ax.set_ylim(0, len(grid))
    ax.invert_yaxis()
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Lazor Puzzle Solution", pad=20)

    for i in range(len(grid)):
        for j in range(len(grid[0])):
            rect = patches.Rectangle(
                (j, i), 1, 1,
                facecolor='white' if grid[i][j] != 'x' else 'black',
                edgecolor='gray',
                linewidth=0.5
            )
            ax.add_patch(rect)

    block_colors = {
        'A': ('#4682B4', 'white'),
        'B': ('#708090', 'white'),
        'C': ('#32CD32', 'black')
    }
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            cell = grid[i][j]
            if cell in block_colors:
                ax.add_patch(patches.Rectangle(
                    (j, i), 1, 1,
                    facecolor=block_colors[cell][0],
                    edgecolor='black',
                    linewidth=1
                ))
                ax.text(j + 0.5, i + 0.5, cell,
                        ha='center', va='center',
                        fontsize=14, color=block_colors[cell][1],
                        weight='bold')

    for start, dir in data['lazors']:
        path = trace_laser(grid, start, dir)
        if path:
            x = [p[0][0] / 2 for p in path]
            y = [p[0][1] / 2 for p in path]
            ax.plot(x, y, 'r-', linewidth=2, alpha=0.7)
            visualize_laser_path_with_steps(ax, path)  # ⬅ 添加路径编号

    for (x, y), (dx, dy) in data['lazors']:
        ax.plot(x / 2, y / 2, 's', color='red', markersize=10, markeredgecolor='black')
        ax.arrow(x / 2, y / 2, dx * 0.3, dy * 0.3,
                 head_width=0.2, head_length=0.15,
                 fc='red', ec='red')

    for x, y in data['points']:
        ax.plot(x / 2, y / 2, 'o',
                markersize=12,
                markeredgecolor='black',
                markerfacecolor='#00FF00',
                alpha=0.8)

    legend_elements = [
        patches.Patch(facecolor='#4682B4', edgecolor='black', label='反射块 (A)'),
        patches.Patch(facecolor='#708090', edgecolor='black', label='阻挡块 (B)'),
        patches.Patch(facecolor='#32CD32', edgecolor='black', label='折射块 (C)'),
        plt.Line2D([0], [0], marker='o', color='w', label='目标点',
                   markerfacecolor='green', markersize=10, markeredgecolor='black'),
        plt.Line2D([0], [0], marker='s', color='w', label='激光起点',
                   markerfacecolor='red', markersize=10, markeredgecolor='black'),
        plt.Line2D([0], [0], color='red', lw=2, label='激光路径')
    ]
    ax.legend(handles=legend_elements,
              loc='upper right',
              bbox_to_anchor=(1.35, 1),
              framealpha=1)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()



# --------------------------
# 主程序
# --------------------------
if __name__ == '__main__':
    INPUT_FILE = r"D:\\tool\\pycharm\\file\\Lazor Project\\bff_files\\mad_1.bff"
    MAX_ATTEMPTS = 100000
    OUTPUT_IMAGE = "solution.png"

    print("=== Lazor Puzzle Solver ===")
    print(f"加载文件: {INPUT_FILE}")

    try:
        start_load = time.time()
        puzzle_data = parse_bff_file(INPUT_FILE)
        load_time = time.time() - start_load
        print(f"文件加载成功 (耗时: {load_time:.2f}s)")

        print("\n=== 谜题信息 ===")
        print(f"网格尺寸: {len(puzzle_data['grid'])}行 x {len(puzzle_data['grid'][0])}列")
        print(f"需要放置: A={puzzle_data['blocks']['A']} B={puzzle_data['blocks']['B']} C={puzzle_data['blocks']['C']}")
        print(f"目标点: {puzzle_data['points']}")
        print(f"激光数量: {len(puzzle_data['lazors'])}")

        print("\n=== 开始求解 ===")
        start_solve = time.time()
        solution = solve_with_bruteforce(puzzle_data, MAX_ATTEMPTS)
        solve_time = time.time() - start_solve

        if solution:
            print(f"\n求解成功！总耗时: {solve_time:.2f}秒")

            print("\n验证解...")
            all_hits = set()
            for start, dir in puzzle_data['lazors']:
                path = trace_laser(solution, start, dir)
                all_hits.update(path)

            missed = [p for p in puzzle_data['points'] if p not in all_hits]
            if not missed:
                print("验证通过！所有目标点被命中")
                print("\n生成可视化结果...")
                visualize_solution(solution, puzzle_data, OUTPUT_IMAGE)
            else:
                print(f"验证失败！未命中点: {missed}")
        else:
            print(f"\n求解失败！总耗时: {solve_time:.2f}秒")
            print("建议：\n1. 增加MAX_ATTEMPTS值\n2. 检查谜题文件是否正确\n3. 确认谜题是否有解")

    except FileNotFoundError as e:
        print(f"错误: {str(e)}")
    except ValueError as e:
        print(f"文件格式错误: {str(e)}")
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"未知错误: {str(e)}")