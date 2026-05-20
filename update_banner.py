import os
import re

htdocs_dir = r"C:\xampp\htdocs"

# Pattern to match: assets/images/banner_{game_name}.jpg
pattern = r'assets/images/banner_(.+?)\.jpg'

for batch_name in os.listdir(htdocs_dir):
    batch_path = os.path.join(htdocs_dir, batch_name)
    
    if not os.path.isdir(batch_path):
        continue
    
    index_file = os.path.join(batch_path, "index.php")
    
    if not os.path.exists(index_file):
        continue
    
    # Read file
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace paths
    def replace_match(match):
        game_name = match.group(1)
        return f"games/{game_name}/banner.png"
    
    new_content = re.sub(pattern, replace_match, content)
    
    # Write back only if changed
    if new_content != content:
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated: {batch_name}/index.php")
    else:
        print(f"No changes: {batch_name}/index.php")

print("Done.")