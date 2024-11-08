import os

def create_file(filename, size_kb):
    """Creates a file of specified size in kilobytes."""

    size_bytes = size_kb * 1024
    with open(filename, 'w') as f:
        f.write('a' * size_bytes)

if __name__ == "__main__":
    create_file('my_20kb_file.txt', 20)