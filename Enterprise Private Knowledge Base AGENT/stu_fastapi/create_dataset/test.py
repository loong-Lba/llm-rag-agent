import os
path_base = os.path.dirname(os.path.dirname(__file__))
csv_path = os.path.join(path_base, 'datasets', 'motogpand675sr.csv')
print(f"CSV路径: {csv_path}")
print(f"文件存在: {os.path.exists(csv_path)}")