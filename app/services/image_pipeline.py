"""
Generates platform-correct image variants from one source image.

Instagram: 1080x1080 (1:1)
X:         1600x900  (16:9)

Strategy: center-crop to the target aspect ratio first (this is the
"safe zone" guarantee -- the center of the source image is always kept),
then resize to the exact target dimensions.
"""
import os
from PIL import Image

PLATFORM_SPECS = {
    "instagram": {"width": 1080, "height": 1080},
    "x": {"width": 1600, "height": 900},
}


def _center_crop_to_ratio(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    target_ratio = target_w / target_h
    src_w, src_h = img.size
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Source is wider than target -> crop left/right, keep full height (center is safe)
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        box = (left, 0, left + new_w, src_h)
    else:
        # Source is taller than target -> crop top/bottom, keep full width
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        box = (0, top, src_w, top + new_h)

    return img.crop(box)


def generate_variant(source_path: str, platform: str, output_dir: str) -> str:
    if platform not in PLATFORM_SPECS:
        raise ValueError(f"Unknown platform '{platform}'. Supported: {list(PLATFORM_SPECS)}")

    spec = PLATFORM_SPECS[platform]
    os.makedirs(output_dir, exist_ok=True)

    with Image.open(source_path) as img:
        img = img.convert("RGB")
        cropped = _center_crop_to_ratio(img, spec["width"], spec["height"])
        resized = cropped.resize((spec["width"], spec["height"]), Image.LANCZOS)

        base_name = os.path.splitext(os.path.basename(source_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_{platform}.jpg")
        resized.save(output_path, "JPEG", quality=90)

    return output_path


def generate_all_variants(source_path: str, output_dir: str) -> dict:
    return {
        platform: generate_variant(source_path, platform, output_dir)
        for platform in PLATFORM_SPECS
    }