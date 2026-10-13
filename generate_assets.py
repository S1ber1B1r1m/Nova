# generate_assets.py
# Bu betik, repo/assets klasörüne kırmızı-siyah tema görsel şablonları üretir.
# Çalıştır: python generate_assets.py

from pathlib import Path
import os
import io

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True)


def safe_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def make_red_black_bg(width, height, accent=(255, 70, 70)):
    img = Image.new("RGBA", (width, height), (15, 15, 18, 255))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(25 + ratio * 150)
        g = int(10 + ratio * 20)
        b = int(12 + ratio * 30)
        draw.line((0, y, width, y), fill=(r, g, b, 255))

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for i in range(0, 180, 10):
        alpha = 120 - i
        gdraw.rounded_rectangle((i, i, width - i, height - i), radius=60, outline=(*accent, max(20, alpha)), width=3)
    img = Image.alpha_composite(img, glow)
    return img


def add_glow_text(draw, text, xy, font, fill=(255, 255, 255), stroke_fill=(255, 60, 60), stroke_width=3):
    draw.text((xy[0] - 1, xy[1]), text, font=font, fill=stroke_fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
    draw.text(xy, text, font=font, fill=fill)


def create_welcome_template():
    width, height = 1200, 420
    img = make_red_black_bg(width, height)
    draw = ImageDraw.Draw(img)

    # Large red glow soft circle behind avatar area
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((40, 80, 320, 360), fill=(220, 20, 20, 90), outline=(255, 90, 90, 180), width=8)
    img = Image.alpha_composite(img, glow)

    # Avatar placeholder circle
    mask = Image.new("L", (220, 220), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((0, 0, 220, 220), fill=255)
    fake_avatar = Image.new("RGBA", (220, 220), (35, 35, 40, 255))
    # simple head/shoulder silhouette effect
    adraw = ImageDraw.Draw(fake_avatar)
    adraw.ellipse((60, 35, 160, 120), fill=(200, 200, 200, 200))
    adraw.rectangle((40, 120, 180, 210), fill=(90, 90, 110, 220))
    img.paste(fake_avatar, (80, 110), mask)

    # Text blocks
    brand_font = safe_font(22)
    title_font = safe_font(62, bold=True)
    sub_font = safe_font(28)
    footer_font = safe_font(18)

    add_glow_text(draw, "NOVA UNIVERSE", (330, 45), brand_font, fill=(255, 110, 110), stroke_fill=(255, 60, 60), stroke_width=2)
    add_glow_text(draw, "HOŞ GELDİN", (330, 100), title_font, fill=(255, 255, 255), stroke_fill=(255, 60, 60), stroke_width=3)
    add_glow_text(draw, "Nova Master", (330, 190), sub_font, fill=(255, 255, 255), stroke_fill=(255, 60, 60), stroke_width=2)
    add_glow_text(draw, "Seninle birlikte 23.956 kişiyiz, iyi eğlenceler!", (330, 245), sub_font, fill=(220, 220, 220), stroke_fill=(255, 60, 60), stroke_width=1)

    draw.text((1020, 20), "NV", font=safe_font(24, bold=True), fill=(255, 90, 90))
    draw.text((980, 375), "NOVA UNIVERSE • NOVA MASTER", font=footer_font, fill=(255, 255, 255))

    return img


def create_ticket_panel():
    width, height = 1200, 350
    img = make_red_black_bg(width, height)
    draw = ImageDraw.Draw(img)

    # Add large ticket frame style red border
    border = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(border)
    bdraw.rounded_rectangle((40, 40, width - 40, height - 40), radius=36, outline=(255, 70, 70, 200), width=6)
    img = Image.alpha_composite(img, border)

    # central ticket card in red-black
    ticket = Image.new("RGBA", (540, 220), (15, 15, 18, 220))
    tdraw = ImageDraw.Draw(ticket)
    tdraw.rounded_rectangle((0, 0, 540, 220), radius=26, outline=(255, 70, 70, 255), width=5)
    # background streaks
    for i in range(0, 540, 18):
        tdraw.line((i, 20, i + 50, 220), fill=(120, 15, 15, 50), width=3)
    img.paste(ticket, (330, 70), ticket)

    # Text inside ticket
    title_font = safe_font(70, bold=True)
    small_font = safe_font(22)
    sign_font = safe_font(16)
    add_glow_text(draw, "TICKET", (190, 120), title_font, fill=(255, 255, 255), stroke_fill=(255, 80, 80), stroke_width=4)
    add_glow_text(draw, "NOVA MASTER", (440, 145), small_font, fill=(255, 240, 240), stroke_fill=(255, 80, 80), stroke_width=2)
    add_glow_text(draw, "Ticket sistemine gelin", (440, 180), small_font, fill=(220, 220, 220), stroke_fill=(255, 80, 80), stroke_width=1)
    draw.text((900, 250), "NOVA UNIVERSE • NOVA MASTER", font=sign_font, fill=(255, 255, 255))
    draw.text((1040, 40), "NV", font=safe_font(26, bold=True), fill=(255, 100, 100))

    return img


def create_giveaway_template():
    width, height = 1200, 450
    img = make_red_black_bg(width, height)
    draw = ImageDraw.Draw(img)

    # glow and frame
    frame = Image.new("RGBA", (width - 120, height - 120), (25, 25, 30, 200))
    fdraw = ImageDraw.Draw(frame)
    fdraw.rounded_rectangle((0, 0, width - 120, height - 120), radius=30, outline=(255, 70, 70, 255), width=5)
    img.paste(frame, (60, 60), frame)

    # center prize box
    prize_box = Image.new("RGBA", (380, 180), (28, 20, 20, 180))
    pdraw = ImageDraw.Draw(prize_box)
    pdraw.rounded_rectangle((0, 0, 380, 180), radius=28, outline=(255, 70, 70, 255), width=4)
    img.paste(prize_box, (410, 150), prize_box)

    title_font = safe_font(70, bold=True)
    small_font = safe_font(28)
    tiny_font = safe_font(18)

    add_glow_text(draw, "ÇEKİLİŞ SONA ERDİ", (250, 60), small_font, fill=(255, 255, 255), stroke_fill=(255, 70, 70), stroke_width=2)
    add_glow_text(draw, "7G SKYLINE", (280, 120), title_font, fill=(255, 255, 255), stroke_fill=(255, 70, 70), stroke_width=4)
    draw.text((480, 290), "NOVA MASTER", font=safe_font(30, bold=True), fill=(255, 255, 255))
    draw.text((790, 395), "NOVA UNIVERSE • NOVA MASTER", font=tiny_font, fill=(255, 255, 255))
    draw.text((1100, 40), "NV", font=safe_font(24, bold=True), fill=(255, 100, 100))

    return img


def create_poll_template():
    width, height = 1200, 400
    img = make_red_black_bg(width, height)
    draw = ImageDraw.Draw(img)

    frame = Image.new("RGBA", (width - 80, height - 80), (25, 25, 25, 200))
    fdraw = ImageDraw.Draw(frame)
    fdraw.rounded_rectangle((0, 0, width - 80, height - 80), radius=28, outline=(255, 70, 70, 220), width=4)
    img.paste(frame, (40, 40), frame)

    font_title = safe_font(44, bold=True)
    font_choice = safe_font(28)
    small_font = safe_font(18)

    add_glow_text(draw, "ANKET", (80, 70), font_title, fill=(255, 255, 255), stroke_fill=(255, 70, 70), stroke_width=2)
    add_glow_text(draw, "Sunucuda hangi sistem daha iyi?", (80, 140), font_choice, fill=(255, 255, 255), stroke_fill=(255, 70, 70), stroke_width=1)

    # A/B option boxes
    a_box = Image.new("RGBA", (270, 90), (90, 20, 20, 210))
    adraw = ImageDraw.Draw(a_box)
    adraw.rounded_rectangle((0, 0, 270, 90), radius=18, outline=(255, 90, 90, 255), width=3)
    img.paste(a_box, (110, 220), a_box)
    draw.text((170, 250), "A", font=safe_font(30, bold=True), fill=(255, 255, 255))

    b_box = Image.new("RGBA", (270, 90), (18, 18, 18, 220))
    bdraw = ImageDraw.Draw(b_box)
    bdraw.rounded_rectangle((0, 0, 270, 90), radius=18, outline=(255, 90, 90, 255), width=3)
    img.paste(b_box, (520, 220), b_box)
    draw.text((580, 250), "B", font=safe_font(30, bold=True), fill=(255, 255, 255))

    draw.text((870, 330), "NOVA UNIVERSE • NOVA MASTER", font=small_font, fill=(255, 255, 255))
    draw.text((1080, 40), "NV", font=safe_font(24, bold=True), fill=(255, 100, 100))
    return img


def save_png(path: Path, image: Image.Image):
    image.save(path)


if __name__ == "__main__":
    save_png(ASSETS_DIR / "welcome_template.png", create_welcome_template())
    save_png(ASSETS_DIR / "ticket_panel.png", create_ticket_panel())
    save_png(ASSETS_DIR / "giveaway_template.png", create_giveaway_template())
    save_png(ASSETS_DIR / "poll_template.png", create_poll_template())
    print("Şablon görseller oluşturuldu:")
    for name in ["welcome_template.png", "ticket_panel.png", "giveaway_template.png", "poll_template.png"]:
        print(f" - {ASSETS_DIR / name}")
