import os
import shutil

images_dir = r"E:\images"
games_dir = r"E:\games"

# Loop through all folders in games directory
for game_name in os.listdir(games_dir):
    game_folder = os.path.join(games_dir, game_name)
    
    # Skip if not a directory
    if not os.path.isdir(game_folder):
        continue
    
    # Source image path
    source_image = os.path.join(images_dir, f"{game_name}.png")
    
    # Destination image path
    destination_image = os.path.join(game_folder, "banner.png")
    
    # Copy if image exists
    if os.path.exists(source_image):
        shutil.copy2(source_image, destination_image)
        print(f"Copied: {game_name}")
    else:
        print(f"Missing image for: {game_name}")

print("Done.")