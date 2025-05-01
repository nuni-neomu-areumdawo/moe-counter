import os
import random
from PIL import Image

random.seed(0)
THEME_BASE_DIR = "theme"

def ceil(x : float) -> int:
    return round(x + 0.5)

# --- Helper Functions ---
def find_image_path(folder, digit):
    """Finds the image file for a given digit, trying common extensions."""
    extensions_to_try = ['.gif', '.png', '.jpg', '.jpeg']
    for ext in extensions_to_try:
        path = os.path.join(folder, str(digit) + ext)
        if os.path.exists(path):
            return path
    return None

def list_themes(base_dir):
    """Lists valid theme subdirectories within the base directory."""
    if not os.path.isdir(base_dir):
        return []
    
    themes = [d for d in os.listdir(base_dir)

    if os.path.isdir(os.path.join(base_dir, d))]
    return sorted(themes)

# --- Core Reusable Function ---
def create_stitched_image(
    number_string,
    output_filename_base="combined_output",
    scale_factor=1.0,
    mode='theme',
    theme_name=None,
    base_theme_dir=THEME_BASE_DIR,
    resize_to_max_height=True,
    output_dir="./output"
):
    available_themes = list_themes(base_theme_dir)
    theme_folder_path = None
    selected_random_theme_name = None

    if mode == 'theme':
        if not theme_name or not base_theme_dir:
            print("Error: 'theme_name' and 'base_theme_dir' required for mode 'theme'.")
            return None
        theme_folder_path = os.path.join(base_theme_dir, theme_name)
        if not os.path.isdir(theme_folder_path):
            print(f"Error: Theme folder not found: {theme_folder_path}")
            return None
        print(f"Using fixed theme: {theme_name}")
    elif mode == 'random_theme':
        if not base_theme_dir or not available_themes:
            print("Error: 'base_theme_dir' and available themes required for 'random_theme'.")
            return None
        selected_random_theme_name = random.choice(available_themes)
        theme_folder_path = os.path.join(base_theme_dir, selected_random_theme_name)
        print(f"Using randomly selected theme: {selected_random_theme_name}")
    elif mode == 'random_digits':
        if not base_theme_dir or not available_themes:
            print("Error: 'base_theme_dir' and available themes required for 'random_digits'.")
            return None
        print(f"Using random digits from available themes: {', '.join(available_themes)}")
    else:
        print(f"Error: Invalid mode '{mode}'.")
        return None

    image_paths_info = [] 
    max_original_height = 0
    found_any_image = False

    for digit in number_string:
        image_path = None
        source_theme = None

        if mode == 'theme' or mode == 'random_theme':
            image_path = find_image_path(theme_folder_path, digit)
            source_theme = theme_name if mode == 'theme' else selected_random_theme_name
        elif mode == 'random_digits':
            possible_paths = []
            possible_themes = []
            for t_name in available_themes:
                t_path = os.path.join(base_theme_dir, t_name)
                found_path = find_image_path(t_path, digit)
                if found_path:
                    possible_paths.append(found_path)
                    possible_themes.append(t_name)
            if possible_paths:
                chosen_index = random.randrange(len(possible_paths))
                image_path = possible_paths[chosen_index]
                source_theme = possible_themes[chosen_index]

        if image_path:
            try:
                with Image.open(image_path) as img:
                    w, h = img.size
                    image_paths_info.append({
                        'path': image_path,
                        'orig_w': w,
                        'orig_h': h,
                        'source_theme': source_theme,
                        'digit': digit 
                    })
                    if h > max_original_height:
                        max_original_height = h
                    found_any_image = True
                    print(f"  - Digit '{digit}': Found {os.path.basename(image_path)} (Theme: {source_theme}, Orig Size: {w}x{h})")
            except Exception as e:
                print(f"  - Warning: Could not read size for {image_path}. Skipping. Error: {e}")
        else:
            print(f"  - Warning: Image for digit '{digit}' not found. Skipping.")

    if not found_any_image:
        print("\nError: No valid images found for the number string.")
        return None

    if max_original_height == 0:
        print("\nError: Maximum original height is 0, cannot proceed.")
        return None

    images_data = [] 
    total_stitched_width = 0
    final_stitch_height = 0 
    is_animated = False
    max_frames = 1
    base_duration = 100
    found_gif_duration = False

    resampling_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS

    for info in image_paths_info:
        try:
            img_path = info['path']
            orig_w, orig_h = info['orig_w'], info['orig_h']
            target_h = max_original_height if resize_to_max_height else orig_h
            target_w = orig_w

            if resize_to_max_height and orig_h != target_h and orig_h > 0:
                aspect_ratio = orig_w / orig_h

                target_w = ceil(target_h * aspect_ratio)
            elif orig_h == 0: 
                target_w = 0
                target_h = 0
                print(f"  - Warning: Image {os.path.basename(img_path)} has zero height. Setting dimensions to 0x0.")

            if final_stitch_height == 0:
                final_stitch_height = target_h

            elif not resize_to_max_height and target_h > final_stitch_height:
                final_stitch_height = target_h


            with Image.open(img_path) as img:
                img.load()

                img_is_animated = getattr(img, 'is_animated', False)
                img_n_frames = getattr(img, 'n_frames', 1)

                processed_data = {
                    'path': img_path,
                    'orig_w': orig_w,
                    'orig_h': orig_h,
                    'target_w': target_w,
                    'target_h': target_h,
                    'is_animated': img_is_animated,
                    'n_frames': img_n_frames,
                    'source_theme': info['source_theme']
                }

                images_data.append(processed_data)
                total_stitched_width += target_w

                if img_is_animated:
                    is_animated = True
                    max_frames = max(max_frames, img_n_frames)
                    if not found_gif_duration:
                        try:
                            img_duration = img.info.get('duration', base_duration)
                            base_duration = img_duration if img_duration > 0 else 100
                            found_gif_duration = True
                        except Exception: 
                            pass

                print(f"  - Digit '{info['digit']}': Processed {os.path.basename(img_path)}. "
                    f"Target size for stitch: {target_w}x{target_h} "
                    f"(Animated: {img_is_animated}, Frames: {img_n_frames})")

        except Exception as e:
            print(f"  - Error processing image {info['path']}, check missing or corrupted: {e}")
            continue 

    if not images_data:
        print("\nError: No images could be processed in Pass 2.")
        return None

    if not resize_to_max_height:
        actual_max_h = 0
        for data in images_data:
            actual_max_h = max(actual_max_h, data['target_h'])
        final_stitch_height = actual_max_h
        print(f"Recalculated max height needed for canvas (no resize): {final_stitch_height}")

    final_canvas_width = total_stitched_width
    final_canvas_height = final_stitch_height

    scaled_output_width = ceil(final_canvas_width * scale_factor)
    scaled_output_height = ceil(final_canvas_height * scale_factor)

    if scaled_output_width <= 0 or scaled_output_height <= 0:
        print(f"Error: Invalid output dimensions after scaling ({scaled_output_width}x{scaled_output_height}). Check scale factor.")
        return None

    print(f"\nStitched canvas base size (before final scaling): {final_canvas_width}x{final_canvas_height}")
    if scale_factor != 1.0:
        print(f"Final output size (after scaling): {scaled_output_width}x{scaled_output_height}")
    print(f"Output type: {'ANIMATED GIF' if is_animated else 'STATIC PNG'}")
    if is_animated:
        print(f"Animation frames: {max_frames}, Frame duration: {base_duration}ms (approx)")


    # --- Create Combined Image(s) ---
    output_path = None
    try:
        if is_animated:
            # --- Animated GIF Output ---
            stitched_frames_unscaled = []
            for frame_index in range(max_frames):
                frame_canvas = Image.new('RGBA', (final_canvas_width, final_canvas_height), (0, 0, 0, 0))
                current_x = 0
                for data in images_data:
                    with Image.open(data['path']) as img_frame_orig:
                        img_frame_orig.load()
                        if data['is_animated']:
                            try:
                                seek_frame = frame_index % data['n_frames']
                                img_frame_orig.seek(seek_frame)
                                img_frame_orig.load() 
                            except EOFError: 
                                img_frame_orig.seek(0)
                                img_frame_orig.load()
                            except Exception as e:
                                print(f"Warning: Error seeking frame {frame_index} for {data['path']}: {e}. Using frame 0.")
                                img_frame_orig.seek(0)
                                img_frame_orig.load()

                        img_frame_rgba = img_frame_orig.convert('RGBA')
                        resized_frame = img_frame_rgba.resize((data['target_w'], data['target_h']), resample=resampling_filter)

                        paste_y = 0
                        if not resize_to_max_height and data['target_h'] < final_canvas_height:
                            pass 

                        frame_canvas.paste(resized_frame, (current_x, paste_y), resized_frame) 
                        current_x += data['target_w'] 

                stitched_frames_unscaled.append(frame_canvas)

            output_frames_scaled = []
            if scale_factor != 1.0:
                print(f"Applying final scale ({scale_factor}) to {len(stitched_frames_unscaled)} frames...")
                for frame in stitched_frames_unscaled:
                    scaled_frame = frame.resize((scaled_output_width, scaled_output_height), resample=resampling_filter)
                    output_frames_scaled.append(scaled_frame)
            else:
                output_frames_scaled = stitched_frames_unscaled 

            output_path = f"{output_filename_base}.gif"
            output_frames_scaled[0].save(
                output_path, save_all=True, append_images=output_frames_scaled[1:],
                duration=base_duration, loop=0, transparency=0, disposal=2
            )
            print(f"\nAnimated GIF saved: {output_path}")

        else:
            final_image_unscaled = Image.new('RGBA', (final_canvas_width, final_canvas_height), (0, 0, 0, 0))
            current_x = 0
            for data in images_data:
                with Image.open(data['path']) as img_orig:
                    img_rgba = img_orig.convert('RGBA')
                    resized_img = img_rgba.resize((data['target_w'], data['target_h']), resample=resampling_filter)

                    paste_y = 0

                    final_image_unscaled.paste(resized_img, (current_x, paste_y), resized_img)
                    current_x += data['target_w']

            if scale_factor != 1.0:
                print(f"Applying final scale ({scale_factor})...")
                final_image_scaled = final_image_unscaled.resize((scaled_output_width, scaled_output_height), resample=resampling_filter)
            else:
                final_image_scaled = final_image_unscaled 

            if output_dir == "":
                output_path = f"./{output_filename_base}.png"
            else:
                if(not os.path.exists(f"./{output_dir}")):
                    os.makedirs(f"./{output_dir}")
                    
                output_path = f"./{output_dir}/{output_filename_base}.png"
            final_image_scaled.save(output_path)
            print(f"\nStatic PNG image saved: {output_path}")

    except Exception as e:
        print(f"\nError during final image creation or saving: {e}")
        if output_path and os.path.exists(output_path):
            try: 
                os.remove(output_path)
            except OSError: 
                pass
        return None

    return output_path


# --- Main Execution Block (for running the script directly) ---
if __name__ == "__main__":
    while True:
        available_themes = list_themes(THEME_BASE_DIR)

        if not available_themes:
            print(f"Error: No theme subfolders found in '{THEME_BASE_DIR}'.")

        # --- Get User Input ---
        number_str = input("Enter the number string (e.g., 1234): ")

        if(len(number_str) > 0):
            if not number_str.isdigit():
                print("Error: Invalid number string.")
                new_string = ""

                for x in number_str:
                    if(x.isdigit()):
                        new_string += new_string
                
                valid = True
        else:
            print("Choosing 1234.")

        # --- Choose Mode ---
        print("\nAvailable modes:")
        print(f"  0: Random Digits (Pick each digit randomly from any theme)")
        for i, theme_name in enumerate(available_themes):
            print(f"  {i + 1}: Use Theme '{theme_name}'")
        print(f"  {len(available_themes) + 1}: Random Theme (Pick one theme randomly)")
        print(f"  {len(available_themes) + 2}: All Themes (Go over all themes)")

        chosen_mode_str = None
        chosen_theme_name_for_mode = None
        output_suffix = "unknown"

        valid = False
        while not valid:
            try:
                choice = int(input(f"Choose a mode (0-{len(available_themes) + 2}): "))
                if choice == 0:
                    chosen_mode_str = 'random_digits'
                    output_suffix = "randomdigits"
                    valid = True
                elif 1 <= choice <= len(available_themes):
                    chosen_mode_str = 'theme'
                    chosen_theme_name_for_mode = available_themes[choice - 1]
                    output_suffix = chosen_theme_name_for_mode
                    valid = True
                elif choice == len(available_themes) + 1:
                    chosen_mode_str = 'random_theme'
                    output_suffix = "randomtheme"
                    valid = True
                elif choice == len(available_themes) + 2:
                    chosen_mode_str = 'all_themes'
                    output_suffix = "all_themes"
                    valid = True
                else: 
                    print(f"\n\nInvalid choice! Please use a number from 0-44. You chose {choice}\n\n")
            except ValueError: 
                print("Invalid input, try again.")
        print(f"Selected mode: {chosen_mode_str}" + (f" ({chosen_theme_name_for_mode})" if chosen_theme_name_for_mode else ""))


        # --- Choose Resize Behavior ---
        resize_behavior = True
        valid = False
        while not valid:
            resize_q = input("Resize all digits to match max height before stitching? (yes/no/blank) [yes]: ").lower().strip()
            if resize_q in ('yes', 'y', '', "blank"): # Default to yes
                resize_behavior = True
                valid = True
            elif resize_q in ('no', 'n'):
                resize_behavior = False
                valid = True
            else:
                print("Please answer 'yes' or 'no' or leave empty.")
        print(f"Resize digits: {resize_behavior}")


        scale_val = 1.0
        valid = False
        while not valid:
            try:
                scale_input = input(f"Enter final scale factor (e.g., 1.0 for original stitch size, or leave blank) [{scale_val}]: ").strip()
                if not scale_input:
                    valid = True
                scale_val = float(scale_input)
                if scale_val > 0:
                    valid = True
                else:
                    print("Scale factor must be positive.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        print(f"Final scale factor: {scale_val}")


        # --- Suggest Output Filename & Call Function ---

        if(chosen_mode_str == "all_themes"):
            for i in range(len(available_themes)):
                chosen_theme_name_for_mode = available_themes[i - 1]

                output_base = f"combined_{number_str}_{chosen_theme_name_for_mode}"
                output_base += "_resized" if resize_behavior else ""

                created_file = create_stitched_image(
                    number_string=number_str,
                    output_filename_base=output_base,
                    scale_factor=scale_val,
                    mode="theme",
                    theme_name=chosen_theme_name_for_mode,
                    base_theme_dir=THEME_BASE_DIR,
                    resize_to_max_height=resize_behavior
                )
        else:
            output_base = f"combined_{number_str}_{output_suffix}"
            output_base += "_resized" if resize_behavior else ""
            created_file = create_stitched_image(
                number_string=number_str,
                output_filename_base=output_base,
                scale_factor=scale_val,
                mode=chosen_mode_str,
                theme_name=chosen_theme_name_for_mode,
                base_theme_dir=THEME_BASE_DIR,
                resize_to_max_height=resize_behavior
            )

        if created_file:
            print(f"\nProcess complete. Output file: {created_file}")
        else:
            print("\nImage creation failed.")
