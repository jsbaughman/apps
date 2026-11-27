#!/usr/bin/env python3
"""gen_hexa.py - writes apps/cluster_themes/hud/layouts/hexa.json

The Hexa theme (Nov 27 2026), after a concept the driver brought: a wide glass rev arc of 23 blocks over a floor of lit
hex tiles, a black well under it for the gear and the speed, four glass gauges either side. Two effect layers do the
drawing (shaders.js): "hfloor" the floor, the well and the eight panels with their bars (static but for the bars and
the warning frames), "hdash" the rev arc alone (the blocks, the scale, the needle, the peak, the shift light), so
neither shader comes near the size that reset the cluster (Vetro 0.27.0). All words and numbers are text layers in
Saira Italic (tools/bake_fonts.py hx_*).

    python3 tools/gen_hexa.py .
"""
import json
import math
import sys

W, H = 1920, 660
CX, CY, R, TH = 960, 843, 708, 72          # the rev arc: one wide circle's slice, its outer radius and band width
T0, T1, KEND = 144.6, 35.4, 8.75           # its 0 end and its 8750 end (deg, counter-clockwise from 3 o'clock): level ends
FAST = 45

# the gauge panels' outlines (screen px), measured off the concept: the left stack wraps round the arc's 0 end, the right
# one hugs the arc 40 px off it; the box at the top right shows the drive mode
LEFT = {
    'boost':   [(150, 292), (446, 292), (381, 376), (90, 376), (90, 350)],
    'coolant': [(94, 385), (366, 385), (372, 393), (356, 470), (86, 470), (86, 393)],
    'oil':     [(88, 479), (348, 479), (376, 560), (96, 560)],
    'intake':  [(104, 569), (384, 569), (402, 654), (124, 654)],
}


def arc_x(y, gap):
    """The arc's outer edge on the right at height y, gap px out."""
    return CX + math.sqrt(R * R - (CY - y) ** 2) + gap


RIGHT = {
    'mode':   [(round(arc_x(292, 40)), 292), (1772, 292), (1830, 350), (1830, 362), (round(arc_x(362, 40)), 362)],
    'power':  [(round(arc_x(379, 40)) + 8, 371), (1826, 371), (1834, 379), (1834, 448), (round(arc_x(448, 40)), 448),
               (round(arc_x(400, 40)), 400)],
    'torque': [(1582, 457), (1832, 457), (1826, 534), (1558, 534)],
    'fuel':   [(1566, 543), (1818, 543), (1796, 654), (1530, 654), (1556, 553)],
}
# the warnings (temperatures in C, fuel 0..1): the frame amber, then red
WARN = {
    'coolant': {'signal': 'coolant', 'amber': 113, 'red': 120},
    'oil': {'signal': 'oil', 'amber': 135, 'red': 145},
    'intake': {'signal': 'intake', 'amber': 55, 'red': 65},
    'fuel': {'signal': 'fuel', 'amber': 0.12, 'red': 0.06, 'low': True},
}


def build(fonts):
    cell = lambda f: fonts[f]['cellHeight']
    widgets = []

    def text(id_, x, ymid, w, t, font, color='fg', align='left', **kw):
        """A text box w wide whose cell is centred on ymid; x is its left (align left), right (right) or middle."""
        x0 = x if align == 'left' else x - w if align == 'right' else x - w / 2.0
        d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(round(x0)), 'y': int(round(ymid - cell(font) / 2.0)), 'w': int(w),
             'h': cell(font), 'text': t, 'font': font, 'color': color, 'align': align}
        d.update({k: v for k, v in kw.items() if v is not None})
        widgets.append(d)

    # --- the backdrop and the rev arc
    order = ['boost', 'coolant', 'oil', 'intake', 'mode', 'power', 'torque', 'fuel']
    panels = [[list(v) for v in (LEFT.get(k) or RIGHT.get(k))] for k in order]
    widgets.append({'id': 'floor', 'type': 'hfloor', 'class': 'content', 'z': 0, 'x': 0, 'y': 0, 'w': W, 'h': H, 'conn': 0,
                    'panels': panels, 'warn': [WARN.get(k) for k in order],
                    'barAt': [[1745, 428, 15], [1745, 514, 15], [1682, 592, 94, 13]],
                    'arc': [CX, CY, R - TH, 515],
                    # the Waze map in the well ("Show Waze map inside the theme"): its window round the arc's inside
                    'hole': [330, 125, 1260, 410], 'holeWhen': 'mapUp', 'holeInset': 0, 'holeAim': [0.5, 0.46]})   # Waze draws its arrow well below its map's centre: this puts it just under the gear
    AX0, AY0 = 240, 95
    widgets.append({'id': 'arc', 'type': 'hdash', 'class': 'content', 'z': 1, 'x': AX0, 'y': AY0, 'w': 1440, 'h': 440, 'conn': 0,
                    'arc': [CX, CY, R, TH], 'ang': [T0, T1, KEND, KEND]})

    # --- the numbers along the arc (7 and 8 red), the gear, the speed, its unit, RPM x 1000
    nr = R - TH - 52
    for k in range(9):
        a = math.radians(T0 - (T0 - T1) * k / float(KEND))
        x, y = CX + nr * math.cos(a), CY - nr * math.sin(a)
        text('n%d' % k, x, y, 64, str(k), 'hx_num', 'hot' if k >= 7 else 'fg', 'center', rate=60000)
    text('gear', 966, 361, 240, '{{gearnum}}', 'hx_gear', 'hot', 'center', rate=FAST, own=True)
    text('prog', 1060, 318, 40, '{{progAM}}', 'hx_unit', 'hot', 'left')   # A / M, small at the gear's top right
    text('speed', 964, 523, 280, '{{speed}}', 'hx_speed', 'fg', 'center', rate=FAST, own=True, spacing=-8)
    text('speed_u', 960, 587, 120, '{{u:speed}}', 'hx_unit', 'fg', 'center')
    text('rpm_u', 668, 516, 200, 'RPM x 1000', 'hx_rpm', 'dim', 'center', rate=60000)

    # --- the left gauges: icon, label, value (right-aligned: its unit right after it)
    rows = [  # key, icon, label, value, unit, icon x, label x / y, value right x / y, unit x, cyan unit
        ('boost', 'turbo', 'BOOST', '{{boost}}', '{{u:boostLc}}', 168, 214, 316, 300, 350, 320, True),
        ('coolant', 'coolant', 'COOLANT', '{{coolant}}', '{{u:temp}}', 136, 184, 408, 254, 444, 262, False),
        ('oil', 'oilcan', 'OIL', '{{oil}}', '{{u:temp}}', 142, 190, 501, 262, 535, 270, False),
        ('intake', 'intake', 'INTAKE', '{{intake}}', '{{u:temp}}', 160, 210, 592, 268, 626, 276, False),
    ]
    for key, ic, label, val, unit, ix, lx, ly, vx, vy, ux, cyan in rows:
        s = 46
        widgets.append({'id': key + '_i', 'type': 'icon', 'icon': ic, 'z': 5, 'x': ix - s // 2, 'y': int((ly + vy) / 2 + 2 - s / 2),
                        'w': s, 'h': s, 'color': 'cool'})
        text(key + '_l', lx, ly, 160, label, 'hx_lab', 'fg', 'left', rate=60000)
        text(key + '_v', vx, vy, 110, val, 'hx_val', 'fg', 'right', rate=FAST if key == 'boost' else None, spacing=-3)
        if cyan:
            text(key + '_u', ux, vy + 2, 60, unit, 'hx_uc', 'cool', 'left')
        else:
            text(key + '_u', ux, vy + 4, 40, unit, 'hx_u', 'dim', 'left')

    # the HV battery above boost (setting "vetroHv"): its panel a picture (car_top.js paintHexaPanel), not in the backdrop
    # shader (0.28.4 / 0.28.5 put it there and the cluster reset); its right edge on boost's line; its icon, label, charge
    HVP = [(242, 207), (512, 207), (453, 283), (161, 283), (161, 262)]
    widgets.append({'id': 'hv_p', 'type': 'icon', 'icon': 'hexaPanel', 'z': 4, 'x': 141, 'y': 190, 'w': 392, 'h': 116,
                    'pts': [list(p) for p in HVP], 'toggle': 'vetroHv', 'conn': 2})
    widgets.append({'id': 'hv_i', 'type': 'icon', 'icon': 'battery', 'z': 5, 'x': 236, 'y': 225, 'w': 44, 'h': 44,
                    'color': 'cool', 'toggle': 'vetroHv', 'conn': 2})
    text('hv_l', 304, 231, 170, 'HV BATTERY', 'hx_lab', 'fg', 'left', rate=60000, toggle='vetroHv', conn=2)
    text('hv_v', 381, 262, 90, '{{hvSoc}}', 'hx_val', 'fg', 'right', spacing=-3, toggle='vetroHv', conn=2)
    text('hv_u', 387, 266, 30, '%', 'hx_u', 'dim', 'left', rate=60000, toggle='vetroHv', conn=2)

    # --- the right: the drive mode in the box, power and torque (their tick bars in the backdrop), fuel
    text('mode', 1645, 327, 320, '{{mode}}', 'hx_mode', 'fg', 'center')
    for key, label, val, unit, lx, ly, vy in (('power', 'POWER', '{{power}}', '{{u:powerLc}}', 1622, 391, 426),
                                             ('torque', 'TORQUE', '{{torque}}', '{{u:torque}}', 1604, 477, 512)):
        text(key + '_l', lx, ly, 160, label, 'hx_lab', 'fg', 'left', rate=60000)
        text(key + '_v', lx + 62, vy, 110, val, 'hx_val', 'fg', 'right', spacing=-3)
        text(key + '_u', lx + 70, vy + 4, 70, unit, 'hx_u', 'dim', 'left')
    text('fuel_l', 1590, 565, 120, 'FUEL', 'hx_lab', 'fg', 'left', rate=60000)
    text('fuel_v', 1636, 598, 80, '{{fuelPct}}', 'hx_val', 'fg', 'right', spacing=-3)
    text('fuel_u', 1642, 602, 30, '%', 'hx_u', 'dim', 'left', rate=60000)
    widgets.append({'id': 'fuel_i', 'type': 'icon', 'icon': 'fuel', 'z': 5, 'x': 1580, 'y': 619, 'w': 28, 'h': 28, 'color': 'fg'})
    text('range_v', 1690, 632, 90, '{{range}}', 'hx_val', 'fg', 'right', spacing=-3)
    text('range_u', 1698, 636, 40, '{{u:distLc}}', 'hx_u', 'dim', 'left')

    # --- the strip: covered, nothing in it; BMW's gear letter left clear
    widgets += [
        {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60,
         'color': 'bg', 'stripRow': 'l'},
        {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60,
         'color': 'bg', 'stripRow': 'r'},
    ]
    # connections (8 layers each): the backdrop, the arc, the middle on 0; the right on 1, the left on 2
    for w in widgets:
        if w['id'] in ('floor', 'arc') or w['id'].startswith('strip') or 'conn' in w:
            continue
        if w['x'] >= 1380:
            w['conn'] = 1
        elif w['x'] + w['w'] <= 480:
            w['conn'] = 2
    # slow texts checked less often
    for w in widgets:
        if w['type'] == 'text' and 'rate' not in w and not w.get('own'):
            toks = [t.split('}}')[0] for t in w['text'].split('{{')[1:]]
            if any(t in ('oil', 'intake', 'hvSoc', 'coolant', 'mode', 'power', 'torque', 'fuelPct', 'range') for t in toks):
                continue
            w['rate'] = 2000 if all(t.startswith('u:') for t in toks) else 1000
    return {
        'schemaVersion': 2,
        'name': 'Hexa',
        'theme': 'hexa',
        'mapLive': True,
        '_about': 'A glass rev arc over a floor of lit hex tiles, generated by tools/gen_hexa.py (edit that and regenerate): '
                  'the hfloor layer draws the floor, the black well and the eight gauge panels (their bars, their warning '
                  'frames), the hdash layer the rev arc (23 blocks lit to the revs, the needle, the peak, the shift light); '
                  'every word and number is text in Saira Italic. Nothing in the strip.',
        'widgets': widgets,
    }


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    fdir = root + '/apps/cluster_themes/hud/fonts/'
    fonts = {}
    for f in ('hx_num', 'hx_gear', 'hx_speed', 'hx_unit', 'hx_rpm', 'hx_mode', 'hx_lab', 'hx_val', 'hx_u', 'hx_uc'):
        j = json.load(open(fdir + f + '.json'))
        fonts[f] = {'cellHeight': j['cellHeight'], 'baseline': j['baseline']}
    path = root + '/apps/cluster_themes/hud/layouts/hexa.json'
    with open(path, 'w') as f:
        json.dump(build(fonts), f, indent=2)
    print('wrote ' + path)
