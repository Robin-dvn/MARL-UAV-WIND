from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def display_images_side_by_side(image_path1, image_path2):
    """
    Displays two PNG images side-by-side horizontally using Plotly.
    No legend or title will be shown, and axes will be hidden.

    Args:
        image_path1 (str): Filesystem path to the first PNG image.
        image_path2 (str): Filesystem path to the second PNG image.
    """
    if not os.path.exists(image_path1):
        print(f"Error: Image not found at {image_path1}")
        return
    if not os.path.exists(image_path2):
        print(f"Error: Image not found at {image_path2}")
        return

    # Load images
    try:
        img1 = Image.open(image_path1)
        img2 = Image.open(image_path2)
    except Exception as e:
        print(f"Error opening images: {e}")
        return

    # Create subplots: 1 row, 2 cols
    fig = make_subplots(rows=1, cols=2)

    # Add first image
    fig.add_trace(go.Image(z=img1), row=1, col=1)

    # Add second image
    fig.add_trace(go.Image(z=img2), row=1, col=2)

    # Update layout to remove legend and title, and hide axes
    fig.update_layout(
        showlegend=False,
        title_text=None,
        xaxis1_visible=False,
        yaxis1_visible=False,
        xaxis2_visible=False,
        yaxis2_visible=False,
        margin=dict(l=0, r=0, t=0, b=0) # Remove margins
    )
    fig.show()

if __name__ == '__main__':
    # --- IMPORTANT ---
    # Replace these with the actual paths to your PNG images.
    # Example:
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # path_to_image1 = os.path.join(script_dir, '..', 'assets', 'your_image1.png')
    # path_to_image2 = os.path.join(script_dir, '..', 'assets', 'your_image2.png')

    # Using placeholder paths - YOU MUST CHANGE THESE
    # For demonstration, dummy PNGs will be created if these exact paths are used and files don't exist.
    placeholder_image1 = "C:\\Users\\r.davenne\\Documents\\ODREE\\Sujets\\Sujet1_Patrol_wind\\images\\paraview.png"
    placeholder_image2 = "C:\\Users\\r.davenne\\Documents\\ODREE\\Sujets\\Sujet1_Patrol_wind\\images\\paraview90.png"

    print(f"Attempting to load images:\n1. {placeholder_image1}\n2. {placeholder_image2}")
    print("Please ensure these paths are correct or update them in the script.")

    # Create dummy PNG files if default placeholders are used and files don't exist
    # This is for demonstration purposes; replace with your actual image paths.
    images_to_display = []

    for i, placeholder_path in enumerate([placeholder_image1, placeholder_image2]):
        if not os.path.exists(placeholder_path):
            if placeholder_path == f"dummy_image_{i+1}.png": # Only create if it's the default dummy name
                try:
                    img_dummy = Image.new('RGB', (200, 200), color = ('red' if i == 0 else 'blue'))
                    draw = ImageDraw.Draw(img_dummy)
                    draw.text((10,10), f"Image {i+1}", fill=(255,255,255) if i == 0 else (0,0,0))
                    img_dummy.save(placeholder_path)
                    print(f"Created {placeholder_path} as a placeholder.")
                    images_to_display.append(placeholder_path)
                except ImportError:
                    print(f"Pillow (PIL) is needed to create dummy image {placeholder_path}. Please install it: pip install Pillow")
                    break # Stop if Pillow is not available
                except Exception as e:
                    print(f"Could not create {placeholder_path}: {e}")
                    break
            else:
                print(f"Image specified at {placeholder_path} not found.")
        else:
            images_to_display.append(placeholder_path)

    if len(images_to_display) == 2:
        display_images_side_by_side(images_to_display[0], images_to_display[1])
    else:
        print("Could not find or create two images to display. Please check paths or install Pillow.")
