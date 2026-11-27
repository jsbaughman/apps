"""gen_vetro.py - writes apps/cluster_themes/hud/layouts/vetro.json

Vetro: an Italian GT style cluster on the 1920x720 panel (Nov 24 2026, after photos of a Ferrari's dash), drawn by one
rdash effect layer (shaders.js) with text layers over it:
- the floor: a perforated metal plate seen low, lit in front, black toward the horizon, the dash's shadows and a soft
  reflection of the dial on it;
- the rev counter in the middle under glass: 0 at six o'clock, clockwise to 8 at half past one; a ladder of ticks with
  a dot at each thousand, red past the redline; silver Michroma numbers (a free face after Microgramma) with a soft
  shadow; a red needle with a glow and a centre cap; the face black, red or yellow (setting "vetroDial"); see-through
  navy boxes for the speed (mph / km/h) and the gear (AUTO / MANUAL under it) in its lower right;
- on the left a borderless blue panel fading into the dial: four recessed bars (boost, or intake with "Show boost" off;
  oil temperature; water temperature; oil pressure) with their readings, the fuel cells and the range under it;
- on the right a framed glass panel: the drive mode, "Tires", the car as an x-ray from above, each tyre's pressure and
  temperature in a box, its wheel green or red (under 33 psi).
With "Show Waze map inside the theme" on, Waze's map takes the left panel while it shows; the right panel then has the car
a bit smaller with two of the bars (boost or intake, oil) side by side under it.
Nothing in the strip (covered, BMW's gear letter left clear, as Circuit).

    python3 tools/gen_vetro.py .
"""
import json
import math
import sys

W, H = 1920, 660
CX, CY, R = 960, 330, 300
START, SWEEP, THOUSANDS, RED = 180, 225, 8, 7200
FAST = 45
LEFT = [200, CY - 0.56 * R, CY + 0.80 * R, 26]          # the left panel: its end x, top, bottom, bow
RIGHT = [CY - 0.60 * R, CY + 0.86 * R, 1890, 1846]      # the right panel: top, bottom, right x at the top, at the bottom
CAR = [1560, 400, 175, 90]
BAR_R, BAR_W = 602, 320                                # the left bars: one column, its right edge clear of the dial
HV = [98, 220, 300]
TUNE = [1312, 250, 248, 140]                            # the Tuning tiles (vetroRight): the first's x, y, w, h; 22 / 18 px apart
# the Waze map in the left panel (setting "Show Waze map inside the theme"): the window, and the right panel meanwhile:
# the car a bit smaller and higher, two of the bars (boost or intake, oil) side by side under it
# cameraNotch: the rev counter lower and smaller, its top clear of the camera; how small by "vetroCamTach" (the camera
# sits lower over some dials, by the driver's eye and the screen's depth): large (top y 114), medium (y 150), small (y 180)
# (small: the right panel's top (y 150) must stay inside the dark band round the dial, R + 36)
CAM_TACH = {'large': (960, 372, 258), 'medium': (960, 392, 242), 'small': (960, 408, 228)}
CAM_FONT = {'large': '_c', 'medium': '_cm', 'small': '_cs'}
MAP_LEFT = 46                                           # the left panel reaches out to here while the map shows
MAP = [24, LEFT[1] + 14, CX - 40 - 24, LEFT[2] - 14 - (LEFT[1] + 14)]   # its left end is cut along the panel's bow
MAP_HV = [300, 114, -300]                               # the HV gauge meanwhile: lying above the panel, x, y, length
MAP_CAR = [1566, 346, 160, 74]
# Waze's arrow sits a little right of its map's centre: the map's centre at 26 % across the window puts the arrow in the
# middle of the part that shows (the window runs on under the dial, where it fades out)
MAP_BARS = [{'of': 0, 'x': 1294, 'y': 536, 'w': 236}, {'of': 1, 'x': 1598, 'y': 536, 'w': 236}]                                     # the HV battery gauge (vetroHv): x, y, height (30 wide)                              # the car's centre, the tyre boxes' x offset, the wheels' y offset
FACES = {                                                # the numbers' colours per face: (0..7, 8)
    'black': (('num', 'numLow'), ('numRed', 'numRedLow')),
    'red': (('num', 'numLow'), ('numBlack', 'numBlackLow')),
    'yellow': (('num', 'numLow'), ('numRed', 'numRedLow')),        # white on the yellow face (Nov 26 2026)
}
# the left bars: icon, value, unit, signal, min, max (+ the boost row's stand-in while "Show boost" is off)
ROWS = [
    ('gauge', '{{boost}}', '{{u:boostLc}}', 'vt_small', 'boost', 0, 2.758),
    ('oilcan', '{{oil}}', '{{u:temp}}', 'vt_deg', 'oil', 50, 150),
    ('therm', '{{coolant}}', '{{u:temp}}', 'vt_deg', 'coolant', 50, 130),
    ('oilcan', '{{oilP}}', '{{u:boostLc}}', 'vt_small', 'oilP', 0, 5.516),
]


def build(fonts):
    cell = lambda f: fonts[f]['cellHeight']
    base = lambda f: fonts[f]['baseline']
    widgets = []

    def text(id_, x, baseline, w, t, font, color='fg', align='left', **kw):
        """A text box w wide whose glyphs sit on baseline; x is its left (align left), right (right) or middle (center)."""
        x0 = x if align == 'left' else x - w if align == 'right' else x - w / 2.0
        d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(round(x0)), 'y': int(round(baseline - base(font))), 'w': int(w),
             'h': cell(font), 'text': t, 'font': font, 'color': color, 'align': align}
        d.update({k: v for k, v in kw.items() if v is not None})
        widgets.append(d)

    # bars' boxes: right ends on a curve round the dial, so the stack leans with it
    bars, rows_y = [], [LEFT[1] + 62 + i * 86 for i in range(4)]
    for (icon, tok, unit, ufont, sig, mn, mx), by in zip(ROWS, rows_y):
        b = {'x': BAR_R - BAR_W, 'y': by, 'w': BAR_W, 'signal': sig, 'min': mn, 'max': mx}
        if sig == 'boost':
            b.update({'alt': 'intake', 'altMin': 0, 'altMax': 100, 'altWhen': 'showBoost'})
        bars.append(b)
    F = [BAR_R - BAR_W, LEFT[2] + 30, 250]
    # the dash, the needle, the numbers, the speed and the gear: as they are, or with the rev counter lower and smaller,
    # clear of the driver camera ("Leave room for the driver camera", cameraNotch), as Circuit's
    for cam in (None, 'large', 'medium', 'small'):
        cx, cy, rr = CAM_TACH[cam] if cam else (CX, CY, R)
        tg, sfx = ('cameraNotch&vetroCamTach=' + cam, CAM_FONT[cam]) if cam else ('!cameraNotch', '')
        fn = (lambda f, s=sfx: f + s)
        both = lambda t: tg + '&' + t if t else tg
        widgets.append({'id': 'dash' + sfx, 'type': 'rdash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
                        'tach': [cx, cy, rr, START, SWEEP, THOUSANDS], 'red': RED, 'left': [round(v, 1) for v in LEFT],
                        'right': [round(v, 1) for v in RIGHT], 'bars': bars, 'fuel': F, 'hv': HV, 'car': CAR,
                        'tbox': [68, 37, 69, 1], 'hole': MAP, 'holeWhen': 'mapUp', 'holeInset': 0, 'holeAim': [0.35, 0.5],
                        'mapLeft': MAP_LEFT, 'mapHv': MAP_HV, 'mapCar': MAP_CAR, 'mapTbox': [58, 31, 56, 0.8],
                        'mapBars': MAP_BARS, 'tune': TUNE, 'toggle': tg})
        # the needle and its cap on a layer of their own, over the numbers (z 6)
        widgets.append({'id': 'needle' + sfx, 'type': 'rneedle', 'class': 'content', 'z': 6, 'x': cx - rr, 'y': cy - rr,
                        'w': 2 * rr, 'h': 2 * rr, 'tach': [cx, cy, rr, START, SWEEP, THOUSANDS], 'conn': 1,
                        'toggle': both('vetroRev=needle')})
        # the numbers: a soft shadow under each, the number per face (silver; the redline one red)
        nr, nf = rr - 77, fn('vt_num')                  # (the ladder 19 px wide)
        bw = {'large': 72, 'medium': 66, 'small': 58}[cam] if cam else 100                        # the boxes narrower on the small dial: neighbours must not overlap (one sheet)
        for k in range(THOUSANDS + 1):
            a = math.radians(START + SWEEP * k / float(THOUSANDS))
            x, y = cx + nr * math.sin(a), cy - nr * math.cos(a)
            top = y - cell(nf) / 2.0 + 2
            widgets.append({'id': 'n%d_sh%s' % (k, sfx), 'type': 'text', 'z': 4, 'x': int(round(x - bw / 2 + 1)), 'y': int(round(top + 4)),
                            'w': bw, 'h': cell(nf), 'text': str(k), 'font': nf, 'color': 'shade', 'align': 'center',
                            'glow': True, 'rate': 60000, 'toggle': tg})
            for face, (lo, hi) in FACES.items():
                c1, c2 = hi if k * 1000 >= RED else lo
                widgets.append({'id': 'n%d_%s%s' % (k, face, sfx), 'type': 'text', 'z': 5, 'x': int(round(x - bw / 2)), 'y': int(round(top)),
                                'w': bw, 'h': cell(nf), 'text': str(k), 'font': nf, 'color': c1, 'color2': c2,
                                'align': 'center', 'toggle': both('vetroDial=' + face), 'rate': 60000})
        # the speed (right-aligned, its unit after it) and the gear (AUTO / MANUAL under it), in their glass boxes
        ux = cx + rr - 87 if cam else cx + 0.687 * rr       # the unit clear of the box's curved end on the small dial
        text('speed' + sfx, ux - 8, cy - 0.08 * rr + 0.36 * cell(fn('vt_speed')), 220, '{{speed}}', fn('vt_speed'), 'fg', 'right',
             rate=FAST, own=True, toggle=tg)
        text('speed_u' + sfx, ux, cy - 0.033 * rr + 7, 80, '{{u:speedLc}}', 'vt_unit', 'dim', 'left', toggle=tg)
        text('gear' + sfx, cx + 0.30 * rr, cy + 0.327 * rr + 0.36 * cell(fn('vt_gear')), 120, '{{gearnum}}', fn('vt_gear'), 'fg', 'center',
             rate=FAST, own=True, toggle=tg)
        text('prog' + sfx, cx + 0.30 * rr - 32, cy + 0.513 * rr, 140, '{{progWord}}', 'vt_word', 'dim', 'left', toggle=tg)

    # --- the bars: the reading over the right end (the number, the unit small after it), the icon before the track; in
    #     the left panel, or the first two under the car while the map shows
    places = [(b['x'], b['y'], BAR_W, i, '!mapUp', '') for i, b in enumerate(bars)]
    places += [(m['x'], m['y'], m['w'], m['of'], 'mapUp', 'm') for m in MAP_BARS]
    for x0, by, bw, i, mt, sfx in places:
        icon, tok, unit, ufont, sig, mn, mx = ROWS[i]
        rx = x0 + bw
        if sig == 'boost':
            for tg, t2, ic in (('showBoost', tok, 'gauge'), ('!showBoost', '{{intake}}', 'therm')):
                k = '' if tg == 'showBoost' else 'i'
                text('b%d_v%s%s' % (i, k, sfx), rx - 44, by - 8, 160, t2, 'vt_val', 'fg', 'right', toggle=tg + '&' + mt,
                     rate=FAST if tg == 'showBoost' else None, own=True)
                text('b%d_u%s%s' % (i, k, sfx), rx - 38, by - 8, 44, unit if tg == 'showBoost' else '{{u:temp}}',
                     ufont if tg == 'showBoost' else 'vt_deg', 'dim', 'left', toggle=tg + '&' + mt)
                widgets.append({'id': 'b%d_icon%s%s' % (i, k, sfx), 'type': 'icon', 'icon': ic, 'z': 5,
                                'x': int(x0 - 45), 'y': int(by - 5), 'w': 35, 'h': 35, 'color': 'fg', 'toggle': tg + '&' + mt})
            continue
        text('b%d_v%s' % (i, sfx), rx - 44, by - 8, 160, tok, 'vt_val', 'fg', 'right', own=True, toggle=mt)
        text('b%d_u%s' % (i, sfx), rx - 38, by - 8, 44, unit, ufont, 'dim', 'left', toggle=mt)
        widgets.append({'id': 'b%d_icon%s' % (i, sfx), 'type': 'icon', 'icon': icon, 'z': 5, 'x': int(x0 - 45), 'y': int(by - 5),
                        'w': 35, 'h': 35, 'color': 'fg', 'toggle': mt})
        if sig == 'oilP':
            text('b%d_p%s' % (i, sfx), x0 - 14, by + 5, 14, 'P', 'vt_p', 'fg', 'center', toggle=mt)
    # --- the peak boost (setting "vetroPeak"): PEAK and its reading in amber over the boost bar's left end (the marker on
    #     the bar is the shader's); in the left panel, or under the car while the map shows
    # (under the car it starts over the icon, clear of the reading)
    for x0, by, mt, sfx in ((bars[0]['x'], bars[0]['y'], '!mapUp', ''), (MAP_BARS[0]['x'] - 44, MAP_BARS[0]['y'], 'mapUp', 'm')):
        tg = 'vetroPeak&showBoost&' + mt
        text('pk_l' + sfx, x0, by - 9, 44, '{{pullPeakLabel}}', 'vt_tiny', 'accent', 'left', toggle=tg)
        text('pk_v' + sfx, x0 + 50, by - 9, 80, '{{pullPeak}}', 'vt_pk', 'accent', 'left', toggle=tg)
    # --- the HV battery (setting "vetroHv"): the charge over the gauge, HV under its battery
    hx = HV[0] + 15
    ht = 'vetroHv&!mapUp'
    text('hv_v', hx + 8, HV[1] - 14, 100, '{{hvSoc}}', 'vt_val', 'fg', 'right', toggle=ht)
    text('hv_u', hx + 11, HV[1] - 14, 30, '%', 'vt_small', 'dim', 'left', toggle=ht)
    widgets.append({'id': 'hv_icon', 'type': 'icon', 'icon': 'battery', 'z': 5, 'x': hx - 17, 'y': HV[1] + HV[2] + 6, 'w': 35,
                    'h': 35, 'color': 'fg', 'toggle': ht})
    text('hv_l', hx, HV[1] + HV[2] + 60, 60, 'HV', 'vt_word', 'cool', 'center', toggle=ht)
    # while the map shows: lying above the panel, its battery before it, the charge and HV after it
    hm, hy = 'vetroHv&mapUp', MAP_HV[1] + 8
    widgets.append({'id': 'hv_icon_m', 'type': 'icon', 'icon': 'battery', 'z': 5, 'x': MAP_HV[0] - 42, 'y': hy - 15, 'w': 30,
                    'h': 30, 'color': 'fg', 'toggle': hm})
    xe = MAP_HV[0] - MAP_HV[2]
    text('hv_vm', xe + 14, hy + 9, 100, '{{hvSoc}}', 'vt_val', 'fg', 'left', toggle=hm)
    text('hv_um', xe + 72, hy + 9, 30, '%', 'vt_small', 'dim', 'left', toggle=hm)
    text('hv_lm', xe + 106, hy + 9, 40, 'HV', 'vt_word', 'cool', 'left', toggle=hm)
    # --- the fuel: the pump icon before the cells, the range in amber after them
    widgets.append({'id': 'fuel_icon', 'type': 'icon', 'icon': 'fuel', 'z': 5, 'x': F[0] - 42, 'y': F[1] - 4, 'w': 32, 'h': 32,
                    'color': 'fg'})
    text('range', F[0] + F[2] + 114, F[1] + 22, 110, '{{range}}', 'vt_range', 'accent', 'right')
    text('range_u', F[0] + F[2] + 120, F[1] + 22, 50, '{{u:distLc}}', 'vt_small', 'accent', 'left')

    # --- the right panel: the drive mode by its stroke, the heading, the car, the tyres' readings in their boxes
    band = R + 36
    tx = CX + math.sqrt((band + 6) ** 2 - (RIGHT[0] + 18 - CY) ** 2) + 10
    text('mode', tx + 30, RIGHT[0] + 24, 400, '{{mode}}', 'vt_mode', 'accent', 'left')
    text('tyre_head', tx + 34, RIGHT[0] + 86, 200, 'Tires', 'vt_head', 'head', 'left', toggle='!vetroRight=tuning')
    text('tyre_head_m', tx + 34, RIGHT[0] + 86, 200, 'Tires', 'vt_head', 'head', 'left', toggle='vetroRight=tuning&mapUp')
    text('tune_head', tx + 34, RIGHT[0] + 86, 200, 'Tuning', 'vt_head', 'head', 'left', toggle='vetroRight=tuning&!mapUp')
    # the Tuning tiles: the name, a note at the right, the reading big with its unit (the tracks are the shader's)
    tg = 'vetroRight=tuning&!mapUp'
    for n, (name, note, tok, unit, ufont) in enumerate((('AFR', 'target {{afrT}}', '{{afr}}', ':1', 'vt_sub'),
                                                        ('HPFP', 'rail', '{{hpfp}}', '{{u:boostLc}}', 'vt_unit'),
                                                        ('TIMING', 'advance', '{{timing}}', '°', 'vt_deg'),
                                                        ('KNOCK', 'retard', '{{knockR}}', '°', 'vt_deg'))):
        x0, y0 = TUNE[0] + (n % 2) * (TUNE[2] + 22), TUNE[1] + (n // 2) * (TUNE[3] + 18)
        xr = x0 + TUNE[2] - 18
        text('tu%d_n' % n, x0 + 18, y0 + 27, 120, name, 'vt_lab', 'cool', 'left', toggle=tg)
        text('tu%d_s' % n, xr, y0 + 27, 120, note, 'vt_sub', 'dim', 'right', toggle=tg)
        text('tu%d_u' % n, xr, y0 + 82, 40, unit, ufont, 'dim', 'right', toggle=tg)
        gap = {':1': 20, '°': 16}.get(unit, 40)            # the reading ends just before its unit
        text('tu%d_v' % n, xr - gap, y0 + 82, 170, tok, 'vt_tv', 'accent' if n == 0 else 'fg', 'right', toggle=tg, own=True)

    # the car and the tyres' readings: full size, or a bit smaller while the map shows
    for mt, sfx, (cx_, cy_, dx_, dy_), cw, bh, pf, py, ty in (('!mapUp&!vetroRight=tuning', '', CAR, 150, 37, 'vt_tp', 40, 64),
                                                             ('mapUp', '_m', MAP_CAR, 124, 31, 'vt_val', 33, 54)):
        widgets.append({'id': 'tyre_car' + sfx, 'type': 'icon', 'icon': 'carXray', 'z': 5, 'x': cx_ - cw // 2, 'y': cy_ - cw,
                        'w': cw, 'h': 2 * cw, 'toggle': mt})
        for pos, sx, sy in (('FL', -1, -1), ('FR', 1, -1), ('RL', -1, 1), ('RR', 1, 1)):
            bx, y0 = cx_ + sx * dx_, cy_ + sy * dy_ - bh
            text('tp_' + pos + sfx, bx + 12, y0 + py, 100, '{{tyreP:%s}}' % pos, pf, 'fg', 'right', toggle=mt)
            text('tpu_' + pos + sfx, bx + 17, y0 + py, 40, '{{u:pressure}}', 'vt_small', 'dim', 'left', toggle=mt)
            text('tt_' + pos + sfx, bx, y0 + ty, 110, '{{tyreT:%s}}{{u:temp}}' % pos, 'vt_tt', 'cool', 'center', toggle=mt)

    # --- the strip: covered, nothing in it; BMW's gear letter left clear ------------------------------------------------
    widgets += [
        {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60,
         'color': 'bg', 'stripRow': 'l'},
        {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60,
         'color': 'bg', 'stripRow': 'r'},
    ]
    # connections (8 layers each): the right panel on 1, the left side on 2, the dial and the strip on 0
    for w in widgets:
        if w['id'].startswith(('dash', 'needle', 'strip')):
            continue
        if w['id'][:1] == 'n' and w['id'][1:2].isdigit():      # the rev counter's numbers: all with the dial (two sheets)
            continue
        if w['x'] >= 1250:
            w['conn'] = 1
        elif w['x'] + w['w'] <= 800:
            w['conn'] = 2
    # slow texts checked less often (as Circuit)
    for w in widgets:
        if w['type'] == 'text' and 'rate' not in w and not w.get('own'):
            toks = [t.split('}}')[0] for t in w['text'].split('{{')[1:]]
            if any(t in ('oil', 'intake', 'oilP', 'mode', 'coolant', 'progWord', 'hvSoc', 'pullPeak', 'pullPeakLabel', 'afr', 'afrT', 'hpfp', 'timing', 'knockR') for t in toks):
                continue
            w['rate'] = 2000 if all(t.startswith('u:') for t in toks) else 1000
    return {
        'schemaVersion': 2,
        'name': 'Vetro',
        'theme': 'vetro',
        '_about': 'An Italian GT style cluster, generated by tools/gen_vetro.py (edit that and regenerate): one rdash layer '
                  'draws a perforated floor, the rev counter under glass (its face black, red or yellow: "vetroDial"), a '
                  'blue panel with four bars and the fuel on the left and a glass tyre panel on the right; the numbers, '
                  'speed, gear and readings are text over it. Nothing in the strip.',
        'widgets': widgets,
    }


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    fdir = root + '/apps/cluster_themes/hud/fonts/'
    fonts = {}
    for f in ('vt_num', 'vt_speed', 'vt_gear', 'vt_word', 'vt_unit', 'vt_small', 'vt_val', 'vt_tp', 'vt_range', 'vt_mode',
              'vt_deg', 'vt_tt', 'vt_head', 'vt_p', 'vt_tiny', 'vt_pk', 'vt_lab', 'vt_tv', 'vt_sub', 'vt_num_c', 'vt_speed_c', 'vt_gear_c',
              'vt_num_cm', 'vt_speed_cm', 'vt_gear_cm', 'vt_num_cs', 'vt_speed_cs', 'vt_gear_cs'):
        j = json.load(open(fdir + f + '.json'))
        fonts[f] = {'cellHeight': j['cellHeight'], 'baseline': j['baseline']}
    path = root + '/apps/cluster_themes/hud/layouts/vetro.json'
    with open(path, 'w') as f:
        json.dump(build(fonts), f, indent=2)
    print('wrote ' + path)
