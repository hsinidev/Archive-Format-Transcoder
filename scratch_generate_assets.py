import os
from PIL import Image, ImageDraw

def generate_icons():
    assets_dir = os.path.join(os.getcwd(), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Create high-res 256x256 image
    size = 256
    img = Image.new("RGBA", (size, size), (10, 12, 16, 255))  # #0A0C10
    draw = ImageDraw.Draw(img)
    
    # Draw rounded dark card box (#1B202E) with border (#273044)
    margin = 16
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=32,
        fill=(27, 32, 46, 255),
        outline=(39, 48, 68, 255),
        width=4
    )
    
    # Draw stylized archive box / layers with Volt Amber (#FFAB00) & Electric Cyan (#00E5FF)
    # Box top layer
    draw.rounded_rectangle([50, 60, 206, 100], radius=10, fill=(255, 171, 0, 255)) # #FFAB00
    # Zipper / teeth accent in electric cyan
    for i in range(65, 195, 20):
        draw.rectangle([i, 75, i+10, 85], fill=(10, 12, 16, 255))
    
    # Middle layer
    draw.rounded_rectangle([60, 110, 196, 150], radius=8, fill=(0, 229, 255, 230)) # #00E5FF
    
    # Bottom layer
    draw.rounded_rectangle([70, 160, 186, 196], radius=6, fill=(255, 171, 0, 200))
    
    # Save PNG
    png_path = os.path.join(assets_dir, "icon.png")
    img.save(png_path, "PNG")
    
    # Save ICO with multiple sizes
    ico_path = os.path.join(assets_dir, "icon.ico")
    img.save(ico_path, format="ICO", sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
    print(f"Icons generated at {png_path} and {ico_path}")

if __name__ == "__main__":
    generate_icons()
