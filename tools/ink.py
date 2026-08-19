"""Tuschestrich-Generator fuer SVG.

Erzeugt Striche als gefuellte Umrisspfade mit entlang der Mittellinie
variabler Breite -- siehe doc/stil-tuschezeichnung.md, Abschnitt 11.
Ein `stroke` mit `stroke-width` kaeme nie an den Duktus einer Feder heran.
"""

import math
import random

TAU = 2 * math.pi


# ---------------------------------------------------------------- Geometrie

def catmull(pts, per_seg=14, closed=False):
    """Catmull-Rom-Spline durch die Stuetzpunkte."""
    pts = [tuple(p) for p in pts]
    if len(pts) < 3:
        return pts
    if closed:
        ctrl = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        ctrl = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(ctrl) - 2):
        p0, p1, p2, p3 = ctrl[i - 1], ctrl[i], ctrl[i + 1], ctrl[i + 2]
        for s in range(per_seg):
            t = s / per_seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not closed:
        out.append(pts[-1])
    return out


def resample(pts, step=2.4):
    """Gleichmaessige Abstaende -- damit das Breitenprofil sauber sitzt."""
    if len(pts) < 2:
        return pts
    out = [pts[0]]
    carry = 0.0
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        seg = math.hypot(dx, dy)
        if seg < 1e-9:
            continue
        d = carry
        while d + step <= seg:
            d += step
            out.append((a[0] + dx * d / seg, a[1] + dy * d / seg))
        carry = d - seg
    if math.dist(out[-1], pts[-1]) > 1e-6:
        out.append(pts[-1])
    return out


def resample_n(pts, n):
    """Auf genau n gleich weit verteilte Punkte bringen.

    Noetig, wenn zwei Kurven einander proportional entsprechen sollen:
    beim Paaren nach Index wuerde die laengere von beiden abgeschnitten."""
    if len(pts) < 2 or n < 2:
        return list(pts)
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.dist(a, b))
    gesamt = d[-1]
    if gesamt < 1e-9:
        return [pts[0]] * n
    out, j = [], 0
    for i in range(n):
        t = gesamt * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < t:
            j += 1
        f = (t - d[j]) / ((d[j + 1] - d[j]) or 1e-9)
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f,
                    pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f))
    return out


def laenge(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def normals(pts):
    n = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        n.append((-dy / ln, dx / ln))
    return n


# ------------------------------------------------------------------ Duktus

def wobble(pts, rng, amp=1.3, waves=1.8, hold_ends=True):
    """Niederfrequentes Zittern quer zur Laufrichtung: die Hand ist keine CNC."""
    if amp <= 0:
        return pts
    nrm = normals(pts)
    ph1, ph2 = rng.uniform(0, TAU), rng.uniform(0, TAU)
    w2 = waves * rng.uniform(2.1, 3.4)
    out = []
    n = len(pts) - 1 or 1
    for i, (p, nv) in enumerate(zip(pts, nrm)):
        t = i / n
        d = amp * (0.72 * math.sin(t * waves * TAU + ph1)
                   + 0.28 * math.sin(t * w2 * TAU + ph2))
        if hold_ends:
            d *= math.sin(math.pi * t) ** 0.45
        out.append((p[0] + nv[0] * d, p[1] + nv[1] * d))
    return out


def _profile(t, w):
    """Breite an Position t. w = (Anfang, Mitte, Ende).

    Lagrange durch (0,w0), (0.5,w1), (1,w2): die Mittenbreite wird
    tatsaechlich erreicht -- bei quadratischer Mischung waere sie nur halb
    so gross wie angegeben."""
    w0, w1, w2 = w
    return (w0 * 2 * (t - 0.5) * (t - 1)
            - w1 * 4 * t * (t - 1)
            + w2 * 2 * t * (t - 0.5))


def outline(pts, w, rng=None, breathe=0.42):
    """Umriss eines Strichs mit variabler Breite, inkl. runder Endkappen."""
    if len(pts) < 2:
        return ""
    nrm = normals(pts)
    n = len(pts) - 1
    ph = rng.uniform(0, TAU) if rng else 0.0
    freq = rng.uniform(1.5, 3.5) if rng else 2.0

    half = []
    for i in range(len(pts)):
        t = i / n
        ww = _profile(t, w)
        if rng and breathe:
            ww *= 1.0 + breathe * math.sin(t * freq * TAU + ph)
        half.append(max(ww, 0.0) / 2.0)

    left = [(p[0] + nv[0] * h, p[1] + nv[1] * h) for p, nv, h in zip(pts, nrm, half)]
    right = [(p[0] - nv[0] * h, p[1] - nv[1] * h) for p, nv, h in zip(pts, nrm, half)]

    def cap(idx, sign):
        """Halbkreis um das Strichende; sign=+1 Ende, -1 Anfang."""
        r = half[idx]
        if r < 0.35:
            return []
        p, nv = pts[idx], nrm[idx]
        tx, ty = -nv[1] * sign, nv[0] * sign
        pts_ = []
        for k in range(1, 7):
            a = math.pi * k / 7
            ca, sa = math.cos(a), math.sin(a)
            pts_.append((p[0] + nv[0] * r * ca * sign + tx * r * sa,
                         p[1] + nv[1] * r * ca * sign + ty * r * sa))
        return pts_

    ring = left + cap(len(pts) - 1, 1) + right[::-1] + cap(0, -1)
    return ("M" + f"{ring[0][0]:.1f},{ring[0][1]:.1f}"
            + "".join(f"L{x:.1f},{y:.1f}" for x, y in ring[1:]) + "Z")


# ------------------------------------------------------------- Zeichen-API

class Pen:
    def __init__(self, seed=0):
        self.seed = seed
        self.rng = random.Random(seed)
        self.paths = []
        # Weisse Flaechen, die VOR der Tusche gezeichnet werden: das Papier
        # der Figur selbst. Ohne sie ist eine Strichzeichnung nur Tusche und
        # Transparenz, und ein Hintergrund scheint mitten durch das Gesicht.
        self.flaechen = []
        self.warp = None
        self.turn = 0.0

    def set_turn(self, phi, cx=200.0, R=67.0):
        """Kopfdrehung um die Hochachse als Zylinderprojektion.

        phi > 0 dreht die Nase nach rechts. Punkte auf der Kopfrundung
        wandern ueber die Silhouette hinweg, waehrend deren Rand fast
        stehen bleibt -- so verhaelt sich ein gedrehter Kopf wirklich.
        Was ausserhalb der Rundung liegt (Haarmasse), wird starr mit der
        Kante mitgefuehrt, damit nichts vom Kopf abreisst."""
        self.turn = phi
        if abs(phi) < 1e-6:
            self.warp = None
            return
        kante = R * math.cos(phi)

        def f(x, y):
            u = (x - cx) / R
            if -1.0 <= u <= 1.0:
                return (cx + R * math.sin(math.asin(u) + phi), y)
            return (x + (1.0 if u > 0 else -1.0) * (kante - R), y)

        self.warp = f

    def _w(self, pts):
        return [self.warp(x, y) for x, y in pts] if self.warp else pts

    def _add(self, d):
        if d:
            self.paths.append(d)
        return d

    def stroke(self, pts, w=(0, 2.4, 0), amp=1.3, waves=1.8, step=2.4,
               per_seg=14, closed=False, cuts=None, jit=0.0):
        """Ein Federstrich. `cuts` = Liste von (von, bis) in 0..1 fuer
        abgesetzte, offene Konturen."""
        pts = list(pts)
        if jit:
            pts = [(x + self.rng.uniform(-jit, jit), y + self.rng.uniform(-jit, jit))
                   for x, y in pts]
        line = self._w(resample(catmull(pts, per_seg, closed), step))
        line = wobble(line, self.rng, amp, waves, hold_ends=not closed)
        if not cuts:
            return self._add(outline(line, w, self.rng))
        n = len(line) - 1
        for a, b in cuts:
            sl = line[int(a * n):int(b * n) + 1]
            if len(sl) < 2:
                continue
            # Breitenprofil des Gesamtstrichs auf das Teilstueck beziehen
            wa, wb = _profile(a, w), _profile(b, w)
            wm = _profile((a + b) / 2, w)
            self._add(outline(sl, (wa * 0.35, wm, wb * 0.35), self.rng))
        return None

    def blob(self, cx, cy, r, wobble_amt=0.42, n=9, spikes=0, spike_len=1.9):
        """Unregelmaessiger Tuscheklecks, optional mit auslaufenden Spitzen."""
        pts = []
        for i in range(n):
            a = TAU * i / n + self.rng.uniform(-0.12, 0.12)
            rr = r * (1 + self.rng.uniform(-wobble_amt, wobble_amt))
            if spikes and i % max(1, n // spikes) == 0:
                rr *= spike_len
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        ring = self._w(catmull(pts, 10, closed=True))
        return self._add("M" + f"{ring[0][0]:.1f},{ring[0][1]:.1f}"
                         + "".join(f"L{x:.1f},{y:.1f}" for x, y in ring[1:]) + "Z")

    def dot(self, cx, cy, r):
        return self.blob(cx, cy, r, wobble_amt=0.3, n=7)

    def patch(self, pts, wob=2.0):
        """Geschlossene Tuscheflaeche mit unruhigem Rand -- fuer Haarmassen,
        die anschliessend mit hairs() ausgefranst werden."""
        ring = wobble(self._w(catmull(pts, 12, closed=True)), self.rng, wob, 3.2,
                      hold_ends=False)
        return self._add("M" + f"{ring[0][0]:.1f},{ring[0][1]:.1f}"
                         + "".join(f"L{x:.1f},{y:.1f}" for x, y in ring[1:]) + "Z")

    def flaeche(self, pts, wob=1.4):
        """Geschlossene weisse Flaeche unter der Zeichnung.

        Der Rand darf leicht unruhig sein, er wird ohnehin von den
        Tuschestrichen ueberdeckt. Wichtig ist nur, dass er die Kontur
        aussen umschliesst."""
        ring = wobble(self._w(catmull(pts, 12, closed=True)), self.rng, wob, 2.6,
                      hold_ends=False)
        d = ("M" + f"{ring[0][0]:.1f},{ring[0][1]:.1f}"
             + "".join(f"L{x:.1f},{y:.1f}" for x, y in ring[1:]) + "Z")
        self.flaechen.append(d)
        return d

    def strands(self, innen, aussen, count, w=(1.6, 2.4, 0), off=1.7,
                kurz=0.22, spaet=0.10, amp=0.7):
        """Haarpartie als Buendel einzelner langer Zuege.

        Zwischen der inneren und der aeusseren Leitkurve werden `count`
        Straehnen interpoliert. Jede setzt etwas spaeter an und endet
        etwas frueher als die Nachbarn -- dadurch franst die Partie an
        beiden Enden aus, statt als geschlossene Kappe zu stehen."""
        # Beide Kurven auf dieselbe Punktzahl bringen: sie sollen einander
        # proportional entsprechen. Nach Index gepaart wuerde die laengere
        # bei der Laenge der kuerzeren abgeschnitten -- die Partie endete
        # dann auf einer Seite mitten im Bild.
        A0, B0 = catmull(innen, 14), catmull(aussen, 14)
        n = max(8, int(max(laenge(A0), laenge(B0)) / 3.0))
        A, B = resample_n(A0, n), resample_n(B0, n)
        if n < 4:
            return
        for i in range(count):
            t = (i + self.rng.uniform(-0.35, 0.35)) / max(1, count - 1)
            t = min(1.0, max(0.0, t))
            k0 = int(n * self.rng.uniform(0, spaet))
            k1 = int(n * (1.0 - self.rng.uniform(0, kurz)))
            if k1 - k0 < 3:
                continue
            schritt = max(1, (k1 - k0) // 12)
            pts = []
            for k in range(k0, k1, schritt):
                ax, ay = A[k]
                bx, by = B[k]
                pts.append((ax + (bx - ax) * t + self.rng.uniform(-off, off),
                            ay + (by - ay) * t + self.rng.uniform(-off, off)))
            if len(pts) >= 2:
                self.stroke(pts, w=(w[0] * self.rng.uniform(0.7, 1.3), w[1], w[2]),
                            amp=amp, waves=1.4, step=2.6)

    def curls(self, base, count, size, size_var=0.45, jitter=5.0,
              w=(2.6, 2.0, 0), turns=0.82):
        """Lockenkopf aus offenen Spiralzuegen statt aus vollen Kleckssen."""
        line = resample(catmull(base, 14), 2.0)
        n = len(line) - 1
        for i in range(count):
            t = (i + self.rng.uniform(0.1, 0.9)) / count
            x, y = line[min(n, int(t * n))]
            x += self.rng.uniform(-jitter, jitter)
            y += self.rng.uniform(-jitter, jitter)
            r = size * (1 + self.rng.uniform(-size_var, size_var))
            a0 = self.rng.uniform(0, TAU)
            drehung = self.rng.choice((1, -1))
            pts = []
            steps = 9
            for k in range(steps):
                a = a0 + drehung * turns * TAU * k / (steps - 1)
                rr = r * (1.0 - 0.42 * k / (steps - 1))
                pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
            self.stroke(pts, w=w, amp=0.4, waves=1.0, step=1.8)

    def hairs(self, base, count, length, w=(2.6, 1.6, 0), spread=0.32,
              curl=0.4, out_dir=1, jitter=0.35, length_var=0.55,
              angle=None, curl_bias=0.7, curl_var=0.45):
        """Buendel auslaufender Striche: dick am Ansatz, spitz am Ende.

        `base` sind Stuetzpunkte der Ansatzlinie. Ohne `angle` stehen die
        Striche quer dazu (out_dir=+1 in Normalenrichtung), mit `angle`
        laufen sie in diese feste Richtung -- Haar hat eine Strichrichtung,
        es strahlt nicht sternfoermig. `curl_bias` biegt alle Strähnen
        ueberwiegend zur gleichen Seite, wie gekaemmtes Haar."""
        line = resample(catmull(base, 14), 2.0)
        nrm = normals(line)
        n = len(line) - 1
        for i in range(count):
            t = (i + self.rng.uniform(0.05, 0.95)) / count
            k = min(n, int(t * n))
            p, nv = line[k], nrm[k]
            if angle is None:
                ang = math.atan2(nv[1] * out_dir, nv[0] * out_dir)
            else:
                ang = angle
            ang += self.rng.uniform(-spread, spread)
            ln = length * (1 + self.rng.uniform(-length_var, length_var))
            tip = (p[0] + math.cos(ang) * ln, p[1] + math.sin(ang) * ln)
            side = ang + math.pi / 2
            bend = ln * curl * (curl_bias + self.rng.uniform(-curl_var, curl_var))
            mid = ((p[0] + tip[0]) / 2 + math.cos(side) * bend,
                   (p[1] + tip[1]) / 2 + math.sin(side) * bend)
            root = (p[0] + self.rng.uniform(-jitter, jitter) * 3,
                    p[1] + self.rng.uniform(-jitter, jitter) * 3)
            ww = (w[0] * self.rng.uniform(0.7, 1.35), w[1], w[2])
            self.stroke([root, mid, tip], w=ww, amp=0.5, waves=1.2, step=2.0)

    def spatter(self, zones, rng_seed=None):
        """zones: Liste von (cx, cy, radius, anzahl).

        Spritzer liegen auf dem Papier, nicht auf dem Kopf -- eine
        eingestellte Drehung gilt fuer sie nicht.

        Mit `rng_seed` bekommen die Spritzer einen eigenen Zufallsstrom.
        Das ist noetig, sobald mehrere Fassungen desselben Bildes entstehen
        (Emotes, Blinzeln): sonst haengen sie davon ab, wie viel Zufall das
        Gesicht davor verbraucht hat, und wackeln beim Umschalten mit.
        Sie liegen aber auf dem Papier und duerfen sich nicht bewegen."""
        gemerkt, self.warp = self.warp, None
        gemerkte_rng = self.rng
        if rng_seed is not None:
            self.rng = random.Random(rng_seed)
        try:
            self._spatter(zones)
        finally:
            self.warp = gemerkt
            self.rng = gemerkte_rng

    def _spatter(self, zones):
        for cx, cy, rad, cnt in zones:
            for _ in range(cnt):
                a = self.rng.uniform(0, TAU)
                d = rad * math.sqrt(self.rng.uniform(0.05, 1.0))
                x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
                roll = self.rng.random()
                if roll < 0.55:
                    self.dot(x, y, self.rng.uniform(0.7, 1.7))
                elif roll < 0.85:
                    self.blob(x, y, self.rng.uniform(1.4, 3.0), 0.5, 8)
                else:
                    ln = self.rng.uniform(4, 11)
                    a2 = self.rng.uniform(0, TAU)
                    self.stroke([(x, y),
                                 (x + math.cos(a2) * ln, y + math.sin(a2) * ln)],
                                w=(2.2, 1.2, 0), amp=0.4, step=2.0)

    def hatch(self, x, y, count, length, angle, spacing, w=(0, 1.5, 0), fan=0.12):
        """Lockere, leicht divergierende Parallelstriche."""
        for i in range(count):
            a = angle + self.rng.uniform(-fan, fan)
            ox = x + math.cos(angle + math.pi / 2) * spacing * i
            oy = y + math.sin(angle + math.pi / 2) * spacing * i
            ln = length * self.rng.uniform(0.65, 1.25)
            self.stroke([(ox, oy), (ox + math.cos(a) * ln, oy + math.sin(a) * ln)],
                        w=w, amp=0.55, waves=1.1, step=2.2)

    def svg(self, w=400, h=520, title=None, grund=True):
        """SVG der Zeichnung.

        Mit `grund` liegt ein weisses Rechteck ueber die ganze Flaeche, wie
        bei den Portraitseiten. Ohne `grund` bleibt der Bildgrund
        durchsichtig, und nur die mit flaeche() gesetzten Silhouetten sind
        weiss. Das brauchen die Puppen: die Figur soll den Hintergrund
        verdecken, das Papier daneben nicht."""
        head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'
        if title:
            head += f"<title>{title}</title>"
        if grund:
            head += f'<rect width="{w}" height="{h}" fill="#fff"/>'
        flaechen = "".join(f'<path d="{d}"/>' for d in self.flaechen)
        body = "".join(f'<path d="{d}"/>' for d in self.paths)
        return (head
                + f'<g fill="#fff" fill-rule="nonzero">{flaechen}</g>'
                + f'<g fill="#111" fill-rule="nonzero">{body}</g></svg>\n')
