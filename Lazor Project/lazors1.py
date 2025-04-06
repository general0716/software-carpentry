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
# 激光追踪逻辑 (关键修复)
# --------------------------
def get_block(grid, point, direction):
    """改进的方块检测，考虑激光方向"""
    x, y = point
    dx, dy = direction
    
    # 计算实际碰撞的方块
    if x % 2 == 0 and y % 2 == 1:  # 水平表面
        row = (y + (1 if dy > 0 else -1)) // 2
        col = x // 2
    elif x % 2 == 1 and y % 2 == 0:  # 垂直表面
        row = y // 2
        col = (x + (1 if dx > 0 else -1)) // 2
    else:
        return None
        
    if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
        return grid[row][col]
    return None

def calculate_interaction(block_type, direction, collision_point):
    dx, dy = direction
    x, y = collision_point

    if block_type == 'A':  # 反射块
        if x % 2 == 0:  # 水平表面
            return [(-dx, dy)]
        else:  # 垂直表面
            return [(dx, -dy)]

    elif block_type == 'B':  # 阻挡块
        return []

    elif block_type == 'C':  # 折射块（关键修复）
        if x % 2 == 0:  # 水平表面
            return [(dx, dy), (dx, -dy)]  # 透射 + 反射
        else:  # 垂直表面
            return [(dx, dy), (-dx, dy)]  # 透射 + 反射

    return [direction]

def trace_laser(grid, start_pos, start_dir, max_reflections=50):
    path = []
    visited = set()
    queue = [(start_pos, start_dir)]
    
    while queue and len(visited) < max_reflections:
        pos, dir = queue.pop(0)
        if (pos, dir) in visited:
            continue
        visited.add((pos, dir))
        
        x, y = pos
        dx, dy = dir
        current_path = []
        
        while True:
            current_path.append((x, y))
            
            # 边界检测
            if x < 0 or y < 0 or x >= len(grid[0])*2 or y >= len(grid)*2:
                break
                
            # 获取当前方块（改进的检测逻辑）
            block = get_block(grid, (x, y), (dx, dy))
            
            if block in ['A', 'B', 'C']:
                # 处理方块交互
                new_dirs = calculate_interaction(block, (dx, dy), (x, y))
                for ndx, ndy in new_dirs:
                    new_pos = (x + ndx, y + ndy)
                    queue.append((new_pos, (ndx, ndy)))
                break
                
            # 移动到下一个位置
            x += dx
            y += dy
            
        path.extend(current_path)
        
    return path


# --------------------------
# 穷举求解器（保持不变）
# --------------------------
def solve_with_bruteforce(data, max_attempts=100000):
    # ...（保持原有实现不变）...


# --------------------------
# 可视化模块（保持不变）
# --------------------------
def visualize_solution(grid, data, save_path=None):
    # ...（保持原有实现不变）...


# --------------------------
# 主程序（保持不变）
# --------------------------
if __name__ == '__main__':
    INPUT_FILE = r"your_puzzle.bff"
    MAX_ATTEMPTS = 100000
    OUTPUT_IMAGE = "solution.png"

    # ...（保持原有执行逻辑不变）...
    