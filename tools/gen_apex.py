"""gen_apex.py - writes apps/cluster_themes/hud/layouts/apex.json

Apex: a mid-engine supercar style needle dash on the 1920x720 cluster, drawn by one cdash effect layer (shaders.js):
- a carbon backdrop with red-glow side panels;
- a round rev counter in the middle, 0..8, its band lit white up to the revs over fixed amber-to-red zones, a red
  needle; the gear big in the middle, the drive mode under it, the speed in the open quarter at the bottom right;
- left: boost and oil temperature, each a value over a line bar with a marker, min / max under it and a red end zone;
  coolant along the bottom;
- right: a G-meter (gmeter) under a "Performance" header; fuel along the bottom;
- the theme's own clock, range and outside temperature in the strip below, BMW's gear letter left uncovered.

    python3 tools/gen_apex.py .
"""
import json
import math
import sys

W, H = 1920, 660
CX, CY, R, BAND = 960, 330, 300, 34
START, SWEEP, THOUSANDS = 100, 260, 8
ZONES = [6500, 7000]          # amber from 6500 rpm, red from 7000

# the min / max labels follow the Units setting (this engine's toggles take one setting; a separate temperature or
# pressure unit setting is not followed by these labels, only by the values)
PSI = ['units=us']
BAR = ['units=metric']
DEGF = ['units=us']
DEGC = ['units=metric']


def text(id_, x, y, w, h, t, font, color='fg', align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(round(x)), 'y': int(round(y)), 'w': int(w), 'h': int(h),
         'text': t, 'font': font, 'color': color, 'align': align}
    d.update(kw)
    return d


def unit_labels(id_, x, y, w, align, lo_hi_by_unit):
    """Min / max labels under a bar, one copy per unit condition."""
    out = []
    for j, (conds, label) in enumerate(lo_hi_by_unit):
        for i, cond in enumerate(conds):
            out.append(text('%s_%d%d' % (id_, j, i), x, y, w, 30, label, 'r_label', 'dim', align, toggle=cond))
    return out


def readout(n, x0, x1, y, label, tok, unit_tok, bar, lo, hi):
    """A left-panel block: label, a rule, the value and unit, the bar, min / max under it."""
    mid = (x0 + x1) / 2
    out = [text('r%d_l' % n, mid - 220, y, 440, 42, label, 'v_title', 'accent'),
           text('r%d_v' % n, mid - 210, y + 56, 240, 82, tok, 'a_big', 'fg', 'right'),
           text('r%d_u' % n, mid + 38, y + 96, 120, 36, unit_tok, 'm_unit', 'fg', 'left')]
    out += unit_labels('r%d_lo' % n, bar['x'] - 10, bar['y'] + 14, 80, 'left', lo)
    out += unit_labels('r%d_hi' % n, bar['x'] + bar['w'] - 70, bar['y'] + 14, 80, 'right', hi)
    return out


def build():
    widgets = []
    # --- the bars and rule lines the shader draws ---------------------------------------------------------------
    LX0, LX1 = 110, 590            # the left panel's content
    RX0, RX1 = 1330, 1810          # the right panel's content
    bars = [
        {'x': 140, 'y': 296, 'w': 420, 'signal': 'boost', 'min': 0, 'max': 2.758, 'red': 0.75},
        {'x': 140, 'y': 506, 'w': 420, 'signal': 'oil', 'min': 50, 'max': 150, 'red': 0.8},
        {'x': 300, 'y': 606, 'w': 200, 'signal': 'coolant', 'min': 40, 'max': 130, 'red': 0.85},
        {'x': 1420, 'y': 606, 'w': 200, 'signal': 'fuel', 'min': 0, 'max': 1, 'red': 1},
    ]
    lines = [[LX0, 192, LX1, 192], [LX0, 402, LX1, 402], [RX0, 192, RX1, 192],
             [LX0, 560, LX1, 560], [RX0, 560, RX1, 560]]
    widgets.append({'id': 'dash', 'type': 'cdash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
                    'tach': [CX, CY, R, BAND, START, SWEEP, THOUSANDS], 'zones': ZONES,
                    'panels': [640, 1280, 120, 660], 'bars': bars, 'lines': lines})
    # --- the G-meter --------------------------------------------------------------------------------------------
    widgets.append({'id': 'gmeter', 'type': 'gmeter', 'class': 'content', 'z': 2, 'x': 1435, 'y': 205, 'w': 330,
                    'h': 290, 'conn': 1})
    # --- rev counter numbers, inside the marks ------------------------------------------------------------------
    num_r = R - BAND - 64
    for k in range(THOUSANDS + 1):
        a = math.radians(START + SWEEP * k / float(THOUSANDS))
        x, y = CX + num_r * math.cos(a), CY + num_r * math.sin(a)
        col = 'hot' if k * 1000 >= ZONES[1] else 'fg'
        widgets.append(text('rpm%d' % k, x - 35, y - 20, 70, 40, str(k), 'a_num', col))
    # --- the middle: gear, drive mode, speed in the open quarter, the scale's unit ------------------------------
    widgets += [
        text('gear', CX - 110, CY - 100, 220, 145, '{{gearnum}}', 'a_gear', 'fg', hotWhen='now'),
        text('mode', CX - 120, CY + 56, 240, 24, '{{mode}}', 'v_label', 'accent'),
        text('rpm_u1', CX + 170, CY + 40, 120, 24, 'RPM', 'v_label', 'hot', 'left'),
        text('rpm_u2', CX + 170, CY + 62, 120, 24, 'x1000', 'v_label', 'dim', 'left'),
        text('speed', CX + 20, CY + 106, 200, 89, '{{speed}}', 'a_speed', 'fg', 'right'),
        text('speed_u', CX + 100, CY + 196, 120, 24, '{{u:speed}}', 'v_label', 'dim', 'right'),
    ]
    # --- left: boost and oil temperature ------------------------------------------------------------------------
    widgets += readout(0, LX0, LX1, 140, 'Boost', '{{boost}}', '{{u:boostLc}}', bars[0],
                       [(PSI, '0'), (BAR, '0')], [(PSI, '40'), (BAR, '2.8')])
    widgets += readout(1, LX0, LX1, 350, 'Oil Temperature', '{{oil}}', '{{u:temp}}', bars[1],
                       [(DEGF, '122'), (DEGC, '50')], [(DEGF, '302'), (DEGC, '150')])
    # --- the bottom row: coolant left, fuel right ---------------------------------------------------------------
    widgets += [
        text('cool_v', 120, 590, 150, 30, '{{coolant}} {{u:temp}}', 'r_label', 'fg', 'right'),
        {'id': 'cool_i', 'type': 'icon', 'z': 5, 'x': 520, 'y': 590, 'w': 32, 'h': 32, 'icon': 'therm', 'color': 'fg'},
        {'id': 'fuel_i', 'type': 'icon', 'z': 5, 'x': 1370, 'y': 590, 'w': 32, 'h': 32, 'icon': 'fuel', 'color': 'fg',
         'conn': 1},
        text('fuel_v', 1640, 590, 150, 30, '{{fuelPct}} %', 'r_label', 'fg', 'left', conn=1),
    ]
    # --- right: the G-meter's header and readouts ---------------------------------------------------------------
    widgets += [
        text('perf', RX0, 140, RX1 - RX0, 42, 'Performance', 'v_title', 'fg', conn=1),
        text('g_vals', 1370, 506, 460, 42, '{{gSide}}    {{gFwd}}', 'v_title', 'fg', conn=1),
    ]
    # --- the bottom strip: clock, range, outside temperature; BMW's gear letter left uncovered ------------------
    widgets += [
        {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60,
         'color': 'bg', 'stripRow': 'l'},
        {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60,
         'color': 'bg', 'stripRow': 'r'},
        text('strip_time', 140, 674, 130, 30, '{{time}}', 'r_label', 'fg', 'right', z=3, stripRow='l'),
        text('strip_ampm', 276, 674, 40, 30, '{{ampmLc}}', 'r_label', 'dim', 'left', z=3, stripRow='l'),
        text('strip_range', 860, 674, 120, 30, '{{range}}', 'r_label', 'fg', 'right', z=3, stripRow='l'),
        text('strip_range_u', 986, 674, 40, 30, '{{u:distLc}}', 'r_label', 'dim', 'left', z=3, stripRow='l'),
        text('strip_out', 1670, 674, 80, 30, '{{ambientN}}', 'r_label', 'fg', 'right', z=3, stripRow='r'),
        text('strip_out_u', 1756, 674, 40, 30, '{{u:temp}}', 'r_label', 'dim', 'left', z=3, stripRow='r'),
    ]
    return {
        'schemaVersion': 2,
        'name': 'Apex',
        'theme': 'apex',
        '_about': 'A needle dash in a mid-engine supercar style, generated by tools/gen_apex.py (edit that and regenerate): '
                  'one cdash layer draws the carbon backdrop with red-glow side panels, the rev counter (0..8, lit white to '
                  'the revs, amber from 6500 and red from 7000 rpm, a red needle), the line bars and rules. Gear in the '
                  'middle, speed in the open quarter, boost and oil temperature left, a G-meter right, coolant and fuel '
                  'along the bottom. No map window. Full screen: the theme\'s own clock, range and outside temperature in '
                  'the strip, BMW\'s gear letter left uncovered.',
        'widgets': widgets,
    }


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    path = root + '/apps/cluster_themes/hud/layouts/apex.json'
    with open(path, 'w') as f:
        json.dump(build(), f, indent=2)
        f.write('\n')
    print('wrote', path)
