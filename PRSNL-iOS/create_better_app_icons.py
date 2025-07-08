#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon(size, filename):
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create a modern gradient background
    for i in range(size):
        for j in range(size):
            # Calculate distance from center
            center_x, center_y = size // 2, size // 2
            distance = ((i - center_x) ** 2 + (j - center_y) ** 2) ** 0.5
            max_distance = (size // 2) * 1.4
            
            if distance <= size // 2:
                # Create gradient from red to dark red
                ratio = distance / max_distance
                red = int(220 - (ratio * 60))  # 220 to 160
                green = int(50 - (ratio * 30))   # 50 to 20
                blue = int(50 - (ratio * 30))    # 50 to 20
                
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
    
    # Add brain icon in center
    brain_size = size // 3
    brain_x = (size - brain_size) // 2
    brain_y = (size - brain_size) // 2
    
    # Draw stylized brain/knowledge symbol
    # Main circle
    draw.ellipse([brain_x, brain_y, brain_x + brain_size, brain_y + brain_size], 
                outline='white', width=max(2, size//40), fill=None)
    
    # Inner lines representing knowledge/neural networks
    center_x, center_y = brain_x + brain_size//2, brain_y + brain_size//2
    line_width = max(1, size//60)
    
    # Draw interconnected lines
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        import math
        rad = math.radians(angle)
        start_x = center_x + (brain_size//4) * math.cos(rad)
        start_y = center_y + (brain_size//4) * math.sin(rad)
        end_x = center_x + (brain_size//3) * math.cos(rad)
        end_y = center_y + (brain_size//3) * math.sin(rad)
        draw.line([start_x, start_y, end_x, end_y], fill='white', width=line_width)
    
    # Central dot
    dot_size = max(2, size//30)
    draw.ellipse([center_x - dot_size, center_y - dot_size, 
                 center_x + dot_size, center_y + dot_size], fill='white')
    
    # Save the image
    img.save(filename, 'PNG', optimize=True)
    print(f"Created {filename} ({size}x{size})")

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
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all icon sizes
    for size, filename in icon_sizes:
        filepath = os.path.join(output_dir, filename)
        create_app_icon(size, filepath)
    
    print(f"\nAll app icons created successfully in {output_dir}")
    print("Icons feature:")
    print("- Modern gradient background (red to dark red)")
    print("- Rounded corners for iOS style")
    print("- Stylized brain/knowledge network symbol")
    print("- High quality PNG format")

if __name__ == "__main__":
    main()