"""
USBCANFD DUAL (CANnectivity) enclosure for M3 screws and heat-set inserts, built from scratch in FreeCAD (OCC).

All parts are built from Part primitives, so the STEP/FCStd files contain real faces (planes, cylinders, cones),
not meshes.

Run (FreeCAD 1.x; with Flatpak the script path must be absolute):
    freecadcmd "$PWD/build_cannectivity_case.py"
    flatpak run --command=/app/bin/freecadcmd org.freecad.FreeCAD "$PWD/build_cannectivity_case.py"
Write the output to another folder (with Flatpak it must be visible to the sandbox, i.e. not /tmp):
    CANNECTIVITY_OUT=~/.cache/cannectivity-try freecadcmd "$PWD/build_cannectivity_case.py"

Outputs (next to the script or in CANNECTIVITY_OUT), all prefixed with PREFIX = USBCANFD_DUAL_M3_NUT_
("M3_NUT": the M3 screw + heat-set insert variant, as opposed to the original snap-fit box):
    …_Bottom.{stl,step}            bottom part
    …_Top.step                     lid as one solid (for CAD)
    …_Top_{body,inlay}_print.stl   two-colour lid, roof down on the bed (red body + white inlay)
    …_Button.{stl,step}            reset button plunger, cap down on the bed
    …_JumperHolder.{stl,step}      termination jumper holder, rim down on the bed
    …_Assembly.step, USBCANFD_DUAL_M3_NUT.FCStd (with GuiDocument.xml)   assembly

Coordinate system: the same as the PCB DXF in the original USBCANFD_DUAL_SOLO.FCStd
(3DBox_for_adaptersSOLO_DUAL.zip): X is the length (USB at −X, CAN terminals at +X), Y the width,
Z the height; the bottom of the enclosure is at Z = 0.
"""
import os
import zipfile

import FreeCAD as App
import Part
import MeshPart

V = App.Vector
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser(os.environ.get("CANNECTIVITY_OUT", HERE))
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/dejavu/DejaVuSans.ttf"   # path inside Flatpak FreeCAD; adjust for your system

# --- PCB (author's DXF) ---------------------------------------------------------
PCB_X0, PCB_X1 = -28.0671, 33.6551      # 61.72 mm
PCB_Y0, PCB_Y1 = -17.2720, 13.2081      # 30.48 mm
PCB_T = 1.6
# PCB-to-wall clearance per side, tuned by test prints:
#   X (long side) 0.3; 0.6 was too loose;
#   Y (short side) 0.1.
PCB_CLEAR_X = 0.3
PCB_CLEAR_Y = 0.1

# --- Heights ------------------------------------------------------------------
FLOOR = 1.0             # floor thickness (as in the original)
LEDGE_Z = 3.5           # PCB ledge: 2.5 mm below the PCB for THT leads
PCB_TOP = LEDGE_Z + PCB_T   # 5.1
Z_SPLIT = 11.0          # parting plane between bottom and lid
ROOF_Z0, ROOF_Z1 = 18.0, 19.0

# Outline of the ledge under the PCB, taken from the author's original bottom part (section at Z 2.5 inside the PCB
# outline). The gaps along the edges are for component leads.
LEDGE_POLY = [
    (33.66, 13.21), (-28.07, 13.21), (-28.07, -17.27), (-4.44, -17.27), (-4.44, -15.65),
    (-26.68, -15.65), (-26.68, 4.23), (-26.07, 4.23), (-26.07, 11.75), (-0.59, 11.75),
    (-0.59, 13.21), (7.69, 13.21), (7.69, 11.75), (32.64, 11.75), (32.64, -15.65),
    (25.92, -15.65), (25.92, -17.27), (33.66, -17.27),
]
LEDGE_PADS = [(0.95, 4.78, -17.27, -15.65), (16.95, 20.84, -17.27, -15.65)]

# --- Outline and screws ----------------------------------------------------------
END_WALL_USB = 1.6      # USB end wall: the plug (DXF to X −42.85) sticks out ~12.9 mm
CAN_FACE_X = 38.10      # CAN end flush with the front of the terminal block housings (DXF silkscreen)
R_CORNER = 4.0          # corner radius; corners are concentric with the screws
DY_SCREW = 3.5          # screw axis distance from the PCB edge in Y (screws sit in the side walls)
X_MIN = PCB_X0 - PCB_CLEAR_X - END_WALL_USB          # −29.97
X_MAX = CAN_FACE_X                                   #  38.10
SCREW_X = (X_MIN + R_CORNER, X_MAX - R_CORNER)
SCREW_Y = (PCB_Y0 - DY_SCREW, PCB_Y1 + DY_SCREW)
SCREWS = [(x, y) for x in SCREW_X for y in SCREW_Y]
Y_MIN = SCREW_Y[0] - R_CORNER
Y_MAX = SCREW_Y[1] + R_CORNER

# Heat-set insert M3×5×4 (knurl Ø4.0, length 5). Pocket Ø3.6 with a Ø4.0 × 0.6 lead-in, 6 mm deep:
# tuned by a test print with slicer XY hole compensation 0.
INSERT_HOLE_D, INSERT_LEAD_D, INSERT_LEAD_H, INSERT_DEPTH = 3.6, 4.0, 0.6, 6.0
SCREW_TIP_D, SCREW_TIP_Z = 3.2, 1.5     # clearance hole below the insert for the screw tip
# Countersunk screw DIN 7991 M3×14
SCREW_THRU_D, SCREW_HEAD_D = 3.4, 6.5

# --- Connectors -------------------------------------------------------------------
# USB cut-out 12.0 wide, as in the author's original. Above it the lid has a tongue down to USB_Z[1],
# so the plug is clamped between the sill and the tongue.
USB_Y = (-8.92, 3.08)   # exactly 12.0 (12.2 and 12.5 were too wide)
USB_Z = (4.0, 8.5)      # sill 4.0 supports the plug from below; tongue from the parting plane down to 8.5
USB_TONGUE_CLEAR = 0.0  # tongue as wide as the cut-out
CAN_Y = (-14.37 - 0.1, 10.43 + 0.1)    # terminal block housings (DXF silkscreen 24.8) + 0.1: cut-out 25.0
CAN_Z = (4.9, 12.7)                   # terminals from the PCB top; 1.7 mm cut-out in the lid (Z 11…12.7)
CAN_X0 = 33.6                         # the cut-out starts above the PCB edge

# --- LEDs, button, jumpers (DXF) -------------------------------------------------
LED_X = (-19.95, -17.55, -15.10, -12.70)
LED_Y = 10.10
LED_LABELS = ("RX1", "TX1", "RX2", "TX2")
LED_WIN_W, LED_WIN_H, LED_WALL, LED_MEMBRANE = 1.6, 3.0, 1.2, 0.4   # light pipe window, wall, membrane
LED_TUBE_Z0 = 6.8                       # bottom of the light pipe block
CRYSTAL_X_MIN, CRYSTAL_CLEAR_Z = -11.4, 10.0   # the light pipe block is cut back above the crystal

# Reset button: a well in the roof with a shelf, a guide shaft, and a separate plunger whose cap sits recessed
# in the well; a split barb below the shaft keeps the plunger captive (same idea as the JK_BMS_Monitor case).
BTN_X, BTN_Y = -25.20, 8.50
BTN_WELL_D, BTN_FUNNEL_D, BTN_WELL_DEPTH = 5.5, 6.5, 4.0   # well, 0.5 chamfer at the roof, depth to the shelf
BTN_BORE_D = 3.4            # guide shaft
BTN_BLOCK_WALL = 1.2        # wall of the shaft block around the well
PL_CAP_D, PL_CAP_H = 4.8, 1.0      # plunger cap (rests on the shelf when pressed)
PL_STEM_D, PL_BARB_D = 3.1, 4.0    # stem and barb diameters
PL_SLIT_W = 0.8                    # slit through the barb (makes it springy)
PL_SLIT_TOP = 1.0                  # solid stem length under the cap, above the slit
BTN_SHELF_Z = ROOF_Z1 - BTN_WELL_DEPTH                     # 15.0
# Solid guide shaft Ø3.4 from the shelf down to 1 mm above the parting plane (the 1 mm is extra plunger travel).
BTN_CHIMNEY_Z0 = Z_SPLIT + 1.0                             # 12.0, bottom of the shaft block
PL_GUIDE = BTN_SHELF_Z - BTN_CHIMNEY_Z0                    # 3.0, guide length
PL_TIP_Z = 7.7              # plunger tip Z with the cap on the shelf, i.e. button pressed (found by test prints)
PL_STEM_LEN = 5.5           # stem from the cap to the barb shoulder
PL_BARB_GAP = PL_STEM_LEN - PL_GUIDE                       # 2.5, upward travel until the barb hits the shaft
PL_TIP_LEN = BTN_SHELF_Z - PL_STEM_LEN - 0.2 - 0.9 - 0.3 - PL_TIP_Z   # 0.4, keeps the tip at PL_TIP_Z

# Termination jumper windows. CAN2 is moved from its DXF position (22.70, −10.05) to match the real board.
JUMPERS = ((22.95, 1.95), (22.70 - 1.0, -10.05 + 1.5 - 0.5))
JMP_WIN_X, JMP_WIN_Y, JMP_WIN_R = 9.0, 6.0, 1.0
JMP_COLLAR_W, JMP_COLLAR_Z0 = 1.2, 15.0          # collar around each window under the roof
JMP_NOTCH = (1.2, 3.0, 0.8)                       # optional fingernail notch next to each window (length, width, depth)
JMP_NOTCH_ON = False                              # not needed: the jumper holders have a rim above the roof
PLUG_CLEAR, PLUG_WALL, PLUG_Z0 = 0.08, 1.0, 15.2  # window plug: clearance per side, skirt wall, skirt bottom
PLUG_RIB_H, PLUG_RIB_W = 0.15, 0.6                # interference ribs on the plug skirt
# Jumper holder: a window plug with a sleeve that grips a standard 2.54 mm jumper cap (5.0 × 2.5 × 6.0, closed top,
# long side along X). Pulling the holder out pulls the jumper off the pins.
JCAP_L, JCAP_W, JCAP_H = 5.0, 2.5, 6.0
JCAP_TOP_Z = 5.1 + 2.5 + JCAP_H        # 13.6, top of a seated jumper cap
JH_POCKET_CLEAR = 0.1                  # pocket larger than the cap per side along X
JH_POCKET_CLEAR_W = 0.2                # same across the width, where the ribs grip
JH_CEIL_GAP = 0.2                      # pocket ceiling above the cap top
JH_GRIP = 3.0                          # how far the sleeve goes down over the cap
JH_WALL = 0.9                          # sleeve wall
JH_RIB_W = 0.6                         # Ø0.6 grip ribs on the long walls, 2 per side
JH_INTERF = 0.20                       # rib interference per side on the cap width (0.0 and 0.1 were too loose)
JH_NECK = 1.0                          # neck height above the roof, under the rim (fingernail gap)
JH_LIP_H, JH_LIP_O = 1.0, 0.7          # rim thickness and overhang beyond the plug outline per side

# --- Labels -------------------------------------------------------------------------
TEXT_DEPTH = 0.6         # 3 layers, so the white inlay does not show red through
TEXT_BOLD = 0.14         # outline offset per side: DejaVu Sans strokes ~0.21 -> ~0.49 mm, otherwise the slicer
                         # drops thin strokes on the first layer (0.5 mm line width)
# Cap heights, mm
CAP_LED = 1.70
LED_LABEL_PITCH = 3.0    # LED labels are fanned out at this pitch (LED pitch 2.4 made them merge in print)
CAP_RST = 3.00           # "R" under the button
CAP_120 = 2.60           # "120Ω" between the jumper windows, right edge at X_120_RIGHT
CAP_CAN = 2.30           # terminal pinout; limited by the 3.8 mm line pitch ("_" hangs 0.32·cap below)
X_120_RIGHT = 26.9
# Device name in the free area of the roof. Its left edge is aligned with "R" and its baseline with "2_L"
# (computed in build_lid).
DEVICE_NAME = "USBCANFD"
CAP_NAME = 5.0
CAN_PINS = (("1_H", 8.10), ("GND", 4.30), ("1_L", 0.50),
            ("2_H", -4.50), ("GND", -8.30), ("2_L", -12.10))
CAN_TEXT_X = (27.9, 37.7)   # from the jumper windows (27.45) to the end face (38.1)

# --- Two-colour lid (red body + white inlay) -----------------------------------------
# The inlay fills the label recesses (TEXT_DEPTH = the first 3 layers when printed roof down).
# MEMBRANE_INLAY: the LED membranes are also part of the white inlay. They are in the same layers, so there are no
# extra filament changes, and a red membrane would block too much light.
MEMBRANE_INLAY = True


# =============================================================================
def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(d, x, y, z0, z1):
    return Part.makeCylinder(d / 2.0, z1 - z0, V(x, y, z0))


def rrect(w, h, r, cx, cy, z0, z1):
    """Rectangle w×h with corner radius r, centred at (cx, cy), extruded from z0 to z1."""
    r = min(r, w / 2 - 1e-3, h / 2 - 1e-3)
    if r <= 0:
        return box(cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2, z0, z1)
    core = Part.makePlane(w - 2 * r, h - 2 * r, V(cx - w / 2 + r, cy - h / 2 + r, z0))
    face = core.makeOffset2D(r, 0)   # join=0: arcs at the corners
    return face.extrude(V(0, 0, z1 - z0))


def outer_body(z0, z1):
    w = SCREW_X[1] - SCREW_X[0] + 2 * R_CORNER
    h = SCREW_Y[1] - SCREW_Y[0] + 2 * R_CORNER
    return rrect(w, h, R_CORNER, (X_MIN + X_MAX) / 2, (Y_MIN + Y_MAX) / 2, z0, z1)


def poly_prism(pts, z0, z1):
    wire = Part.makePolygon([V(x, y, z0) for x, y in pts] + [V(pts[0][0], pts[0][1], z0)])
    return Part.Face(wire).extrude(V(0, 0, z1 - z0))


def fuse_all(shapes):
    s = shapes[0]
    if len(shapes) > 1:
        s = s.fuse(shapes[1:])
    return s.removeSplitter()


_cap_cache = {}


def text_solid(text, cap, z0, z1, anchor, align="center", rotate90=False, max_width=None, font=FONT):
    """Text solid with capital letters `cap` high. `anchor` is the middle of the line (align='center'),
    its left or right end at mid cap height (align='left'/'right'), or the glyphs' centre of mass (align='mass').
    rotate90: the text reads bottom to top."""
    if font not in _cap_cache:
        hb = Part.Compound([w for c in Part.makeWireString("H", font, 10.0, 0) for w in c]).BoundBox
        _cap_cache[font] = hb.YLength / 10.0
    size = cap / _cap_cache[font]
    chars = Part.makeWireString(text, font, size, 0)
    faces = []
    for wires in chars:
        if wires:
            # Glyph curves (B-splines) -> polylines with 5 µm deflection: OCC fuses offset B-splines
            # unreliably (invalid solids), polylines work fine.
            poly = []
            for w in wires:
                pts = w.discretize(Deflection=0.005)
                if (pts[0] - pts[-1]).Length > 1e-7:
                    pts.append(pts[0])
                poly.append(Part.makePolygon(pts))
            faces.append(Part.makeFace(poly, "Part::FaceMakerBullseye"))
    shape = Part.Compound(faces)
    bb = shape.BoundBox
    scale = 1.0
    if max_width and bb.XLength + 2 * TEXT_BOLD > max_width:
        scale = (max_width - 2 * TEXT_BOLD) / bb.XLength
        shape = shape.scaled(scale, V(bb.XMin, 0, 0))   # scale from the left edge
        bb = shape.BoundBox
    if TEXT_BOLD > 0:
        # Thicken every glyph (arcs at the corners); overlaps between glyphs are merged by the fuse below
        shape = Part.Compound([f.makeOffset2D(TEXT_BOLD, 0) for f in shape.Faces])
    capz = cap * scale
    if align == "mass":   # glyphs' centre of mass (optical centre, e.g. "R" under the button)
        dx = -sum(f.Area * f.CenterOfMass.x for f in shape.Faces) / sum(f.Area for f in shape.Faces)
    else:
        dx = -bb.XMin - {"center": bb.XLength / 2, "left": 0.0, "right": bb.XLength + TEXT_BOLD}[align]
    shape.translate(V(dx, -capz / 2, 0))
    if rotate90:
        shape.rotate(V(0, 0, 0), V(0, 0, 1), 90)
    shape.translate(V(anchor[0], anchor[1], z0))
    solids = [f.extrude(V(0, 0, z1 - z0)) for f in shape.Faces]
    # After thickening, neighbouring outlines (glyphs, parts of a glyph) overlap: merge them
    out = solids[0].fuse(solids[1:]).removeSplitter() if len(solids) > 1 else solids[0]
    if not out.isValid():
        out.fix(1e-4, 1e-4, 1e-4)
    return out


# =============================================================================
def build_bottom():
    body = outer_body(0.0, Z_SPLIT)
    pocket = box(PCB_X0 - PCB_CLEAR_X, PCB_X1 + PCB_CLEAR_X, PCB_Y0 - PCB_CLEAR_Y, PCB_Y1 + PCB_CLEAR_Y,
                 FLOOR, Z_SPLIT + 1)
    body = body.cut(pocket)
    # Ledge: clearance band around the PCB + outline from the original + 2 pads
    band = box(PCB_X0 - PCB_CLEAR_X, PCB_X1 + PCB_CLEAR_X, PCB_Y0 - PCB_CLEAR_Y, PCB_Y1 + PCB_CLEAR_Y,
               FLOOR - 0.01, LEDGE_Z).cut(box(PCB_X0, PCB_X1, PCB_Y0, PCB_Y1, FLOOR - 1, LEDGE_Z + 1))
    ledge = [band, poly_prism(LEDGE_POLY, FLOOR - 0.01, LEDGE_Z)]
    ledge += [box(x0, x1, y0, y1, FLOOR - 0.01, LEDGE_Z) for x0, x1, y0, y1 in LEDGE_PADS]
    body = body.fuse(ledge)
    # Connector cut-outs
    body = body.cut(box(X_MIN - 1, PCB_X0 + 0.5, USB_Y[0], USB_Y[1], USB_Z[0], Z_SPLIT + 1))
    body = body.cut(box(CAN_X0, X_MAX + 1, CAN_Y[0], CAN_Y[1], CAN_Z[0], Z_SPLIT + 1))
    # Heat-set insert pockets (vertical axis, inserted from the top)
    holes = []
    for sx, sy in SCREWS:
        holes.append(cyl(INSERT_HOLE_D, sx, sy, Z_SPLIT - INSERT_DEPTH, Z_SPLIT + 1))
        holes.append(cyl(INSERT_LEAD_D, sx, sy, Z_SPLIT - INSERT_LEAD_H, Z_SPLIT + 1))
        holes.append(cyl(SCREW_TIP_D, sx, sy, SCREW_TIP_Z, Z_SPLIT - INSERT_DEPTH + 0.01))
    body = body.cut(holes)
    return body.removeSplitter()


def build_lid(two_color=False):
    """Lid. two_color=False: single colour (recessed labels, membranes made of the lid material).
    two_color=True: returns (body, inlay); the inlay fills the labels (and the membranes)."""
    body = outer_body(Z_SPLIT, ROOF_Z1)
    cavity = box(PCB_X0 - PCB_CLEAR_X, PCB_X1 + PCB_CLEAR_X, PCB_Y0 - PCB_CLEAR_Y, PCB_Y1 + PCB_CLEAR_Y,
                 Z_SPLIT - 1, ROOF_Z0)
    body = body.cut(cavity)
    # Tongue over the USB cut-out in the end wall: closes the bottom's cut-out from Z_SPLIT down to USB_Z[1]
    body = body.fuse(box(X_MIN, PCB_X0 - PCB_CLEAR_X, USB_Y[0] + USB_TONGUE_CLEAR,
                         USB_Y[1] - USB_TONGUE_CLEAR, USB_Z[1], Z_SPLIT + 0.01))
    # Cut-out over the terminal blocks (they are taller than the parting plane)
    body = body.cut(box(CAN_X0, X_MAX + 1, CAN_Y[0], CAN_Y[1], Z_SPLIT - 1, CAN_Z[1]))

    adds = []
    # Light pipes: a block of tubes from the roof down to LED_TUBE_Z0
    tx0 = min(LED_X) - LED_WIN_W / 2 - LED_WALL
    tx1 = max(LED_X) + LED_WIN_W / 2 + LED_WALL
    ty0 = LED_Y - LED_WIN_H / 2 - LED_WALL
    ty1 = LED_Y + LED_WIN_H / 2 + LED_WALL
    # The block reaches the lid side wall. Below the parting plane it keeps 0.15 clearance to the bottom's wall
    # so the lid seats without friction; above it overlaps the lid wall.
    wall_y = PCB_Y1 + PCB_CLEAR_Y
    tubes = box(tx0, tx1, ty0, wall_y - 0.15, LED_TUBE_Z0, ROOF_Z0 + 0.01).fuse(
        box(tx0, tx1, ty0, wall_y + 0.01, Z_SPLIT, ROOF_Z0 + 0.01))
    tubes = tubes.cut(box(CRYSTAL_X_MIN, tx1 + 1, ty0 - 1, ty1 + 1, LED_TUBE_Z0 - 1, CRYSTAL_CLEAR_Z))
    adds.append(tubes)
    # Button shaft block: from the lid's side wall (−X) and back wall (+Y) to the light pipe block
    cav_x0 = PCB_X0 - PCB_CLEAR_X
    adds.append(box(cav_x0 - 0.01, BTN_X + BTN_WELL_D / 2 + BTN_BLOCK_WALL,
                    BTN_Y - BTN_WELL_D / 2 - BTN_BLOCK_WALL, PCB_Y1 + PCB_CLEAR_Y + 0.01,
                    BTN_CHIMNEY_Z0, ROOF_Z0 + 0.01))
    # Collars around the jumper windows
    for jx, jy in JUMPERS:
        adds.append(rrect(JMP_WIN_X + 2 * JMP_COLLAR_W, JMP_WIN_Y + 2 * JMP_COLLAR_W,
                          JMP_WIN_R + JMP_COLLAR_W, jx, jy, JMP_COLLAR_Z0, ROOF_Z0 + 0.01))
    # The two collars are joined into one block (no gap between them)
    (ux, uy), (lx_, ly) = sorted(JUMPERS, key=lambda j: -j[1])
    cx = JMP_WIN_X / 2 + JMP_COLLAR_W
    cy = JMP_WIN_Y / 2 + JMP_COLLAR_W
    rc = JMP_WIN_R + JMP_COLLAR_W   # reaches into the collar corner fillets so no notches are left
    adds.append(box(max(ux, lx_) - cx, min(ux, lx_) + cx, ly + cy - rc, uy - cy + rc,
                    JMP_COLLAR_Z0, ROOF_Z0 + 0.01))
    body = body.fuse(adds)
    # The lower window (CAN2) has no −Y collar wall: there is a capacitor on the PCB.
    # Cut back to the straight part of the side walls (including the corner fillets); the roof is not touched.
    body = body.cut(box(lx_ - cx - 0.1, lx_ + cx + 0.1, ly - cy - 0.1, ly - JMP_WIN_Y / 2 + JMP_WIN_R,
                        JMP_COLLAR_Z0 - 1, ROOF_Z0))

    cuts = []
    membrane_inlay = two_color and MEMBRANE_INLAY
    membranes = []
    for lx in LED_X:   # light pipe windows up to the membrane (or through, if the membrane is part of the inlay)
        x0, x1 = lx - LED_WIN_W / 2, lx + LED_WIN_W / 2
        y0, y1 = LED_Y - LED_WIN_H / 2, LED_Y + LED_WIN_H / 2
        cuts.append(box(x0, x1, y0, y1, LED_TUBE_Z0 - 1,
                        ROOF_Z1 + 1 if membrane_inlay else ROOF_Z1 - LED_MEMBRANE))
        membranes.append(box(x0, x1, y0, y1, ROOF_Z1 - LED_MEMBRANE, ROOF_Z1))
    # Button: shaft Ø3.4, well Ø5.5 down to the shelf, chamfer to Ø6.5 at the roof
    cuts.append(cyl(BTN_BORE_D, BTN_X, BTN_Y, BTN_CHIMNEY_Z0 - 1, BTN_SHELF_Z + 0.01))
    cuts.append(cyl(BTN_WELL_D, BTN_X, BTN_Y, BTN_SHELF_Z, ROOF_Z1 + 1))
    cuts.append(Part.makeCone(BTN_WELL_D / 2, BTN_FUNNEL_D / 2 + 0.01, 0.51, V(BTN_X, BTN_Y, ROOF_Z1 - 0.5)))
    nx, nw, nd = JMP_NOTCH
    for jx, jy in JUMPERS:
        cuts.append(rrect(JMP_WIN_X, JMP_WIN_Y, JMP_WIN_R, jx, jy, JMP_COLLAR_Z0 - 1, ROOF_Z1 + 1))
        if JMP_NOTCH_ON:
            cuts.append(box(jx - JMP_WIN_X / 2 - nx, jx - JMP_WIN_X / 2 + 0.5, jy - nw / 2, jy + nw / 2,
                            ROOF_Z1 - nd, ROOF_Z1 + 1))
    for sx, sy in SCREWS:   # DIN 7991: Ø3.4 + 90° countersink to Ø6.5 at the roof
        cuts.append(cyl(SCREW_THRU_D, sx, sy, Z_SPLIT - 1, ROOF_Z1 + 1))
        h = (SCREW_HEAD_D - SCREW_THRU_D) / 2
        cuts.append(Part.makeCone(SCREW_THRU_D / 2, SCREW_HEAD_D / 2, h, V(sx, sy, ROOF_Z1 - h)))
        cuts.append(cyl(SCREW_HEAD_D, sx, sy, ROOF_Z1, ROOF_Z1 + 1))
    # Labels
    tz0, tz1 = ROOF_Z1 - TEXT_DEPTH, ROOF_Z1 + 0.5
    texts = []
    led_mid = (LED_X[0] + LED_X[-1]) / 2
    for i, name in enumerate(LED_LABELS):
        lx = led_mid + (i - (len(LED_LABELS) - 1) / 2) * LED_LABEL_PITCH
        texts.append(text_solid(name, CAP_LED, tz0, tz1, (lx, ty1 + 0.4), align="left", rotate90=True))
    # "R" (reset): top of the letter ~0.6 mm below the well chamfer
    rst_y = BTN_Y - BTN_FUNNEL_D / 2 - 0.6 - TEXT_BOLD - CAP_RST / 2
    r_solid = text_solid("R", CAP_RST, tz0, tz1, (BTN_X, rst_y), align="mass")
    texts.append(r_solid)
    jx_mid = (JUMPERS[0][0] + JUMPERS[1][0]) / 2
    jy_mid = (JUMPERS[0][1] + JUMPERS[1][1]) / 2
    texts.append(text_solid("120Ω", CAP_120, tz0, tz1, (X_120_RIGHT, jy_mid), align="right"))
    # Device name: left edge aligned with "R", baseline with "2_L" (both have the same TEXT_BOLD offset)
    r_x0 = r_solid.BoundBox.XMin + TEXT_BOLD        # left edge of the "R" glyph without the offset
    base_2l = dict((n, y) for n, y in CAN_PINS[3:])["2_L"] - CAP_CAN / 2   # "2_L" is not scaled (narrower than the field)
    texts.append(text_solid(DEVICE_NAME, CAP_NAME, tz0, tz1, (r_x0, base_2l + CAP_NAME / 2), align="left"))
    for name, py in CAN_PINS:
        # all lines centred on one axis (middle of CAN_TEXT_X)
        texts.append(text_solid(name, CAP_CAN, tz0, tz1, (sum(CAN_TEXT_X) / 2, py), align="center",
                                max_width=CAN_TEXT_X[1] - CAN_TEXT_X[0]))
    body = body.cut(cuts + texts).removeSplitter()
    if not two_color:
        return body
    # Inlay: exactly the volume of the label recesses in the roof (+ membranes)
    slab = outer_body(tz0, ROOF_Z1)
    inlay = [slab.common(t) for t in texts]
    if membrane_inlay:
        inlay += membranes
    inlay = fuse_all(inlay)
    return body, inlay


def build_plug():
    """Jumper window plug, centred at (0, 0), in lid coordinates (roof top at Z 19)."""
    w, h = JMP_WIN_X - 2 * PLUG_CLEAR, JMP_WIN_Y - 2 * PLUG_CLEAR
    r = JMP_WIN_R - PLUG_CLEAR
    top = rrect(w, h, r, 0, 0, ROOF_Z0, ROOF_Z1)
    skirt = rrect(w, h, r, 0, 0, PLUG_Z0, ROOF_Z0 + 0.01).cut(
        rrect(w - 2 * PLUG_WALL, h - 2 * PLUG_WALL, max(r - PLUG_WALL, 0.2), 0, 0, PLUG_Z0 - 1, ROOF_Z0))
    parts = [top, skirt]
    rib_z0 = PLUG_Z0 + 0.2
    rib_z1 = ROOF_Z0 - 0.6
    for sx in (-w / 4, w / 4):
        for sgn in (-1, 1):
            parts.append(cyl(PLUG_RIB_W, sx, sgn * (h / 2 - PLUG_RIB_W / 2 + PLUG_RIB_H), rib_z0, rib_z1))
    # One more rib on each ±X side: the lower window has no −Y collar wall
    for sgn in (-1, 1):
        parts.append(cyl(PLUG_RIB_W, sgn * (w / 2 - PLUG_RIB_W / 2 + PLUG_RIB_H), 0, rib_z0, rib_z1))
    return fuse_all(parts)


def build_jumper_holder(interf=JH_INTERF, neck=None):
    """Window plug with a sleeve that holds the jumper cap. Centred at (0, 0), lid coordinates.
    interf: rib interference per side relative to the cap width JCAP_W.
    neck: neck height above the roof with a JH_LIP_H rim on top overhanging by JH_LIP_O (None: flush with the roof)."""
    ceil_z = JCAP_TOP_Z + JH_CEIL_GAP                    # 13.8
    z0 = ceil_z - JH_GRIP                                 # 10.8, bottom of the sleeve
    pl, pw = JCAP_L + 2 * JH_POCKET_CLEAR, JCAP_W + 2 * JH_POCKET_CLEAR_W   # 5.2 × 2.9
    sl, sw = pl + 2 * JH_WALL, pw + 2 * JH_WALL           # 7.0 × 4.7
    body = build_plug().fuse(rrect(sl, sw, 0.5, 0, 0, z0, ROOF_Z0 + 0.5))
    body = body.cut(box(-pl / 2, pl / 2, -pw / 2, pw / 2, z0 - 1, ceil_z))
    # 0.5 lead-in chamfer at the pocket entry
    w0 = Part.makePolygon([V(x, y, z0 - 0.01) for x, y in ((-pl/2-0.5, -pw/2-0.5), (pl/2+0.5, -pw/2-0.5),
                                                          (pl/2+0.5, pw/2+0.5), (-pl/2-0.5, pw/2+0.5), (-pl/2-0.5, -pw/2-0.5))])
    w1 = Part.makePolygon([V(x, y, z0 + 0.5) for x, y in ((-pl/2, -pw/2), (pl/2, -pw/2),
                                                         (pl/2, pw/2), (-pl/2, pw/2), (-pl/2, -pw/2))])
    body = body.cut(Part.makeLoft([w0, w1], True))
    # ribs: crest at JCAP_W/2 − interf from the axis
    yc = JCAP_W / 2 - interf + JH_RIB_W / 2
    ribs = [cyl(JH_RIB_W, sx, sg * yc, z0 + 0.6, ceil_z + 0.01) for sx in (-1.4, 1.4) for sg in (-1, 1)]
    ribs = [r.common(box(-pl / 2 - 0.1, pl / 2 + 0.1, -pw / 2 - 0.1, pw / 2 + 0.1, z0, ceil_z + 0.02)) for r in ribs]
    if neck:
        w, h = JMP_WIN_X - 2 * PLUG_CLEAR, JMP_WIN_Y - 2 * PLUG_CLEAR
        r = JMP_WIN_R - PLUG_CLEAR
        o = JH_LIP_O
        ribs.append(rrect(w, h, r, 0, 0, ROOF_Z1 - 0.01, ROOF_Z1 + neck + 0.01))
        ribs.append(rrect(w + 2 * o, h + 2 * o, r + o, 0, 0, ROOF_Z1 + neck, ROOF_Z1 + neck + JH_LIP_H))
    return body.fuse(ribs).removeSplitter()


def build_plunger(stem=None):
    """Button plunger in assembly coordinates (axis X=Y=0), pressed state: cap resting on the shelf.
    Top to bottom: cap Ø4.8 × 1.0 (0.3 chamfer to Ø4.0 on top), stem Ø3.1, barb (shoulder out to Ø4.0 over 0.2,
    cone back to Ø3.1 over 0.9), tip Ø3.1 (PL_TIP_LEN cylinder) with a 0.3 chamfer to Ø2.0.
    The 0.8 slit goes through the barb only; the tip end and the cap are solid.
    stem: stem length from the cap to the barb shoulder, mm (default PL_STEM_LEN). The tip has a fixed length,
    so a longer stem moves the barb and the tip down together."""
    if stem is None:
        stem = PL_STEM_LEN
    assert stem >= PL_GUIDE + 0.2, f"stem {stem} is shorter than the guide shaft {PL_GUIDE}: the barb cannot clear it"
    z_cap_top = BTN_SHELF_Z + PL_CAP_H              # 16.0
    z_barb = BTN_SHELF_Z - stem                     # barb shoulder
    tip_z = z_barb - 0.2 - 0.9 - PL_TIP_LEN - 0.3   # tip end
    parts = [
        Part.makeCone(PL_CAP_D / 2, 4.0 / 2, 0.3, V(0, 0, z_cap_top - 0.3)),    # chamfer on top of the cap
        cyl(PL_CAP_D, 0, 0, BTN_SHELF_Z, z_cap_top - 0.3 + 0.01),
        cyl(PL_STEM_D, 0, 0, z_barb - 0.01, BTN_SHELF_Z + 0.01),
        Part.makeCone(PL_BARB_D / 2, PL_STEM_D / 2, 0.2, V(0, 0, z_barb - 0.2)),   # shoulder (facing up)
        Part.makeCone(PL_STEM_D / 2, PL_BARB_D / 2, 0.9, V(0, 0, z_barb - 1.1)),   # lead-in cone
        cyl(PL_STEM_D, 0, 0, tip_z + 0.3 - 0.01, z_barb - 1.1 + 0.01),
        Part.makeCone(2.0 / 2, PL_STEM_D / 2, 0.3, V(0, 0, tip_z)),
    ]
    pl = fuse_all(parts)
    # The slit runs up to PL_SLIT_TOP below the cap (longer fingers, easier to insert) and stops 0.8 mm above
    # the tip end, so the tip end stays solid.
    slit_z1 = max(z_barb + 1.2, BTN_SHELF_Z - PL_SLIT_TOP)
    slit = box(-PL_SLIT_W / 2, PL_SLIT_W / 2, -3, 3, max(z_barb - 1.8, tip_z + 0.8), slit_z1)
    return pl.cut(slit).removeSplitter()


# =============================================================================
def check(name, s):
    sol = s.Solids
    print(f"  {name}: solids={len(sol)}, isValid={s.isValid()}, faces={len(s.Faces)}, "
          f"volume={s.Volume:.1f} mm³, bounds "
          f"X[{s.BoundBox.XMin:.2f}, {s.BoundBox.XMax:.2f}] Y[{s.BoundBox.YMin:.2f}, {s.BoundBox.YMax:.2f}] "
          f"Z[{s.BoundBox.ZMin:.2f}, {s.BoundBox.ZMax:.2f}]")
    assert len(sol) == 1 and s.isValid(), f"{name}: invalid solid"
    return sol[0]


def write_stl(shape, path):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.01, AngularDeflection=0.1, Relative=False)
    m.write(path)
    return m


def ensure_fcstd_gui_visibility(path, obj_names):
    """freecadcmd does not write GuiDocument.xml; without it the GUI opens all bodies hidden."""
    xml = ("<?xml version='1.0' encoding='utf-8'?>\n<Document SchemaVersion='1' HasExpansion='1'>\n"
           f"    <Expand />\n    <ViewProviderData Count='{len(obj_names)}'>\n")
    for n in obj_names:
        xml += (f"        <ViewProvider name='{n}' expanded='0'>\n            <Properties Count='1'>\n"
                "                <Property name='Visibility' type='App::PropertyBool' status='1'>\n"
                "                    <Bool value='true'/>\n                </Property>\n"
                "            </Properties>\n        </ViewProvider>\n")
    xml += "    </ViewProviderData>\n</Document>\n"
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            if it.filename != "GuiDocument.xml":
                zout.writestr(it, zin.read(it.filename))
        zout.writestr("GuiDocument.xml", xml)
    os.replace(tmp, path)


# File name prefix: "M3_NUT" marks the M3 screw + heat-set insert variant, as opposed to the original snap-fit box
PREFIX = "USBCANFD_DUAL_M3_NUT_"


def main():
    print("=== USBCANFD DUAL M3_NUT enclosure (FreeCAD/OCC) ===")
    bottom = check("Bottom", build_bottom())
    lid = check("Lid", build_lid())
    check("Window plug", build_plug())
    plunger = build_plunger()
    plunger.translate(V(BTN_X, BTN_Y, 0))
    plunger = check("Button plunger", plunger)
    for nm, part in (("lid", lid), ("bottom", bottom)):
        iv = plunger.common(part).Volume
        print(f"  Plunger ∩ {nm}: {iv:.4f} mm³")
        assert iv < 1e-3
    # Upward travel: the plunger is free up to PL_BARB_GAP, then the barb hits the bottom of the shaft
    for dz in (PL_BARB_GAP - 0.05, PL_BARB_GAP + 0.1):
        t = plunger.copy(); t.translate(V(0, 0, dz))
        print(f"  Plunger raised by {dz:.2f}: ∩ lid {t.common(lid).Volume:.4f} mm³")
    lid2, inlay = build_lid(two_color=True)
    lid2 = check("Two-colour lid (body)", lid2)
    print(f"  Two-colour lid inlay: solids={len(inlay.Solids)}, isValid={inlay.isValid()}, volume={inlay.Volume:.1f} mm³")
    assert inlay.isValid()
    iv = lid2.common(inlay).Volume
    print(f"  Lid body ∩ inlay: {iv:.4f} mm³")
    assert iv < 1e-3
    inter = bottom.common(lid).Volume
    print(f"  Bottom ∩ lid: {inter:.4f} mm³")
    assert inter < 1e-3

    def out(name):
        return os.path.join(OUT, PREFIX + name)

    # Jumper holder (interference JH_INTERF, neck JH_NECK), placed in both windows in the assembly
    jh = check(f"Jumper holder (interference {JH_INTERF:.2f}, neck {JH_NECK:.1f})", build_jumper_holder(JH_INTERF, JH_NECK))
    holders = []
    for jx, jy in JUMPERS:
        t = jh.copy(); t.translate(V(jx, jy, 0))
        # The interference ribs intentionally reach into the collar by PLUG_RIB_H − PLUG_CLEAR = 0.07 mm
        iv_l, iv_b = t.common(lid).Volume, t.common(bottom).Volume
        print(f"    in window ({jx:.2f}, {jy:.2f}): ∩ lid {iv_l:.3f} mm³ (ribs), ∩ bottom {iv_b:.4f} mm³")
        assert iv_l < 0.5 and iv_b < 1e-3
        holders.append(t)
    ivv = holders[0].common(holders[1]).Volume
    print(f"    holder ∩ holder: {ivv:.4f} mm³")
    assert ivv < 1e-3

    # Parts for printing (STL) and CAD (STEP). Plunger cap down, holder rim down
    # (rotation by 180° about X, NOT a mirror), both with the axis at (0, 0).
    plunger_print = plunger.copy()
    plunger_print.translate(V(-BTN_X, -BTN_Y, 0))
    jh_print = jh.copy()
    for s_ in (plunger_print, jh_print):
        s_.rotate(V(0, 0, 0), V(1, 0, 0), 180)
        s_.translate(V(0, 0, -s_.BoundBox.ZMin))
    for name, s_ in (("Bottom", bottom), ("Button", plunger_print), ("JumperHolder", jh_print)):
        s_.exportStep(out(name + ".step"))
        write_stl(s_, out(name + ".stl"))
    lid.exportStep(out("Top.step"))   # lid as one solid (for CAD); it is printed in two colours, see below

    # Two-colour lid for printing: both parts turned roof down by the SAME transformation,
    # with the same origin, so a slicer can combine them into one multi-part object.
    t2 = lid2.copy(); t2.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    i2 = inlay.copy(); i2.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    off = V(-t2.BoundBox.XMin, -t2.BoundBox.YMin, -t2.BoundBox.ZMin)
    t2.translate(off); i2.translate(off)
    write_stl(t2, out("Top_body_print.stl"))
    write_stl(i2, out("Top_inlay_print.stl"))
    cb = (t2.BoundBox.Center.x, t2.BoundBox.Center.y)
    ci = (i2.BoundBox.Center.x, i2.BoundBox.Center.y)
    print(f"  Two-colour print: body centre ({cb[0]:.3f}, {cb[1]:.3f}), inlay centre ({ci[0]:.3f}, {ci[1]:.3f}), "
          f"inlay offset dX={ci[0] - cb[0]:.3f} dY={ci[1] - cb[1]:.3f}; inlay Z {i2.BoundBox.ZMin:.2f}…{i2.BoundBox.ZMax:.2f}")

    # Assembly: STEP and FCStd
    parts = [("Bottom", bottom), ("Top_body", lid2), ("Top_inlay", inlay), ("Button", plunger)] + \
            [(f"JumperHolder_CAN{i}", h) for i, h in enumerate(holders, 1)]
    Part.Compound([s_ for _, s_ in parts]).exportStep(out("Assembly.step"))
    doc = App.newDocument(PREFIX.rstrip("_"))
    names = []
    for name, s_ in parts:
        doc.addObject("Part::Feature", name).Shape = s_
        names.append(name)
    doc.recompute()
    fc = os.path.join(OUT, PREFIX.rstrip("_") + ".FCStd")
    doc.saveAs(fc)
    ensure_fcstd_gui_visibility(fc, names)
    App.closeDocument(doc.Name)
    print(f"=== Done: {OUT} ===")


main()
