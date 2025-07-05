import os

# Какие расширения считать (можно менять по желанию)
extensions = {'.py'}

# Папки, которые игнорируем
ignored_dirs = {'OLD_VERSION', '.git', 'node_modules', '__pycache__', '.venv', 'venv', '.idea', '.vscode', 'build', 'dist', '.mypy_cache'}

# Путь к корню проекта
project_path = '.'

total_lines = 0
file_count = 0

for root, dirs, files in os.walk(project_path):
    # Убираем нежелательные директории из обхода
    dirs[:] = [d for d in dirs if d not in ignored_dirs]

    for file in files:
        _, ext = os.path.splitext(file)
        if ext.lower() in extensions:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    file_count += 1
            except Exception as e:
                print(f"Не удалось прочитать {file_path}: {e}")

print(f'Файлов прочитано: {file_count}')
print(f'Всего строк кода: {total_lines}')