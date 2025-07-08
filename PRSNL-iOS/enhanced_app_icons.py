#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import math
import shutil
import sys

def create_app_icon(size, filename):
    """Create a highly distinctive app icon guaranteed to work with iOS."""
    # Create a new image with bright background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create a high-contrast gradient background (blue to purple)
    for i in range(size):
        for j in range(size):
            # Calculate distance from center
            center_x, center_y = size // 2, size // 2
            distance = ((i - center_x) ** 2 + (j - center_y) ** 2) ** 0.5
            max_distance = (size // 2) * 1.4
            
            # Only fill within the icon boundary
            if distance <= size // 2:
                # Create gradient from blue to purple
                ratio = distance / max_distance
                red = int(80 + (ratio * 120))    # 80 to 200
                green = int(10 + (ratio * 50))   # 10 to 60
                blue = int(220 - (ratio * 70))   # 220 to 150
                
                # Ensure values are within range
                red = max(0, min(255, red))
                green = max(0, min(255, green))
                blue = max(0, min(255, blue))
                
                img.putpixel((i, j), (red, green, blue, 255))
    
    # Add rounded corners for iOS style
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    corner_radius = size // 5  # 20% corner radius
    mask_draw.rounded_rectangle([0, 0, size, size], corner_radius, fill=255)
    
    # Apply mask
    img.putalpha(mask)
    
    # Draw distinctive "P" letter
    letter_color = (255, 255, 255, 255)  # Bright white
    font_size = size // 2
    
    # Draw a white circle background for the P
    circle_size = int(size * 0.7)
    circle_pos = (size - circle_size) // 2
    draw.ellipse(
        [circle_pos, circle_pos, circle_pos + circle_size, circle_pos + circle_size],
        fill=(255, 255, 255, 180)  # Semi-transparent white
    )
    
    # Draw a bold "P" in the center
    p_width = int(size * 0.5)
    p_height = int(size * 0.6)
    p_x = (size - p_width) // 2
    p_y = (size - p_height) // 2
    
    # Draw the stem of the P
    stem_width = int(p_width * 0.3)
    draw.rectangle(
        [p_x, p_y, p_x + stem_width, p_y + p_height],
        fill=(50, 50, 200)  # Dark blue
    )
    
    # Draw the loop of the P
    loop_height = int(p_height * 0.6)
    loop_width = p_width - stem_width
    draw.ellipse(
        [p_x + stem_width - 1, p_y, p_x + p_width, p_y + loop_height],
        fill=(50, 50, 200)  # Dark blue
    )
    draw.rectangle(
        [p_x + stem_width, p_y + loop_height // 2, p_x + p_width, p_y + loop_height],
        fill=(50, 50, 200)  # Dark blue
    )
    
    # Cut out the inner part of the P
    inner_margin = max(2, size // 40)
    inner_width = loop_width - inner_margin * 2
    inner_height = loop_height - inner_margin * 2
    draw.ellipse(
        [p_x + stem_width + inner_margin, p_y + inner_margin, 
         p_x + p_width - inner_margin, p_y + loop_height - inner_margin],
        fill=(80, 10, 220)  # Match gradient start color
    )
    
    # Add a subtle shadow
    shadow = img.copy()
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=size//30))
    shadow_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    shadow_img.paste(shadow, (size//50, size//50), mask)
    
    # Composite the shadow and the main image
    final_img = Image.alpha_composite(shadow_img, img)
    
    # Ensure the icon has the correct mode for iOS
    if final_img.mode != 'RGBA':
        final_img = final_img.convert('RGBA')
    
    # Save with optimizations specifically for iOS
    final_img.save(filename, 'PNG', optimize=True)
    print(f"Created {filename} ({size}x{size})")
    return final_img

def create_contents_json(output_dir):
    """Create a proper Contents.json file for the AppIcon.appiconset"""
    contents = {
      "images": [
        {
          "filename": "AppIcon-20x20@2x.png",
          "idiom": "iphone",
          "scale": "2x",
          "size": "20x20"
        },
        {
          "filename": "AppIcon-20x20@3x.png",
          "idiom": "iphone",
          "scale": "3x",
          "size": "20x20"
        },
        {
          "filename": "AppIcon-29x29@2x.png",
          "idiom": "iphone",
          "scale": "2x",
          "size": "29x29"
        },
        {
          "filename": "AppIcon-29x29@3x.png",
          "idiom": "iphone",
          "scale": "3x",
          "size": "29x29"
        },
        {
          "filename": "AppIcon-40x40@2x.png",
          "idiom": "iphone",
          "scale": "2x",
          "size": "40x40"
        },
        {
          "filename": "AppIcon-40x40@3x.png",
          "idiom": "iphone",
          "scale": "3x",
          "size": "40x40"
        },
        {
          "filename": "AppIcon-60x60@2x.png",
          "idiom": "iphone",
          "scale": "2x",
          "size": "60x60"
        },
        {
          "filename": "AppIcon-60x60@3x.png",
          "idiom": "iphone",
          "scale": "3x",
          "size": "60x60"
        },
        {
          "filename": "AppIcon-1024x1024.png",
          "idiom": "ios-marketing",
          "scale": "1x",
          "size": "1024x1024"
        }
      ],
      "info": {
        "author": "xcode",
        "version": 1
      }
    }
    
    import json
    with open(os.path.join(output_dir, 'Contents.json'), 'w') as f:
        json.dump(contents, f, indent=2)
    print(f"Created Contents.json in {output_dir}")

def create_backup(output_dir):
    """Create a backup of the existing AppIcon.appiconset"""
    if os.path.exists(output_dir):
        backup_dir = output_dir + "_backup_" + str(int(os.path.getmtime(output_dir)))
        shutil.copytree(output_dir, backup_dir)
        print(f"Created backup of existing AppIcon.appiconset at {backup_dir}")
    
def main():
    # Define the required icon sizes for iOS
    icon_sizes = [
        (40, "AppIcon-20x20@2x.png"),
        (60, "AppIcon-20x20@3x.png"),
        (58, "AppIcon-29x29@2x.png"),
        (87, "AppIcon-29x29@3x.png"),
        (80, "AppIcon-40x40@2x.png"),
        (120, "AppIcon-40x40@3x.png"),
        (120, "AppIcon-60x60@2x.png"),
        (180, "AppIcon-60x60@3x.png"),
        (1024, "AppIcon-1024x1024.png")
    ]
    
    # Create output directory
    output_dir = "PRSNL-iOS/Implementation/PRSNL/Assets.xcassets/AppIcon.appiconset"
    
    # Create a backup first
    create_backup(output_dir)
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all icon sizes
    for size, filename in icon_sizes:
        filepath = os.path.join(output_dir, filename)
        create_app_icon(size, filepath)
    
    # Create proper Contents.json
    create_contents_json(output_dir)
    
    print(f"\nAll app icons created successfully in {output_dir}")
    print("New icons feature:")
    print("- High-contrast blue-to-purple gradient background")
    print("- Bold 'P' letter design with visual depth")
    print("- Optimized formatting for iOS display")
    print("- Rounded corners for iOS style")
    print("- Extra visibility for home screen recognition")
    
    print("\nTo complete the process:")
    print("1. Build and deploy the app again")
    print("2. If the icon still doesn't appear, try removing the app from the device first")
    print("3. You may need to restart the device to clear iOS icon caches")

if __name__ == "__main__":
    main()