#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render review-only D2 frames. Pillow is needed only for this host demo.

No camera image, display device, GPIO, battery bus, DRM, media unmount, OS
shutdown, web service or external asset is used. The background is a synthetic
full-sensor framing target. The library rasterizer itself uses only stdlib.
"""
import argparse
from dataclasses import asdict, replace
import hashlib
import html
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gs8_camera_evf.d2_presentation import CANVAS_SIZE, present_shutdown, present_status, rasterize
from gs8_camera_evf.d2_runtime import D2Status


def scenarios():
    base = D2Status('ready', 24, 1.0, 24, 1.0, False, 3920, 76, False, None, None,
                    None, True, 'simulation_unqualified', ())
    rows = [
        ('01-ready', 'Ready after release', base),
        ('02-recording-18', '18 FPS recording', replace(base, phase='recording', selected_fps=18, active_fps=18)),
        ('03-recording-next', 'Active 24 / next 18 and 4x', replace(base, phase='recording', selected_fps=18,
                                                               selected_gain=4, active_gain=2, settings_pending=True)),
        ('04-saving', 'Saving, settings still pending', replace(base, phase='saving', selected_fps=18,
                                                             selected_gain=4, active_gain=2, settings_pending=True)),
        ('05-low-cell-warning', 'Low-cell warning during capture', replace(base, phase='recording',
                                                                       battery_millivolts=3450, battery_percent=8,
                                                                       battery_warning=True)),
        ('06-applying', 'Applying between takes', replace(base, phase='applying_settings', selected_fps=18,
                                                        selected_gain=4, settings_pending=True)),
        ('07-missing-telemetry', 'Startup with unknown telemetry', replace(base, phase='checking',
                                                                       selected_fps=None, selected_gain=None,
                                                                       active_fps=None, active_gain=None,
                                                                       battery_millivolts=None, battery_percent=None)),
        ('08-readiness-blocked', 'Media / storage readiness lost', replace(base, phase='checking', simulation_only=False,
                                                                       readiness_state='degraded',
                                                                       readiness_reasons=('media_writable_outside_limit',
                                                                                          'free_bytes_outside_limit'))),
        ('09-input-loss', 'Input lost, draining shutdown', replace(base, phase='shutting_down',
                                                                shutdown_reason='controls_unavailable',
                                                                failure='controls_unavailable: RuntimeError: disconnected')),
        ('10-battery-data-loss', 'Cached gauge values suppressed', replace(base, phase='shutting_down',
                                                                        shutdown_reason='battery_telemetry_stale_or_reordered')),
        ('11-low-cell-stop', 'Low cell requests shutdown', replace(base, phase='shutting_down',
                                                                shutdown_reason='battery_low_voltage',
                                                                battery_millivolts=3300, battery_percent=3)),
        ('12-capture-stopped', 'Capture stopped, halt unconfirmed', replace(base, phase='stopped',
                                                                        shutdown_reason='operator_shutdown')),
        ('13-fault-stopped', 'Recorder fault after drain', replace(base, phase='fault_stopped',
                                                                shutdown_reason='recorder_failed',
                                                                failure='recorder_failed: RuntimeError: commit failed ' + 'detail ' * 100)),
        ('14-shutdown-hold', 'Generic pre-rendered shutdown frame', None),
        ('15-dense-fault', 'Worst-case long-status regression', replace(base, phase='fault_stopped', selected_fps=None,
                                                                    settings_pending=True, battery_millivolts=None,
                                                                    shutdown_reason='battery_low_voltage',
                                                                    failure='controls_unavailable: ' + 'detail ' * 100,
                                                                    hardware_qualified=True, readiness_state='degraded',
                                                                    readiness_reasons=(
                                                                        'commissioning_evidence_missing_or_unverified',
                                                                        'runtime_health_invalid_or_stale',
                                                                        'soc_temperature_c_outside_limit',
                                                                        'throttled_bits_outside_limit', 'usb_resets_outside_limit',
                                                                        'media_writable_outside_limit', 'free_bytes_outside_limit',
                                                                        'unknown_' + 'X' * 1000))),
    ]
    return rows


def make_target(Image, ImageDraw, ImageFont):
    """Draw a synthetic input image at the backend's documented 728x544 size."""
    image = Image.new('RGB', (728, 544))
    draw = ImageDraw.Draw(image)
    for y in range(544):
        t = y / 543
        draw.line((0, y, 727, y), fill=(int(72 + 144 * t), int(103 + 85 * t), int(120 + 34 * t)))
    draw.polygon(((0, 370), (138, 215), (275, 347), (467, 204), (727, 349), (727, 543), (0, 543)), fill=(60, 88, 91))
    draw.polygon(((0, 433), (202, 317), (381, 443), (550, 291), (727, 455), (727, 543), (0, 543)), fill=(33, 54, 58))
    draw.polygon(((0, 505), (318, 396), (473, 448), (727, 393), (727, 543), (0, 543)), fill=(17, 29, 33))
    # Exact sensor edges and corner names let a reviewer see that none is lost.
    draw.rectangle((0, 0, 727, 543), outline=(233, 234, 214), width=2)
    font = ImageFont.load_default(size=19)
    for x, y, name in ((12, 10, 'TL'), (685, 10, 'TR'), (12, 510, 'BL'), (685, 510, 'BR')):
        draw.rectangle((x - 4, y - 2, x + 30, y + 25), fill=(13, 22, 27))
        draw.text((x, y), name, font=font, fill=(244, 238, 209))
    draw.rectangle((159, 228, 567, 286), fill=(19, 33, 37))
    draw.text((364, 239), 'SYNTHETIC FULL-SENSOR TARGET', anchor='mt', font=font, fill=(234, 240, 239))
    draw.text((364, 262), 'NO CAMERA FOOTAGE', anchor='mt', font=ImageFont.load_default(size=14), fill=(188, 203, 203))
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
    except ImportError as error:
        raise SystemExit('This optional host preview tool needs Pillow; the renderer and tests do not.') from error
    destination = args.output
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'native-frames').mkdir(exist_ok=True)
    (destination / 'rgba-overlays').mkdir(exist_ok=True)
    target = make_target(Image, ImageDraw, ImageFont)
    target.save(destination / 'synthetic-input-728x544.png')
    info = PngImagePlugin.PngInfo()
    info.add_text('Description', 'HOST-RENDERED PREVIEW. Synthetic inputs; not camera footage, hardware display validation or optical legibility evidence.')
    info.add_text('Software', 'D2 host presentation demo; Python + Pillow; no external images')
    title_font = ImageFont.load_default(size=22)
    caption_font = ImageFont.load_default(size=17)
    sheet = Image.new('RGB', (1536, 72 + 5 * 430), (23, 28, 33))
    sheet_draw = ImageDraw.Draw(sheet)
    sheet_draw.text((20, 12), 'D2 EVF / HOST-RENDERED LAYOUT STUDY', font=title_font, fill=(240, 244, 247))
    sheet_draw.text((20, 42), 'Synthetic inputs only. No hardware, optical legibility, display retention or shutdown validation.',
                    font=caption_font, fill=(193, 203, 211))
    records, cards = [], []
    generated_paths = [destination / 'synthetic-input-728x544.png', destination / 'host-preview-contact-sheet.png',
                       destination / 'index.html']
    for index, (name, caption, status) in enumerate(scenarios()):
        presentation = present_shutdown(simulation_only=True) if status is None else present_status(status)
        overlay = Image.frombytes('RGBA', CANVAS_SIZE, rasterize(presentation))
        overlay.save(destination / 'rgba-overlays' / f'{name}.png', pnginfo=info)
        frame = Image.new('RGBA', CANVAS_SIZE, (0, 0, 0, 255))
        rect = presentation.preview_rect
        if rect is not None:
            # Demonstrates the *required* future compositor placement, not the
            # existing backend (which still uses the full 1024x768 canvas).
            frame.paste(target.resize((rect.width, rect.height), Image.Resampling.NEAREST), (rect.x, rect.y))
        frame = Image.alpha_composite(frame, overlay).convert('RGB')
        frame.save(destination / 'native-frames' / f'{name}.png', pnginfo=info)
        review = Image.new('RGB', (1024, 824), (23, 28, 33))
        draw = ImageDraw.Draw(review)
        draw.text((16, 7), 'HOST-RENDERED PREVIEW / ' + caption, font=title_font, fill=(240, 244, 247))
        draw.text((16, 33), '1024 x 768 panel pixels below; synthetic target; no hardware validation',
                  font=caption_font, fill=(193, 203, 211))
        review.paste(frame, (0, 56))
        review_name = f'host-preview-{name}.png'
        review.save(destination / review_name, pnginfo=info)
        generated_paths.extend((destination / review_name, destination / 'native-frames' / f'{name}.png',
                                destination / 'rgba-overlays' / f'{name}.png'))
        col, row = index % 3, index // 3
        sheet.paste(frame.resize((512, 384), Image.Resampling.NEAREST), (col * 512, 72 + row * 430 + 38))
        sheet_draw.text((col * 512 + 10, 72 + row * 430 + 8), caption, font=caption_font, fill=(230, 235, 239))
        records.append({'id': name, 'caption': caption, 'status': asdict(status) if status is not None else None,
                        'preview_rect': asdict(rect) if rect is not None else None,
                        'text': presentation.text, 'notice_codes': presentation.notice_codes,
                        'native_frame': f'native-frames/{name}.png', 'review_image': review_name})
        cards.append(f'<figure><a href="{review_name}"><img src="{review_name}" alt="{html.escape(caption)}"></a>'
                     f'<figcaption>{html.escape(caption)} · <a href="native-frames/{name}.png">native pixels</a> · '
                     f'<a href="rgba-overlays/{name}.png">RGBA overlay</a></figcaption></figure>')
    sheet.save(destination / 'host-preview-contact-sheet.png', pnginfo=info)
    (destination / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>D2 host-rendered EVF previews</title>
<style>body{font:16px/1.5 system-ui,sans-serif;background:#171c21;color:#edf2f5;margin:28px auto;max-width:1500px;padding:0 18px}h1{font-size:25px}a{color:#c2deef}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,480px),1fr));gap:22px}figure{margin:0}img{width:100%;height:auto}figcaption{margin:6px 0 18px;color:#bccbd5}.note{max-width:1000px}</style>
<h1>D2 EVF: host-rendered layout study</h1><p class="note">Synthetic inputs and a generated full-sensor target only. These are not camera footage, hardware display validation, optical legibility measurements or proof of retained shutdown pixels. The existing Picamera preview still fills its whole canvas. A future compositor must explicitly place the complete source at (57,48), 910×680, before using these rails.</p>
<p class="note">Selected design canvas: 1024×768. All full-sensor edges remain visible. The routine view uses 78.7% of panel pixels; critical failures use an opaque status page. Open the native images at 100% to inspect pixels. Every state preserves the unqualified label.</p>
<p><a href="host-preview-contact-sheet.png">Contact sheet</a> · <a href="manifest.json">Inputs and SHA-256 manifest</a></p><div class="grid">'''
                                              + '\n'.join(cards) + '</div></html>\n', encoding='utf-8')
    files = {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(generated_paths)}
    manifest = {'schema_version': 1, 'evidence_type': 'host_rendered_preview', 'hardware_qualified': False,
                'optical_legibility_measured': False, 'display_retention_verified': False,
                'native_canvas': CANVAS_SIZE, 'rgba_format': 'straight-alpha RGBA8888, top-left, tightly packed',
                'source_target': (728, 544), 'scenarios': records, 'sha256': files}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(destination), 'scenarios': len(records), 'hashed_files': len(files),
                      'hardware_qualified': False}))


if __name__ == '__main__':
    main()
