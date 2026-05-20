import os
import shutil

htdocs_dir = r"C:\xampp\htdocs"
images_dir = r"E:\images"

# Loop through batch folders
for batch_name in os.listdir(htdocs_dir):
    batch_path = os.path.join(htdocs_dir, batch_name)
    
    if not os.path.isdir(batch_path):
        continue
    
    games_path = os.path.join(batch_path, "games")
    
    # Skip if no games folder
    if not os.path.isdir(games_path):
        continue
    
    # Loop through game folders inside batch
    for game_name in os.listdir(games_path):
        game_folder = os.path.join(games_path, game_name)
        
        if not os.path.isdir(game_folder):
            continue
        
        source_image = os.path.join(images_dir, f"{game_name}.png")
        destination_image = os.path.join(game_folder, "banner.png")
        
        if os.path.exists(source_image):
            shutil.copy2(source_image, destination_image)
            print(f"Copied: {batch_name} -> {game_name}")
        else:
            print(f"Missing: {game_name}")

print("Done.")