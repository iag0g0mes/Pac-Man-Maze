import random
import sys

sys.setrecursionlimit(10000)

def generate_maze(size):
    grid = [[1 for _ in range(size)] for _ in range(size)]

    # Recursive backtracker to carve paths (0)
    def carve_passages(cx, cy):
        #Up, Down, Left, Right
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            # If the neighbor is within bounds and is still a wall
            if 0 <= nx < size and 0 <= ny < size and grid[ny][nx] == 1:
                # Knock down the wall between current cell and neighbor
                grid[cy + dy // 2][cx + dx // 2] = 0
                grid[ny][nx] = 0
                carve_passages(nx, ny)

    # Start at top-left
    grid[0][0] = 0
    carve_passages(0, 0)

    grid[size-1][size-1] = 0
    grid[size-1][size-2] = 0
    grid[size-2][size-1] = 0

    print(f"### {size}x{size} Map")
    print(f"START 0 0 EXIT {size-1} {size-1}")
    for row in grid:
        print("".join(str(cell) for cell in row))
    print("\n")


sizes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
for s in sizes:
    generate_maze(s)