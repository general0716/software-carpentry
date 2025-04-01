def parse_bff_file(filename):
    """
    解析 .bff 文件，提取网格信息、激光器、目标点等
    """
    with open(filename, 'r') as file:
        lines = file.readlines()

    grid = []
    blocks = {'A': 0, 'B': 0, 'C': 0}
    lazors = []
    points = []

    reading_grid = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith("GRID START"):
            reading_grid = True
            continue
        elif line.startswith("GRID STOP"):
            reading_grid = False
            continue

        if reading_grid:
            row = line.replace(" ", "")
            grid.append(list(row))
        elif line.startswith("A"):
            blocks['A'] = int(line.split()[1])
        elif line.startswith("B"):
            blocks['B'] = int(line.split()[1])
        elif line.startswith("C"):
            blocks['C'] = int(line.split()[1])
        elif line.startswith("L"):
            parts = line.split()
            pos = (int(parts[1]), int(parts[2]))
            direction = (int(parts[3]), int(parts[4]))
            lazors.append((pos, direction))
        elif line.startswith("P"):
            parts = line.split()
            point = (int(parts[1]), int(parts[2]))
            points.append(point)

    return {
        "grid": grid,
        "blocks": blocks,
        "lazors": lazors,
        "points": points
    }

def simulate_lazor_path(grid, lazors, max_steps=100):
    """
    在细分8×8坐标系中模拟激光路径，不考虑反射，仅直线追踪
    """
    grid_width = len(grid[0]) * 2
    grid_height = len(grid) * 2
    paths = []

    for (x, y), (dx, dy) in lazors:
        path = [(x, y)]
        steps = 0

        while 0 <= x < grid_width and 0 <= y < grid_height and steps < max_steps:
            x += dx
            y += dy
            path.append((x, y))
            steps += 1

        paths.append(path)

    return paths

# 示例使用（将路径改为你实际的 .bff 文件路径）
filename = r"D:\tool\pycharm\file\Lazor Project\bff_files\mad_1.bff"


# 解析文件
bff_data = parse_bff_file(filename)

# 输出基础信息
print("🔲 Grid Size: {}x{}".format(len(bff_data["grid"]), len(bff_data["grid"][0])))
print("🧱 Block Counts:", bff_data["blocks"])
print("🔦 Lazors:", bff_data["lazors"])
print("🎯 Target Points:", bff_data["points"])
print("🗺️ Grid Layout:")
for row in bff_data["grid"]:
    print("".join(row))

# 模拟激光路径
paths = simulate_lazor_path(bff_data["grid"], bff_data["lazors"])

# 输出路径
print("\n📍 Lazor Paths:")
for i, path in enumerate(paths):
    print(f"  Lazor {i+1}:")
    for point in path:
        print("   ", point)
