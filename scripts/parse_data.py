import csv
import math

# File paths
INPUT_FILE = "../data/raw/usa.txt"
INTERSECTIONS_CSV = "../docker/import/intersections.csv"
ROADS_CSV = "../docker/import/roads.csv"

def parse_data():
    print("Reading usa.txt...")
    
    with open(INPUT_FILE, 'r') as f:
        lines = f.readlines()
    
    # Line 1: header
    header = lines[0].strip().split()
    num_vertices = int(header[0])
    num_edges = int(header[1])
    
    print(f"Total intersections: {num_vertices}")
    print(f"Total roads: {num_edges}")
    
    # Parse vertices (lines 2 to num_vertices + 1)
    vertices = {}
    print("Parsing intersections...")
    
    for i in range(1, num_vertices + 1):
        parts = lines[i].strip().split()
        vertex_id = int(parts[0])
        x = int(parts[1])
        y = int(parts[2])
        vertices[vertex_id] = (x, y)
    
    # Parse edges (remaining lines)
    edges = []
    print("Parsing roads...")
    
    for i in range(num_vertices + 1, len(lines)):
        parts = lines[i].strip().split()
        if len(parts) >= 2:
            source = int(parts[0])
            target = int(parts[1])
            edges.append((source, target))
    
    print(f"Parsed {len(vertices)} intersections")
    print(f"Parsed {len(edges)} roads")
    
    # Write intersections.csv
    print("Writing intersections.csv...")
    
    with open(INTERSECTIONS_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'x', 'y'])
        for vertex_id, (x, y) in vertices.items():
            writer.writerow([vertex_id, x, y])
    
    # Write roads.csv with distance
    print("Writing roads.csv...")
    
    with open(ROADS_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'target', 'distance'])
        for source, target in edges:
            x1, y1 = vertices[source]
            x2, y2 = vertices[target]
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            distance = round(distance, 2)
            writer.writerow([source, target, distance])
    
    print("Done!")
    print(f"Files saved:")
    print(f"  - {INTERSECTIONS_CSV}")
    print(f"  - {ROADS_CSV}")

if __name__ == "__main__":
    parse_data()