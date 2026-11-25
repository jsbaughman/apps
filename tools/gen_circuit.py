"""gen_circuit.py - writes apps/cluster_themes/hud/layouts/circuit.json

Circuit: a German track-car style cluster on the 1920x720 panel (Nov 23 2026, after a photo of a GT3's dash), drawn by
one gdash effect layer (shaders.js) on a carbon backdrop:
- the rev counter in the middle: a bevelled metal bezel, a tick track coloured blue to warm to red, the numbers 0..8 white
  on a grooved red band, a cream needle on a silver hub; the speed big in the black face with the gear in a red box;
- a smaller dial on the left with two scales, over the top and under the bottom, each picked like Apex's left gauges
  (settings leftTop / leftBottom: boost, oil temperature, intake temperature, oil pressure; "Show boost" off puts the
  intake in boost's place), their values in the middle;
- a dial of the same size on the right: the car from above (car_top.js) with the tyres coloured by pressure, each tyre's
  pressure and temperature beside it.
Nothing in the strip (it is covered, BMW's gear letter left clear, as Apex).

    python3 tools/gen_circuit.py .
"""
import json
import math
import sys

W, H = 1920, 660
TACH = [960, 340, 308]                 # centre x, y, outer radius (to the bezel's edge)
START, SWEEP, THOUSANDS = -122, 244, 8  # 0 at -122 deg from 12 o'clock, clockwise to 8
ZONES = [6500, 7000]
SIDE_R = 266
LEFT = [338, 362, SIDE_R]
RIGHT = [1582, 362, SIDE_R]
K = TACH[2] / 322.0                    # the mockup's sizes were for a 322 px dial
KS = SIDE_R / 278.0                    # and 278 for the side ones
FAST = 45
MAP_R = 244                            # the map's square round the right dial's face (its window is the face)

# the left dial's choices: heading, value, unit, the scale (signal, min, max, red from 0..1), five labels per unit system
CHOICES = [
    ('boost', 'Boost', '{{boost}}', '{{u:boostLc}}', {'signal': 'boost', 'min': 0, 'max': 2.758, 'red': 0.75},
     ('0', '10', '20', '30', '40'), ('0', '0.7', '1.4', '2.1', '2.8')),
    ('oil', 'Oil Temp', '{{oil}}', '{{u:temp}}', {'signal': 'oil', 'min': 50, 'max': 150, 'red': 0.8},
     ('122', '167', '212', '257', '302'), ('50', '75', '100', '125', '150')),
    ('intake', 'Intake Temp', '{{intake}}', '{{u:temp}}', {'signal': 'intake', 'min': 0, 'max': 100, 'red': 0.6},
     ('32', '77', '122', '167', '212'), ('0', '25', '50', '75', '100')),
    ('oilP', 'Oil Pressure', '{{oilP}}', '{{u:boostLc}}', {'signal': 'oilP', 'min': 0, 'max': 5.516, 'red': 1},
     ('0', '20', '40', '60', '80'), ('0', '1.4', '2.8', '4.1', '5.5')),
    ('coolant', 'Water Temp', '{{coolant}}', '{{u:temp}}', {'signal': 'coolant', 'min': 50, 'max': 130, 'red': 0.81},
     ('122', '158', '194', '230', '266'), ('50', '70', '90', '110', '130')),
]
PICKS = {k: {c[0]: c[4] for c in CHOICES} for k in ('left0', 'left1')}
ARCS = [(-68.0, 136.0), (248.0, -136.0)]   # top scale: start, sweep (clockwise); bottom: the other way round, left to right


def text(id_, x, y, w, h, t, font, color='fg', align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(round(x)), 'y': int(round(y)), 'w': int(w), 'h': int(h),
         'text': t, 'font': font, 'color': color, 'align': align}
    d.update({k: v for k, v in kw.items() if v is not None})
    return d


def centred(id_, cx, cy, w, h, t, font, color='fg', align='center', **kw):
    """A text box of w x h whose middle is at cx, cy (h is the font's cell)."""
    return text(id_, cx - w / 2.0, cy - h / 2.0, w, h, t, font, color, align, **kw)


CAM_TACH = [960, 382, 270]                 # "Leave room for the driver camera": the rev counter lower and smaller, its top
                                           # (y 112) clear of the camera (visible.CAMERA y 0..110), its foot above the strip
CAM_FONTS = {'ci_num': 'ci_num_c', 'ci_speed': 'ci_speed_c', 'ci_gear': 'ci_gear_c'}


def build(cells):
    widgets = []
    car = [RIGHT[0], int(round(RIGHT[1] + 5 * KS)), 57, 129]
    for cam in (False, True):
        cx, cy, R = CAM_TACH if cam else TACH
        k = R / 322.0
        tg = 'cameraNotch' if cam else '!cameraNotch'
        sfx = '_c' if cam else ''
        fn = (lambda f: CAM_FONTS.get(f, f)) if cam else (lambda f: f)
        rb1, rb0 = R - 64 * k, R - 150 * k
        SP_R = cx + 58 * k / K                            # the speed's digits end here (right-aligned, growing leftward)
        gbox = [SP_R + 14 + 20 * k, cy + 82 * k, 20 * k, 30 * k]   # the gear's box a fixed gap after the speed
        widgets.append({'id': 'dash' + sfx, 'type': 'gdash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
                        'tach': [cx, cy, R, START, SWEEP, THOUSANDS], 'zones': ZONES, 'left': LEFT, 'right': RIGHT,
                        'gbox': [round(v, 1) for v in gbox], 'car': car, 'toggle': tg,
                        # the Waze map in the right dial's face ("Show Waze map inside the theme"), the tyres hidden meanwhile
                        'hole': [RIGHT[0] - MAP_R, RIGHT[1] - MAP_R, 2 * MAP_R, 2 * MAP_R], 'holeWhen': 'mapUp', 'holeInset': 0, 'holeIf': 'circuitMap=map',
                        'arcs': [{'pick': 'left0', 'signal': 'boost', 'min': 0, 'max': 2.758, 'red': 0.75},
                                 {'pick': 'left1', 'signal': 'oil', 'min': 50, 'max': 150, 'red': 0.8}]})
        # --- the rev counter's numbers on the red band; its labels, the speed, the gear --------------------------------
        nr = (rb0 + rb1) / 2
        for kk in range(THOUSANDS + 1):
            a = math.radians(START + SWEEP * kk / float(THOUSANDS))
            widgets.append(centred('rpm%d%s' % (kk, sfx), cx + nr * math.sin(a), cy - nr * math.cos(a), 80, cells[fn('ci_num')],
                                   str(kk), fn('ci_num'), 'bandInk', toggle=tg))
        widgets += [
            centred('mode' + sfx, cx, cy - 70 * k, 300, cells['ci_mode'], '{{mode}}', 'ci_mode', 'dim', toggle=tg),
            centred('rpm_u' + sfx, cx, cy + R - 36 * k, 200, cells['ci_rpm'], 'RPM x 1000', 'ci_rpm', 'dim', toggle=tg),
            text('speed' + sfx, SP_R - 260, cy + 80 * k - cells[fn('ci_speed')] / 2.0, 260, cells[fn('ci_speed')], '{{speed}}',
                 fn('ci_speed'), 'fg', 'right', rate=FAST, toggle=tg),
            centred('speed_u' + sfx, SP_R - 44 * k / K, cy + 134 * k, 120, cells['ci_unit'], '{{u:speedLc}}', 'ci_unit', 'fg', toggle=tg),
            centred('gear' + sfx, gbox[0], gbox[1], 2 * gbox[2], cells[fn('ci_gear')], '{{gearnum}}', fn('ci_gear'), 'hot', rate=FAST, toggle=tg),
        ]
    # --- the left dial: per spot and choice, the scale's five numbers and the value in the middle ----------------------
    lx, ly, lr = LEFT
    linner = lr - 22 * lr / 322.0
    anr = ((linner - 98) + (linner - 44)) / 2
    for spot, (a0, sw) in enumerate(ARCS):
        vy = ly + (-42 if spot == 0 else 78) * KS          # the value's middle
        for key, label, tok, unit, _scale, us, metric in CHOICES:
            pick = 'left%d=%s' % (spot, key)
            for j in range(5):
                a = math.radians(a0 + sw * j / 4.0)
                x, y = lx + anr * math.sin(a), ly - anr * math.cos(a)
                sysk = 'uPress' if key in ('boost', 'oilP') else 'uTemp'   # the scale follows Temperature / Pressure
                for units, labels in (('us', us), ('metric', metric)):
                    widgets.append(centred('a%d%s_%d%s' % (spot, key, j, units[0]), x, y, 70, cells['ci_anum'], labels[j],
                                           'ci_anum', 'bandInk', toggle=pick + '&' + sysk + '=' + units))
            widgets += [
                centred('l%d%s_h' % (spot, key), lx, vy - 40 * KS, 220, cells['ci_lab'], label, 'ci_lab', 'dim', toggle=pick),
                text('l%d%s_v' % (spot, key), lx - 8 * KS - 200, vy + 4 * KS - cells['ci_val'] / 2.0, 200, cells['ci_val'],
                     tok, 'ci_val', 'fg', 'right', toggle=pick, rate=FAST if key == 'boost' else None),
                text('l%d%s_u' % (spot, key), lx + 2 * KS, vy + 14 * KS - cells['ci_unit'] / 2.0, 80, cells['ci_unit'],
                     unit, 'ci_unit', 'fg', 'left', toggle=pick),
            ]
    # --- the right dial: the car (an image over the shader's tyres), each tyre's pressure and temperature ---------------
    rx, ry, rr = RIGHT
    widgets.append({'id': 'tyre_car', 'type': 'icon', 'icon': 'carTop', 'z': 5, 'x': car[0] - round(car[2] * 1.16),
                    'y': car[1] - car[3], 'w': 2 * round(car[2] * 1.16), 'h': 2 * car[3], 'toggle': '!mapHere'})
    widgets += [
        centred('tyre_head', rx, ry - 202 * KS, 200, cells['ci_head'], 'Tires', 'ci_head', 'fg', toggle='!mapHere'),
        centred('tyre_u', rx, ry + 199 * KS, 120, cells['ci_head'], '{{u:pressure}}', 'ci_head', 'fg', toggle='!mapHere'),
    ]
    for pos, sx, sy in (('FL', -1, -1), ('FR', 1, -1), ('RL', -1, 1), ('RR', 1, 1)):
        x, y = rx + sx * 142 * KS, car[1] + sy * car[3] * 0.6
        widgets += [
            centred('tp_' + pos, x, y - 17 * KS, 110, cells['ci_tp'], '{{tyreP:%s}}' % pos, 'ci_tp', 'fg', toggle='!mapHere'),
            centred('tt_' + pos, x, y + 29 * KS, 110, cells['ci_tt'], '{{tyreT:%s}}{{u:temp}}' % pos, 'ci_tt', 'cool', toggle='!mapHere'),
        ]
    # --- the strip: covered, nothing in it; BMW's gear letter left clear ------------------------------------------------
    widgets += [
        {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60,
         'color': 'bg', 'stripRow': 'l'},
        {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60,
         'color': 'bg', 'stripRow': 'r'},
    ]
    # the fast numbers on their own small layers; slow texts checked less often (as Apex)
    for w in widgets:
        if w.get('id') in ('gear', 'speed', 'gear_c', 'speed_c') or (w['id'][:1] == 'l' and w['id'].endswith('_v')):
            w['own'] = True
        elif w['type'] == 'text' and 'rate' not in w:
            toks = [t.split('}}')[0] for t in w['text'].split('{{')[1:]]
            if any(t in ('oil', 'intake', 'oilP', 'mode', 'coolant') for t in toks):
                continue
            w['rate'] = 2000 if all(t.startswith('u:') for t in toks) else 1000
    return {
        'schemaVersion': 2,
        'name': 'Circuit',
        'theme': 'circuit',
        '_about': 'A German track-car style cluster, generated by tools/gen_circuit.py (edit that and regenerate): one gdash '
                  'layer draws the carbon backdrop and three round dials: the rev counter (0..8 on a red band, a cream '
                  'needle), a two-scale gauge on the left (picked: boost, oil, intake, oil pressure) and the tyres on the '
                  'right. The speed and gear in the rev counter\'s face. Nothing in the strip.',
        'picks': PICKS,
        'widgets': widgets,
    }


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    fonts = root + '/apps/cluster_themes/hud/fonts/'
    cells = {}
    for f in ('ci_num_c', 'ci_speed_c', 'ci_gear_c', 'ci_num', 'ci_anum', 'ci_speed', 'ci_gear', 'ci_val', 'ci_tp', 'ci_unit', 'ci_lab', 'ci_head', 'ci_tt',
              'ci_mode', 'ci_rpm'):
        cells[f] = json.load(open(fonts + f + '.json'))['cellHeight']
    path = root + '/apps/cluster_themes/hud/layouts/circuit.json'
    with open(path, 'w') as f:
        json.dump(build(cells), f, indent=2)
    print('wrote ' + path)
