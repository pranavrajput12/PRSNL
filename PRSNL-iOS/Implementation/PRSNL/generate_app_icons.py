#!/usr/bin/env python3
"""
Simple script to generate app icons for PRSNL iOS app.
This creates basic red circular icons with a brain symbol.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon(size, filename):
    """Create a simple app icon with the specified size."""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw red circle background
    margin = size // 20  # Small margin
    draw.ellipse([margin, margin, size - margin, size - margin], 
                 fill=(220, 20, 60, 255))  # Crimson red
    
    # Draw a simple brain-like shape (simplified)
    center_x, center_y = size // 2, size // 2
    brain_size = size // 3
    
    # Draw brain outline (simplified as overlapping circles)
    brain_color = (255, 255, 255, 255)  # White
    
    # Left hemisphere
    left_x = center_x - brain_size // 4
    draw.ellipse([left_x - brain_size//2, center_y - brain_size//2,
                  left_x + brain_size//2, center_y + brain_size//2],
                 outline=brain_color, width=max(1, size//40))
    
    # Right hemisphere
    right_x = center_x + brain_size // 4
    draw.ellipse([right_x - brain_size//2, center_y - brain_size//2,
                  right_x + brain_size//2, center_y + brain_size//2],
                 outline=brain_color, width=max(1, size//40))
    
    # Add "P" in the center for PRSNL
    try:
        font_size = max(12, size // 6)
        font = ImageFont.load_default()
        text = "P"
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2
        
        draw.text((text_x, text_y), text, fill=brain_color, font=font)
    except:
        # Fallback if font loading fails
        pass
    
    # Save the image
    img.save(filename, 'PNG')
    print(f"Created {filename} ({size}x{size})")

def main():
    """Generate all required app icon sizes."""
    # Define required sizes
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
    
    # Create the AppIcon.appiconset directory if it doesn't exist
    icon_dir = "Assets.xcassets/AppIcon.appiconset"
    os.makedirs(icon_dir, exist_ok=True)
    
    # Generate each icon
    for size, filename in icon_sizes:
        filepath = os.path.join(icon_dir, filename)
        create_app_icon(size, filepath)
    
    print(f"\nGenerated {len(icon_sizes)} app icons in {icon_dir}/")
    print("You can now build and deploy your app with proper icons!")

if __name__ == "__main__":
    main()