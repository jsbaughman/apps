"""gen_aero.py - writes apps/cluster_themes/hud/layouts/aero.json

Aero: a British hypercar style cluster on the 1920x720 panel (Nov 24 2026, after photos of a McLaren's dash), drawn by one
adash effect layer (shaders.js) on deep navy:
- a full-width rev rail across the top (a parabola as wide as the screen, fading at both sides): a silver top line over a
  four-band track, a white line up to a flat blade needle with an orange glow under it, outlined tabs at each thousand,
  0..8 in Oxanium under them (grey, the band the revs are in white, the red zone red), a red zone from 7000 rpm;
- in the middle the gear big in orange (Saira), the programme letter beside it, the speed under it;
- on the left two small straight rails picked like Apex's left gauges (leftTop / leftBottom), their values over them;
- on the right the car from above (car_top.js) with the tyres round it (blue, red when low), pressures and temperatures,
  the drive mode, a slim curved fuel column with the % in italics and the pump icon;
- curved frame lines round both side panels; outside temperature and the clock in the strip.

    python3 tools/gen_aero.py .
"""
import json
import math
import sys

W, H = 1920, 660
RAIL = [75, 960, 5302, 42]           # top-line y at the middle, middle x, curve radius, track depth
SCALE = [200, 1720, 8]               # x at 0 rpm, x at 8000, thousands
ZONES = [6500, 7000]
BARS = [[130, 380, 430, 22], [130, 540, 430, 22]]
CAR = [1570, 440, 56, 64]
FUEL = [1858, 596, 372]
MAP = [640, 215, 640, 445]           # the map window x, y, w, h (between the panels, under the rail)
FAST = 45
LEFT = [
    ('boost', 'Boost', '{{boost}}', '{{u:boostLc}}', {'signal': 'boost', 'min': 0, 'max': 2.758, 'red': 0.75}, 'uPress',
     ('0', '10', '20', '30', '40'), ('0', '0.7', '1.4', '2.1', '2.8')),
    ('oil', 'Oil Temp', '{{oil}}', '{{u:temp}}', {'signal': 'oil', 'min': 50, 'max': 150, 'red': 0.8}, 'uTemp',
     ('122', '167', '212', '257', '302'), ('50', '75', '100', '125', '150')),
    ('intake', 'Intake Temp', '{{intake}}', '{{u:temp}}', {'signal': 'intake', 'min': 0, 'max': 100, 'red': 0.6}, 'uTemp',
     ('32', '77', '122', '167', '212'), ('0', '25', '50', '75', '100')),
    ('oilP', 'Oil Pressure', '{{oilP}}', '{{u:boostLc}}', {'signal': 'oilP', 'min': 0, 'max': 5.516, 'red': 1}, 'uPress',
     ('0', '20', '40', '60', '80'), ('0', '1.4', '2.8', '4.1', '5.5')),
    ('coolant', 'Water Temp', '{{coolant}}', '{{u:temp}}', {'signal': 'coolant', 'min': 50, 'max': 130, 'red': 0.81}, 'uTemp',
     ('122', '158', '194', '230', '266'), ('50', '70', '90', '110', '130')),
]
PICKS = {k: {c[0]: c[4] for c in LEFT} for k in ('left0', 'left1')}


def text(id_, x, y, w, h, t, font, color='fg', align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(round(x)), 'y': int(round(y)), 'w': int(w), 'h': int(h),
         'text': t, 'font': font, 'color': color, 'align': align}
    d.update({k: v for k, v in kw.items() if v is not None})
    return d


def centred(id_, cx, cy, w, cells, t, font, color='fg', align='center', **kw):
    return text(id_, cx - w / 2.0, cy - cells[font] / 2.0, w, cells[font], t, font, color, align, **kw)


def rail_y(x):
    dx = x - RAIL[1]
    return RAIL[0] + dx * dx / (2.0 * RAIL[2])


def frame(o, k, e, tl=34.0):
    """a frame line from the outer end o to the corner k and on to e, the corner rounded (tangent length tl)"""
    def unit(a, b):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    u0 = unit(k, o); u1 = unit(k, e)
    B = (k[0] + u0[0] * tl, k[1] + u0[1] * tl); D = (k[0] + u1[0] * tl, k[1] + u1[1] * tl)
    bis = unit((0, 0), (u0[0] + u1[0], u0[1] + u1[1]))
    half = math.acos(max(-1, min(1, u0[0] * u1[0] + u0[1] * u1[1]))) / 2
    r = tl * math.tan(half)
    dc = tl / math.cos(half)
    C = (k[0] + bis[0] * dc, k[1] + bis[1] * dc)
    return [o[0], o[1], B[0], B[1], round(C[0], 2), round(C[1], 2), round(r, 2), D[0], D[1], e[0], e[1]]


def build(cells):
    T = RAIL[3]
    frames = [frame((90, 262), (560, 262), (610, 292)), frame((90, 640), (560, 640), (610, 610)),
              frame((1830, 262), (1360, 262), (1310, 292)), frame((1830, 640), (1360, 640), (1310, 610))]
    widgets = [{'id': 'dash', 'type': 'adash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
                # the Waze map (Map tab): a window in the middle between the panels, hosted there (hud.js _mapHost)
                'hole': [MAP[0], MAP[1], MAP[2], MAP[3]], 'holeWhen': 'mapUp', 'holeInset': 0, 'holeFeather': 40,
                'rail': RAIL, 'scale': SCALE, 'zones': ZONES, 'bars': BARS, 'frames': frames, 'car': CAR, 'fuel': FUEL,
                'arcs': [{'pick': 'left0', 'signal': 'boost', 'min': 0, 'max': 2.758, 'red': 0.75},
                         {'pick': 'left1', 'signal': 'oil', 'min': 50, 'max': 150, 'red': 0.8}]}]
    # --- the scale's numbers, each centred under its tab (a dark copy under it for the shadow) ----------------------
    span = SCALE[1] - SCALE[0]
    for k in range(SCALE[2] + 1):
        x = SCALE[0] + span * k / SCALE[2]
        dk = x - RAIL[1]; sl = dk / RAIL[2]; cs = 1 / math.sqrt(1 + sl * sl)
        n = (-sl * cs, cs)
        cx, cy = x + n[0] * (T + 12), rail_y(x) + n[1] * (T + 12) + 35
        red = k * 1000 >= ZONES[1]
        band = [k * 1000, 99999] if red else [k * 1000, (k + 1) * 1000]
        widgets += [
            centred('rn%d_s' % k, cx + 4, cy + 5, 90, cells, str(k), 'ae_num', 'shade', z=4),
            centred('rn%d' % k, cx, cy, 90, cells, str(k), 'ae_num', 'numRed' if red else 'num', litBand=band,
                    litColor='hot' if red else 'fg', rate=100),
        ]
    x8 = SCALE[1]
    widgets += [
        centred('rpm_l', x8 + 58, rail_y(x8) + 40, 80, cells, 'RPM', 'ae_tiny', 'fg'),
        centred('rpm_x', x8 + 58, rail_y(x8) + 58, 80, cells, 'x1000', 'ae_tiny', 'dim'),
    ]
    # --- the middle: the gear, the programme letter, the speed ------------------------------------------------------
    widgets += [
        centred('gear', 960, 380, 300, cells, '{{gearnum}}', 'ae_gear', 'accent', rate=FAST, own=True, toggle='!mapUp'),
        text('prog', 1040, 452 - cells['ae_prog'] / 2.0, 60, cells['ae_prog'], '{{progLetter}}', 'ae_prog', 'accent', 'left', rate=FAST, toggle='!mapUp'),
        centred('speed', 960, 565, 260, cells, '{{speed}}', 'ae_speed', 'fg', rate=FAST, own=True, toggle='!mapUp'),
        centred('speed_u', 960, 628, 140, cells, '{{u:speed}}', 'ae_lab', 'fg', toggle='!mapUp'),
        # with the map in the middle: the gear bottom left, the speed bottom right, over the window's faded foot
        centred('gear_m', 720, 590, 160, cells, '{{gearnum}}', 'ae_gear_m', 'accent', rate=FAST, own=True, toggle='mapUp'),
        text('prog_m', 768, 620 - cells['ae_prog_m'] / 2.0, 40, cells['ae_prog_m'], '{{progLetter}}', 'ae_prog_m', 'accent', 'left', rate=FAST, toggle='mapUp'),
        text('speed_m', 1250 - 200, 580 - cells['ae_speed_m'] / 2.0, 200, cells['ae_speed_m'], '{{speed}}', 'ae_speed_m', 'fg', 'right', rate=FAST, own=True, toggle='mapUp'),
        text('speed_um', 1250 - 120, 638 - cells['ae_lab'] / 2.0, 120, cells['ae_lab'], '{{u:speed}}', 'ae_lab', 'fg', 'right', toggle='mapUp'),
    ]
    # --- the left rails: per spot and choice the label, the value and unit, five numbers per unit system -------------
    for spot, (bx, by, bw, bt) in enumerate(BARS):
        for key, label, tok, unit, _sc, sysk, us, met in LEFT:
            pick = 'left%d=%s' % (spot, key)
            widgets += [
                text('b%d%s_l' % (spot, key), bx, by - 42 - 24, 260, cells['ae_lab'], label, 'ae_lab', 'dim', 'left', toggle=pick),
                text('b%d%s_v' % (spot, key), bx + bw - 44 - 200, by - 38 - 34, 200, cells['ae_val'], tok, 'ae_val', 'fg', 'right',
                     toggle=pick, rate=FAST if key == 'boost' else None, own=True),
                text('b%d%s_u' % (spot, key), bx + bw - 38, by - 40 - 20, 60, cells['ae_unit'], unit, 'ae_unit', 'sub', 'left', toggle=pick),
            ]
            for j in range(5):
                x = bx + bw * j / 4.0
                redj = j / 4.0 >= _sc['red'] - 1e-6 and _sc['red'] < 0.999
                for units, labs in (('us', us), ('metric', met)):
                    widgets.append(centred('b%d%s_%d%s' % (spot, key, j, units[0]), x, by + bt + 24, 80, cells, labs[j], 'ae_bnum',
                                           'hot' if redj else 'num', toggle=pick + '&' + sysk + '=' + units))
    # --- the right: the car over the shader's tyres, pressures and temperatures, the drive mode -----------------------
    cx, cy = CAR[0], CAR[1]
    widgets.append({'id': 'tyre_car', 'type': 'icon', 'icon': 'carTop', 'z': 5, 'x': cx - 62, 'y': cy - 120, 'w': 124, 'h': 240})
    for pos, sx, sy in (('FL', -1, -1), ('FR', 1, -1), ('RL', -1, 1), ('RR', 1, 1)):
        x, y = cx + sx * 160, cy + sy * 64
        widgets += [
            centred('tp_' + pos, x, y - 16, 90, cells, '{{tyreP:%s}}' % pos, 'ae_tp', 'fg'),
            text('tpu_' + pos, x + 34, y - 22 - cells['ae_psi'] / 2.0, 50, cells['ae_psi'], '{{u:pressure}}', 'ae_psi', 'sub', 'left'),
            centred('tt_' + pos, x, y + 22, 90, cells, '{{tyreT:%s}}°' % pos, 'ae_tt', 'cool'),
        ]
    widgets.append(text('mode', 1400, 600 - cells['ae_mode'] / 2.0, 260, cells['ae_mode'], '{{mode}}', 'ae_mode', 'accent', 'left'))
    # --- the fuel column's % (in italics) and the pump icon ---------------------------------------------------------
    fx, fy, ft = FUEL
    tx = fx - 6
    widgets += [
        text('fuel_v', tx - 74, ft - 30 - cells['ae_pct'] / 2.0, 74, cells['ae_pct'], '{{fuelPct}}', 'ae_pct', 'fg', 'right'),
        text('fuel_u', tx + 6, ft - 26 - cells['ae_pctu'] / 2.0, 30, cells['ae_pctu'], '%', 'ae_pctu', 'fg', 'left'),
        {'id': 'fuel_i', 'type': 'icon', 'z': 5, 'x': fx - 26, 'y': fy + 14, 'w': 34, 'h': 34, 'icon': 'fuel', 'color': 'fg'},
    ]
    # --- the strip: outside temperature left, the clock right; BMW's gear letter left clear -------------------------
    widgets += [
        {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60, 'color': 'bg', 'stripRow': 'l'},
        {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60, 'color': 'bg', 'stripRow': 'r'},
        text('strip_out', 110, 672 - cells['ae_strip'] / 2.0, 120, cells['ae_strip'], '{{ambientN}}{{u:temp}}', 'ae_strip', 'fg', 'left', z=3, stripRow='l'),
        text('strip_time', 1640, 672 - cells['ae_strip'] / 2.0, 170, cells['ae_strip'], '{{time}} {{ampmLc}}', 'ae_strip', 'fg', 'right', z=3, stripRow='r'),
    ]
    for w in widgets:
        if w['type'] == 'text' and 'rate' not in w:
            toks = [t.split('}}')[0] for t in w['text'].split('{{')[1:]]
            if any(t in ('oil', 'intake', 'oilP', 'coolant', 'mode', 'boost') for t in toks):
                continue
            w['rate'] = 2000 if all(t.startswith('u:') for t in toks) else 1000
    # connections: the right panel on 1, the left rails' text on 2 (each connection has 8 layers: smaller sheets)
    for w in widgets:
        i = w['id']
        if i.startswith(('tp_', 'tpu_', 'tt_', 'tyre_car', 'mode', 'fuel_', 'speed_m', 'speed_um')):
            w['conn'] = 1
        elif i.startswith('b') and i[1:2] in ('0', '1'):
            w['conn'] = 2
    for w in widgets:
        if w.get('own') is None:
            w.pop('own', None)
    return {'schemaVersion': 2, 'name': 'Aero', 'theme': 'aero',
            '_about': 'A British hypercar style cluster, generated by tools/gen_aero.py (edit that and regenerate): one adash '
                      'layer draws the deep navy backdrop, the full-width rev rail with its needle, the left rails, the frame '
                      'lines, the tyres and the fuel column; text widgets in Oxanium and Saira.',
            'picks': PICKS, 'widgets': widgets}


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    fonts = root + '/apps/cluster_themes/hud/fonts/'
    cells = {}
    for f in ('ae_gear_m', 'ae_prog_m', 'ae_speed_m', 'ae_num', 'ae_bnum', 'ae_tiny', 'ae_gear', 'ae_prog', 'ae_speed', 'ae_lab', 'ae_unit', 'ae_psi', 'ae_val', 'ae_tp',
              'ae_tt', 'ae_mode', 'ae_pct', 'ae_pctu', 'ae_strip'):
        cells[f] = json.load(open(fonts + f + '.json'))['cellHeight']
    path = root + '/apps/cluster_themes/hud/layouts/aero.json'
    with open(path, 'w') as f:
        json.dump(build(cells), f, indent=2)
    print('wrote ' + path)
