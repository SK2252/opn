import os

def generate_tree(startpath, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(startpath):
            # Modify dirs in-place to skip unwanted directories
            dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', '.idea', '.vscode', 'node_modules', '.pytest_cache', 'qdrant_data']]
            
            level = root.replace(startpath, '').count(os.sep)
            if level == 0:
                f.write(f'{os.path.basename(root)}/\n')
            else:
                indent = '│   ' * (level - 1) + '├── '
                f.write(f'{indent}{os.path.basename(root)}/\n')
            
            subindent = '│   ' * level + '├── '
            for file in files:
                f.write(f'{subindent}{file}\n')

if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Generating tree for: {current_dir}")
    generate_tree(current_dir, 'project_structure.txt')
    print("Tree generated in project_structure.txt")
