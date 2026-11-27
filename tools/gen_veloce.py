"""gen_veloce.py - writes apps/cluster_themes/hud/layouts/veloce.json

Veloce: an Italian supercar style cluster on the 1920x720 panel, drawn by one ldash effect layer (shaders.js):
- a hex-cell backdrop;
- a wide elliptical rev arc of bevelled blocks across the top, 0..8, lit silver up to the revs and red from the redline,
  its numbers inside it;
- the gear big and hollow in red in the middle over a grey band, the drive mode beside it, the rpm in digits in the band;
- the speed in a bold italic at the bottom right inside the arc;
- small horizontal scales with red needles at the sides: oil temperature and boost left, fuel and coolant right;
- the theme's own clock, range and outside temperature in the strip, BMW's gear letter left uncovered.

    python3 tools/gen_veloce.py .
"""
import json
import math
import sys

W, H = 1920, 660
ARC = [960, 732, 621, 587]                 # centre x, y, horizontal and vertical radius (outer edge); a near-circle whose
                                           # centre sits below its ends, so the ends lean outward as they come down
START, SWEEP, BLOCKS, THOUSANDS, BAND = 195, 150, 24, 8, 0.15
RED = 7000                                 # red from (rpm)
NUMS_R = 0.78                             # the numbers' place, as a fraction of the arc's radius

# the scale numbers follow the Units setting (one condition each)
US, METRIC = 'units=us', 'units=metric'
TUS, TMET = 'uTemp=us', 'uTemp=metric'      # temperatures: the Temperature setting
PUS, PMET = 'uPress=us', 'uPress=metric'    # pressures: the Pressure setting


def text(id_, x, y, w, h, t, font, color='fg', align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(round(x)), 'y': int(round(y)), 'w': int(w), 'h': int(h),
         'text': t, 'font': font, 'color': color, 'align': align}
    d.update(kw)
    return d


def mini_block(n, mini, label, value, unit, nums, conn=None, when=None, sfx=''):
    """A side scale's texts: the label and value on one row above it, its min / middle / max numbers just above the line."""
    x, y, w = mini['x'], mini['y'], mini['w']
    # 20 % larger than the first version (vl_lab, vl_sm, 0.21.7), on the same baselines (the label row's bottom at y - 54,
    # the scale numbers' at y - 19)
    both = lambda c: (when + '&' + c) if when and c else (when or c)
    out = [text('m%d_l' % n, x, y - 54 - 33, 210, 33, label, 'vl_lab', 'fg', 'left'),
           text('m%d_v' % n, x + w - 136, y - 54 - 33, 130, 33, value, 'vl_lab', 'fg', 'right'),
           text('m%d_u' % n, x + w, y - 54 - 33, 60, 33, unit, 'vl_lab', 'dim', 'left')]
    for cond, (lo, mid, hi) in nums:
        tag = 'us' if cond in (US, TUS, PUS) else 'm'
        out += [text('m%d_lo_%s' % (n, tag), x - 36, y - 19 - 25, 72, 25, lo, 'vl_sm', 'dim', 'center', toggle=cond),
                text('m%d_mid_%s' % (n, tag), x + w / 2 - 36, y - 19 - 25, 72, 25, mid, 'vl_sm', 'dim', 'center', toggle=cond),
                text('m%d_hi_%s' % (n, tag), x + w - 36, y - 19 - 25, 72, 25, hi, 'vl_sm', 'hot', 'center', toggle=cond)]
    for t in out:
        if conn is not None:
            t['conn'] = conn
        if when:
            t['toggle'] = both(t.get('toggle'))
            t['id'] += sfx
    return out


def build():
    widgets = []
    minis = [
        # staggered along the arc, as in the reference photo: the upper scales sit further in, the lower ones further out
        {'x': 210, 'y': 330, 'w': 210, 'signal': 'oil', 'min': 50, 'max': 150, 'red': 0.8},
        {'x': 90, 'y': 490, 'w': 210, 'signal': 'boost', 'min': 0, 'max': 2.758, 'red': 0.75,
         'alt': 'intake', 'altMin': 0, 'altMax': 100, 'altRed': 0.6, 'altWhen': 'showBoost'},   # "Show boost" off: intake
        {'x': 1500, 'y': 330, 'w': 210, 'signal': 'fuel', 'min': 0, 'max': 1, 'red': 1},
        {'x': 1620, 'y': 490, 'w': 210, 'signal': 'coolant', 'min': 40, 'max': 130, 'red': 0.85},
    ]
    widgets.append({'id': 'dash', 'type': 'ldash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
                    'arc': ARC + [START, SWEEP, BLOCKS, THOUSANDS, BAND], 'red': RED,
                    'band': [560, 354, 800, 56], 'minis': minis})
    # the arc's numbers, inside the blocks
    cx, cy, rx, ry = ARC
    for k in range(THOUSANDS + 1):
        a = math.radians(START + SWEEP * k / float(THOUSANDS))
        x, y = cx + rx * NUMS_R * math.cos(a), cy + ry * NUMS_R * math.sin(a)
        widgets.append(text('rpm%d' % k, x - 40, y - 24, 80, 47, str(k), 'a_tach', 'hot' if k * 1000 >= RED else 'fg'))
    # the middle: the gear over the band, the drive mode beside it, the rpm in digits in the band
    widgets += [
        text('gear', 830, 320, 260, 163, '{{gearnum}}', 'a_gear', 'hot', dx=-7, toggle='!gearStyle=solid'),
        text('gear_s', 830, 326, 260, 151, '{{gearnum}}', 'a_gear_s', 'hot', dx=-12, toggle='gearStyle=solid'),   # the solid one (Apex's)
        text('mode', 1040, 420, 220, 24, '{{mode}}', 'v_label', 'hot', 'left'),
        text('rpm_d', 680, 359, 190, 47, '{{rpm}}', 'a_tach', 'ink', 'right', dx=-6),
        text('rpm_u', 1130, 369, 160, 30, 'RPM', 'r_label', 'ink', 'left'),
    ]
    # the speed, bottom middle under the band
    widgets += [
        text('speed', 790, 508, 240, 76, '{{speed}}', 'a_speed', 'fg', 'right', dx=-24, conn=1),
        text('speed_u', 1008, 545, 80, 37, '{{u:speedLc}}', 'a_unit', 'fg', 'left', conn=1),
    ]
    # the side scales
    widgets += mini_block(0, minis[0], 'Oil Temp', '{{oil}}', '{{u:temp}}',
                          [(TUS, ('122', '212', '302')), (TMET, ('50', '100', '150'))])
    widgets += mini_block(1, minis[1], 'Boost', '{{boost}}', '{{u:boostLc}}',
                          [(PUS, ('0', '20', '40')), (PMET, ('0', '1.4', '2.8'))], when='showBoost')
    widgets += mini_block(1, minis[1], 'Intake', '{{intake}}', '{{u:temp}}',
                          [(TUS, ('32', '122', '212')), (TMET, ('0', '50', '100'))], when='!showBoost', sfx='i')
    widgets += mini_block(2, minis[2], 'Fuel', '{{fuelPct}}', '%',
                          [(US, ('0', '50', '100')), (METRIC, ('0', '50', '100'))], conn=1)
    widgets += mini_block(3, minis[3], 'Water Temp', '{{coolant}}', '{{u:temp}}',
                          [(TUS, ('104', '185', '266')), (TMET, ('40', '85', '130'))], conn=1)
    # the bottom strip: clock, range, outside temperature; BMW's gear letter left uncovered
    widgets += [
        {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60,
         'color': 'bg', 'stripRow': 'l'},
        {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60,
         'color': 'bg', 'stripRow': 'r'},
        text('strip_time', 120, 670, 160, 42, '{{time}}', 'v_title', 'fg', 'right', z=3, stripRow='l'),
        text('strip_ampm', 284, 678, 50, 32, '{{ampmLc}}', 'm_tiny', 'fg', 'left', z=3, stripRow='l'),
        text('strip_range', 830, 670, 140, 42, '{{range}}', 'v_title', 'fg', 'right', z=3, stripRow='l'),
        text('strip_range_u', 974, 678, 50, 32, '{{u:distLc}}', 'm_tiny', 'fg', 'left', z=3, stripRow='l'),
        text('strip_out', 1640, 670, 110, 42, '{{ambientN}}', 'v_title', 'fg', 'right', z=3, stripRow='r'),
        text('strip_out_u', 1754, 678, 50, 32, '{{u:temp}}', 'm_tiny', 'fg', 'left', z=3, stripRow='r'),
    ]
    # as Apex (0.21.6): the speed, gear and boost looked at on every 50 ms tick, each on its own small image layer (a change
    # uploads only that small picture's changed rect); the slow readings once a second, fixed labels and units every 2 s;
    # the drive mode, the rpm digits and oil / coolant (they flash over their warning limit, 300 ms) at the default 200 ms
    for w in widgets:
        if w.get('id') in ('gear', 'gear_s', 'speed', 'm1_v'):
            w['rate'] = 45
            w['own'] = True
            w['conn'] = 2
        elif w['type'] == 'text' and 'rate' not in w:
            txt = w['text']
            if any(k in txt for k in ('{{oil}}', '{{coolant}}', '{{boost}}', '{{mode}}', '{{gSide}}', '{{gFwd}}', '{{rpm}}')):
                continue
            tokens = [x.split('}}')[0] for x in txt.split('{{')[1:]]
            w['rate'] = 2000 if all(tk.startswith('u:') for tk in tokens) else 1000
    return {
        'schemaVersion': 2,
        'name': 'Veloce',
        'theme': 'veloce',
        '_about': 'An Italian supercar style cluster, generated by tools/gen_veloce.py (edit that and regenerate): one ldash '
                  'layer draws the hex backdrop, the wide rev arc of bevelled blocks (0..8, silver to the revs, red from '
                  '7000 rpm), the grey middle band and the four side scales. The gear hollow in red over the band, the rpm '
                  'in digits, the speed bottom right; oil temperature and boost left, fuel and coolant right. No map window.',
        'widgets': widgets,
    }


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    path = root + '/apps/cluster_themes/hud/layouts/veloce.json'
    with open(path, 'w') as f:
        json.dump(build(), f, indent=2)
        f.write('\n')
    print('wrote', path)
