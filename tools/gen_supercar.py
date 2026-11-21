"""gen_supercar.py - writes apps/cluster_themes/hud/layouts/supercar.json

A supercar-style "virtual cockpit" cluster on the 1920x720 panel, built on the Vector theme's vdash shader:
- a big round segmented rev counter (0..8) in the middle, with the speed, gear and drive mode inside it;
- Power % and Torque % as ring gauges on the right, fuel and oil as smaller rings under them;
- boost / coolant / intake as bars on the left;
- with "Show Waze map inside the theme" on (mapUp), the rev counter moves to the left and the map takes the
  middle (Waze can only appear in the middle of the cluster: BMW's map window, 416..1504 x 120..600).

    python3 tools/gen_supercar.py .   [backdrop 0|1|2]
"""
import json
import math
import sys

W, H = 1920, 660
ZONES = [6500, 7000]   # amber from 6500 rpm, red from 7000 (fixed, not the shift point)
BG = 2                 # backdrop: 0 black, 1 graphite, 2 carbon


def text(id_, x, y, w, h, t, font, color='fg', align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h),
         'text': t, 'font': font, 'color': color, 'align': align}
    d.update(kw)
    return d


# font cell heights (hud/fonts/*.json)
FONT_H = {'sc_num': 42, 's_gear': 65, 'big': 93, 'v_label': 24, 'v_val': 23, 's_unit': 29, 's_val': 26, 's_scale': 27}

# the right-hand ring gauges: the same in both views
RINGS = [
    {'cx': 1470, 'cy': 250, 'r': 92, 'signal': 'powerPct', 'min': 0, 'max': 100, 'color': [0.95, 0.96, 0.98]},
    {'cx': 1710, 'cy': 250, 'r': 92, 'signal': 'torquePct', 'min': 0, 'max': 100, 'color': [0.95, 0.96, 0.98]},
    {'cx': 1470, 'cy': 500, 'r': 62, 'signal': 'fuel', 'min': 0, 'max': 1, 'color': [0.93, 0.13, 0.16]},
    {'cx': 1710, 'cy': 500, 'r': 62, 'signal': 'oil', 'min': 40, 'max': 150, 'color': [0.93, 0.13, 0.16]},
]


def ring_texts():
    out = []
    for i, (lab, tok, unit) in enumerate([('POWER', '{{powerPct}}', '%'), ('TORQUE', '{{torquePct}}', '%')]):
        g = RINGS[i]
        out.append(text('ring%d_l' % i, g['cx'] - 60, g['cy'] - g['r'] - 40, 120, 24, lab, 'v_label', 'fg'))
        out.append(text('ring%d_u' % i, g['cx'] - 40, g['cy'] - 40, 80, 24, unit, 'v_label', 'dim'))
        out.append(text('ring%d_v' % i, g['cx'] - 70, g['cy'] - 14, 140, 70, tok, 'value', 'fg'))
    for i, (lab, tok) in enumerate([('FUEL %', '{{fuelPct}}'), ('OIL {{u:temp}}', '{{oil}}')]):
        g = RINGS[2 + i]
        out.append(text('ring%d_v' % (2 + i), g['cx'] - 50, g['cy'] - 20, 100, 23, tok, 'v_val', 'fg'))
        out.append(text('ring%d_l' % (2 + i), g['cx'] - 60, g['cy'] + g['r'] + 12, 120, 24, lab, 'v_label', 'dim'))
    return out


def tach_view(tag, cx, cy, r_in, r_out, num_r, toggle, hole=None, bars=None, segs=None, num_font='sc_num'):
    """One vdash layer with its rev counter at cx, cy, plus the texts that belong to that view."""
    start, sweep, segs_n = 135, 270, 40
    dash = {'id': 'vdash_' + tag, 'type': 'vdash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
            'toggle': toggle,
            'tach': [cx, cy, r_in, r_out, start, sweep, segs_n],
            'segs': segs or [], 'rings': RINGS, 'bars': bars or [],
            'zones': ZONES, 'face': {'bg': BG, 'shadow': 46 if tag == 'c' else 34, 'dial': True}}
    if hole:
        dash.update({'hole': hole, 'holeWhen': 'mapUp', 'holeInset': 0, 'holeCut': 40})
    out = [dash]
    # big rev numbers inside the ring (0..8, the shader's VDASH_RPM)
    for k in range(9):
        a = math.radians(start + sweep * k / 8.0)
        x, y = cx + num_r * math.cos(a), cy + num_r * math.sin(a)
        nh = FONT_H[num_font]
        out.append(text('%s_rpm%d' % (tag, k), x - 40, y - nh // 2, 80, nh, str(k), num_font, 'fg', toggle=toggle))
    # inside: speed unit, speed, gear, drive mode
    out.append(text(tag + '_su', cx - 80, cy - 150, 160, 29, '{{u:speedLc}}', 's_unit', 'dim', toggle=toggle))
    out.append(text(tag + '_speed', cx - 130, cy - 118, 260, 93, '{{speed}}', 'big', 'fg', toggle=toggle))
    out.append(text(tag + '_gear', cx - 80, cy + 10, 160, 65, '{{gearnum}}', 's_gear', 'fg', toggle=toggle,
                    hotWhen='now'))
    out.append(text(tag + '_mode', cx - 100, cy + 80, 200, 24, '{{mode}}', 'v_label', 'accent', toggle=toggle))
    out.append(text(tag + '_rpmu', cx - 90, cy + r_in - 20, 180, 24, '1/min x 1000', 'v_label', 'dim', toggle=toggle))
    return out


def build():
    widgets = []
    # --- the normal view: rev counter in the middle, bars on the left -------------------------------------------
    bars = [{'x': 150, 'y': 330, 'w': 400, 'signal': 'boost', 'min': 0, 'max': 1.4},
            {'x': 150, 'y': 440, 'w': 400, 'signal': 'coolant', 'min': 40, 'max': 130},
            {'x': 150, 'y': 550, 'w': 400, 'signal': 'intake', 'min': 0, 'max': 80}]
    segs_c = [[150, 250, 560, 250, 2, 0.25], [1360, 120, 1780, 120, 2, 0.25], [1360, 600, 1830, 600, 2, 0.25]]
    widgets += tach_view('c', 960, 340, 228, 304, 188, '!mapUp', bars=bars, segs=segs_c)
    for i, (lab, tok, unit) in enumerate([('BOOST', '{{boost}}', '{{u:boostLc}}'),
                                          ('COOLANT', '{{coolant}}', '{{u:temp}}'),
                                          ('INTAKE', '{{intake}}', '{{u:temp}}')]):
        y = bars[i]['y'] - 44
        widgets.append(text('bar%d_l' % i, 150, y, 200, 24, lab, 'v_label', 'dim', 'left', toggle='!mapUp'))
        widgets.append(text('bar%d_v' % i, 380, y, 110, 23, tok, 'v_val', 'fg', 'right', toggle='!mapUp'))
        widgets.append(text('bar%d_u' % i, 496, y, 64, 24, unit, 'v_label', 'dim', 'left', toggle='!mapUp'))
    # --- the map view: rev counter left, the map in BMW's map window in the middle ------------------------------
    # the map window's octagon frame (as Vector's), plus the right panel's lines
    o = [(646, 120), (1274, 120), (1324, 170), (1324, 550), (1274, 600), (646, 600), (596, 550), (596, 170)]
    segs_m = [[a[0], a[1], b[0], b[1], 2, 0.3] for a, b in zip(o, o[1:] + o[:1])]
    segs_m += [[1360, 120, 1780, 120, 2, 0.25], [1360, 600, 1830, 600, 2, 0.25]]
    widgets += tach_view('m', 330, 340, 186, 254, 158, 'mapUp', hole=[600, 124, 720, 472], segs=segs_m,
                         num_font='s_scale')
    # --- the right-hand rings, the same in both views -----------------------------------------------------------
    widgets += ring_texts()
    # --- the bottom strip: clock, range, outside temperature; BMW's gear letter left uncovered (as vector.json) --
    widgets += [
        {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60,
         'color': 'bg', 'stripRow': 'l'},
        {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60,
         'color': 'bg', 'stripRow': 'r'},
        text('strip_time', 144, 678, 124, 26, '{{time}}', 's_val', 'fg', 'right', z=3, stripRow='l'),
        text('strip_ampm', 274, 676, 35, 29, '{{ampmLc}}', 's_unit', 'dim', 'left', z=3, stripRow='l'),
        text('strip_range', 874, 678, 116, 26, '{{range}}', 's_val', 'fg', 'right', z=3, stripRow='l'),
        text('strip_range_u', 996, 676, 36, 29, '{{u:distLc}}', 's_unit', 'dim', 'left', z=3, stripRow='l'),
        text('strip_out', 1676, 678, 80, 26, '{{ambient}}', 's_val', 'fg', 'right', z=3, stripRow='r'),
        text('strip_out_u', 1762, 676, 27, 29, '{{u:temp}}', 's_unit', 'dim', 'left', z=3, stripRow='r'),
    ]
    for w in widgets:
        if w['type'] == 'text':
            w['z'] = w.get('z', 5)
    return {
        'schemaVersion': 2,
        'name': 'Supercar',
        'theme': 'supercar',
        '_about': 'A supercar-style virtual cockpit, generated by tools/gen_supercar.py (edit that and regenerate): a big '
                  'round rev counter in the middle with the speed, gear and drive mode inside, Power % and Torque % '
                  'rings on the right with fuel and oil under them, boost, coolant and intake bars on the left. With '
                  'the Waze map on, the rev counter moves left and the map takes the middle (rebuilds on the switch). '
                  'Full screen: the theme\'s own clock, range and outside temperature along the bottom, BMW\'s gear '
                  'letter left uncovered.',
        'widgets': widgets,
    }


if __name__ == '__main__':
    root = sys.argv[1]
    if len(sys.argv) > 2:
        BG = int(sys.argv[2])
    path = root + '/apps/cluster_themes/hud/layouts/supercar.json'
    with open(path, 'w') as f:
        json.dump(build(), f, indent=2)
        f.write('\n')
    print('wrote', path)
