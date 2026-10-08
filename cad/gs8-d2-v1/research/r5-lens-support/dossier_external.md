# GS / HQ camera lens-load dossier (external facts), 2026-10-06

Scope: how the Raspberry Pi Global Shutter (GS) and High Quality (HQ) camera C/CS lens assembly is built and how the lens load reaches the PCB, plus material and lens data for a D2 lens-sag fix. Sources are the local Raspberry Pi drawings and briefs (`cad/gs8-d2-v1/research/m12-drawings/`), official Raspberry Pi pages, forum posts, and manufacturer drawings. Items I could not confirm are marked **[unconfirmed]**. My own measurements and arithmetic are marked **[measured]** or **[inference]**. Forum and documentation text is paraphrased, except for one short quote.

---

## 0. Headline findings (read first)

1. **The mount is metal, not plastic.** The HQ product brief describes a milled aluminium lens mount with an integrated tripod mount (hq_p2.png). The GS launch post says the GS reuses the HQ camera's C/CS-mount metalwork. The official filter-removal procedure, written for both HQ and GS, says the IR filter is glued to the aluminium. The only plastic part on the GS is the removable rear cover. **So the plastic-mount creep premise is wrong.** The compliant links are elsewhere (see 5 and 8).
2. **Load path inside the camera** [inference from the sources in 2 and 3]:
   - lens → C-CS adapter (aluminium) → 1"-32 thread → back-focus adjustment ring (BFAR, aluminium)
   - → a fine external thread on the BFAR (about Ø28.8, 0.75 to 0.8 pitch) → the aluminium housing. The housing's thread is split at the top tab and clamped by the back-focus lock screw.
   - → **two small M2-class socket screws** (1.5 mm hex), fitted from the PCB rear with a nylon washer then a steel washer → **a slightly sticky gasket** → the PCB (FR4, 38 × 38 × 1.4).
   - A Raspberry Pi engineer (6by9) advises users worried about heavy lenses to support the lens and let the camera module float behind it (quoted in 5).
3. **The BFAR moves axially when it is turned.** It is a screw in the housing, carries the CS thread, and the lens moves with it. Its knurled head therefore does **not** stay at a fixed axial position.
4. **The official GS drawing (25.07 mm overall) very probably shows the camera with the C-CS adapter fitted.** Evidence:
   - The GS brief gives the bare camera as 38 × 38 × **19.8** mm, and 29.5 mm with adapter and dust cap.
   - In the drawing, rear cover 6.49 + PCB 1.4 + housing 10.35 + 1.2 element = 19.44 ≈ 19.8. Adding the 5.8 front element gives 25.07.
   - **[measured]** In side view the front 5.8 mm element is **Ø≈31 (the Ø30.75 callout)**. The thin 1.2 mm element behind it is **Ø≈36.5 (the Ø36 callout)**. The official exploded diagram and the brief's cover drawing show the C-CS adapter as a coarse-knurled ring of smaller diameter than the finely scalloped BFAR.
   - So: **the Ø36 scalloped BFAR head stands about 1.2 to 1.6 mm proud of the housing front, and Ø30.75 × ~5.8 is the adapter.**
5. **D2's camera stack therefore looks about 10 mm too long** [inference; verify on the part with calipers before acting]. D2 models:
   - a Ø36 × 5.8 ring, then a Ø30.75 × 5 CS ring, then a 5 mm adapter;
   - a bare depth of 19.27 + 10.8 = 30.07 mm, against the official 19.8 mm;
   - the C flange at x +10.6. Official numbers put it at about x 0 to +3 (BFAR fully in to CS standard; see 8.1).
   
   D2 has no sensor/image plane in `layout.py`, so the 17.526 mm flange focal distance has never been checked.
6. **There is no 39.5 square land at the front of the camera.** 39.5 is the plastic **rear cover**. The PCB is 38 square and sits 10.35 mm behind the housing front.
   - The housing is a round aluminium body about Ø35 [measured], with a 10.16 wide split tab at the top and a 13.97 wide tripod block at the bottom.
   - The only fixed, forward-facing faces outside a Ø36.5 bore are the **top-tab front** and the **tripod-block front and its shoulders**, both in the housing front plane.
   - The official exploded diagram labels the tripod mount *Optional*. Photos show two socket screws on its angled shoulders, so it is probably a separate block screwed to the housing **[unconfirmed]**. It has a **1/4"-20 tapped hole in aluminium**, a metal anchor that bypasses the PCB.
7. **Kowa LM6HC (official Kowa drawing):**
   - the focus ring is near the rear, the iris ring near the front, each with an **M2 thumb screw**;
   - the only part both non-rotating and non-translating is the **Ø42 knurled rear ring, about 2.2 to 7.6 mm ahead of the flange** (fixed status inferred from the photo index mark);
   - the Ø54 front barrel covers only 41.7 to 50.5 mm;
   - D2's segment table has the ring order reversed.
8. **Computar H6Z0812 (official drawing):** a **fixed Ø48.5 rear barrel, about 1 to 25.5 mm ahead of the flange**, which is an ideal cradle location. Focus, zoom and iris rings each carry a lock thumbscrew. Mass is 305 g.

---

## 1. Plastic vs metal (Q1)

| Part | Material | Evidence |
|---|---|---|
| Housing (D2: mount base; RPi: main housing) | **Milled aluminium**, black | HQ product brief p.2 describes a milled aluminium lens mount with an integrated tripod mount (local hq_p2.png; same on [RPi HQ product page](https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/)). GS: [RPi GS launch post](https://www.raspberrypi.com/news/new-raspberry-pi-global-shutter-camera/) says the GS combines the HQ camera's C/CS-mount metalwork with the IMX296; GS brief p.2 says it has the same C/CS-mount lens assembly as the HQ. The filter procedure, valid for both HQ and GS, has the filter glued to the aluminium ([RPi docs, filter removal](https://www.raspberrypi.com/documentation/accessories/camera.html#filter-removal); [source adoc](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/accessories/camera/filters.adoc)). A forum user describes the board as glued to a black metal housing ([forum t=274926](https://forums.raspberrypi.com/viewtopic.php?t=274926)). |
| Back-focus adjustment ring (knurled, carries CS thread) | Aluminium **[unconfirmed for the ring itself]** | The HQ brief lists it as part of the aluminium lens mount assembly. Photos show black anodised, machined-looking scallops. |
| CS thread (1"-32 UN internal) | Cut in the BFAR (aluminium) | [forum t=314326](https://forums.raspberrypi.com/viewtopic.php?t=314326): the BFAR has the C/CS internal thread and an unknown external thread into the housing. |
| C-CS adapter | Aluminium, black, knurled **[unconfirmed for the RPi part]**. Generic 5 mm C-CS rings are anodised aluminium ([Opticstar](https://www.adorama.com/oscsc.html), [Omegon](https://www.omegon.eu/other-adapters/omegon-cs-to-c-mount-adapter/p,60655)). | Official exploded diagram ([HQ product page diagram](https://images.prismic.io/rpf-products/4f9d3f75-0df4-4303-96c0-72d749e64569_200217+HQ+Cam+Diagram+Compliance-01.png)). |
| Tripod mount (1/4"-20) | Aluminium, integrated per the brief, but labelled *Optional tripod mount* in the exploded diagram | HQ brief p.2 and exploded diagram. The thread is cut directly in the block, with no insert visible in the M12-variant photo (hq_p6.png). |
| Rear cover (GS only) | **Plastic**, removable | GS brief p.2: removable plastic back cover. [CNX review](https://www.cnx-software.com/2023/03/09/review-raspberry-pi-global-shutter-camera/). |
| Washers on the 2 housing screws | **Nylon** (against PCB) + steel (under head) | RPi filter-removal procedure. |
| Gasket housing↔PCB | Slightly sticky gasket material (foam/adhesive type) **[material unconfirmed]** | RPi filter-removal procedure: it needs some force to separate and stays on the PCB on reassembly. |
| Dust cap | Plastic **[unconfirmed]** | Adafruit kit photo ([Adafruit 5702](https://www.adafruit.com/product/5702)). |

Masses (GS brief p.3): **34 g bare; 41 g with adapter and dust cap**, so adapter plus cap is about 7 g. The adapter alone is about 4 g **[inference]**: Al ring OD 30.75 / ID ~25.4 × 5 mm plus a ~3 mm thread spigot is about 1.4 cm³ × 2.7 g/cm³. D2's 6.0 g is conservative.

---

## 2. Back-focus mechanism (Q2)

- **What turns, and what moves.** The **BFAR is the part the lens screws into.**
  - The RPi lens guide tells users to screw the CS lens, or the C lens plus C-CS adapter, fully into the BFAR. It also says screwing the BFAR fully in gives the shortest back focus, and that the lock screw keeps it from moving while aperture or focus are adjusted ([MagPi HQ getting started](https://magazine.raspberrypi.com/articles/get-started-with-the-high-quality-camera); [PiShop HQ HowTo](https://support.pishop.us/article/72-raspberry-pi-hq-camera-howto)).
  - The BFAR has a **C/CS internal thread and a separate external thread** into the housing ([forum t=314326](https://forums.raspberrypi.com/viewtopic.php?t=314326)).
  - So turning the BFAR screws it in or out of the housing and **carries the lens with it**. It is not a separate drive collar.
  - **The knurled head moves axially with the ring**, by one pitch per turn. Forum instructions say to screw the BFAR out of the camera body by 1 to 2 turns and then back by about 1.5 notches ([forum t=278608](https://forums.raspberrypi.com/viewtopic.php?t=278608)).
- **BFAR external thread.** Measured by a user at about **Ø28.83 mm**. A 32 TPI gauge fitted very well (0.79 mm pitch); M28 × 0.75 was also proposed ([t=314326](https://forums.raspberrypi.com/viewtopic.php?t=314326)). Another user's procedure gives the ring thread as 0.75 mm pitch and works with ~1/30 turn ≈ 1.5 notches, so the head has about 45 scallops ([t=278608](https://forums.raspberrypi.com/viewtopic.php?t=278608)). **Pitch 0.75 to 0.79 mm [unconfirmed which].** The BFAR wall between the 1"-32 internal thread (major Ø25.4) and the Ø28.8 external thread is only about 1.7 mm radial, so it is thin.
- **Setting vs CS standard.** On one sample, the standard 12.53 mm CS spacing (BFAR outer face to sensor) is reached about **1⅔ turns out from fully in**, which is ≈1.25 mm at 0.75 pitch. Following the factory screw-fully-in instruction gives less than the CS standard ([forum t=380193, sandyol](https://forums.raspberrypi.com/viewtopic.php?t=380193)). Unit-to-unit tolerance applies.
- **Reference face.** The CS flange reference is the **BFAR's outer (front) face** (same thread). The C-CS adapter's rear face seats on it.
- **Travel.** Not documented. The spec back focus length 12.5–22.4 mm (GS brief p.3; HQ brief p.3) is a 9.9 mm span. If that span includes the 5 mm adapter, BFAR travel is about **4.9 mm (≈6 to 6.5 turns)** **[inference, unconfirmed; measure]**. A 10 mm travel inside a 10.35 mm deep housing is implausible.
- **Lock screw.** A small screw in the **split tab at the top of the housing** (tab 10.16 wide with a **0.8 slot**; screw head visible in side view, axis transverse to the optical axis; gs_side.png, exploded diagram label *Back focus lock screw*).
  - Tightening it closes the slot, so the housing's internal thread pinches the BFAR's external thread. That locks rotation and **takes up the thread clearance**.
  - The kit's small flat screwdriver is for this screw ([CNX review](https://www.cnx-software.com/2023/03/09/review-raspberry-pi-global-shutter-camera/)), so it is a **slotted** screw **[size unconfirmed, probably M2]**.
  - With the screw loose, the only things holding BFAR/lens tilt are the fine-thread flank clearance and engagement length. When the BFAR is far out (few threads engaged) the lens wobbles (see 5).
- **Stuck rings.** One BFAR would not turn with the screw removed and needed water-pump pliers to break free ([t=307002](https://forums.raspberrypi.com/viewtopic.php?t=307002)). There is evidence of thread lubricant or locking compound, or of a tight fit.

---

## 3. Housing-to-PCB fixing; corner holes (Q3)

- **Fixing.** **Two 1.5 mm hex lock keys (socket screws) on the underside (rear) of the main PCB** hold the housing. A 1.5 mm hex fits an M2 ISO 4762 socket cap screw **[inference: M2]**.
  - Each has a **nylon washer against the PCB, then a steel washer**.
  - A **slightly sticky gasket** between housing and PCB stays on the PCB. On reassembly the housing is realigned with the gasket.
  - Source: [RPi docs, filter removal](https://www.raspberrypi.com/documentation/accessories/camera.html#filter-removal); [adoc](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/accessories/camera/filters.adoc). It applies to both HQ and GS.
  - **No dowel pins are mentioned**, so housing-to-sensor location appears to rely on the clamp, the gasket and screw-hole clearance **[inference]**.
  - A forum user noted that only two small screws hold the board/camera to the tripod mount ([forum t=282003](https://forums.raspberrypi.com/viewtopic.php?t=282003)).
- **GS rear view** (gs_p4.png rear-cover drawing **[measured]**, gs_p5.png photo):
  - two Ø2.5 holes in the plastic rear cover on the horizontal centreline, 7.56 from each side, so **24.38 apart**;
  - the two socket heads are visible through them, which gives access to the two housing screws;
  - whether the cover is held by the same screws or clipped is **[unconfirmed]**.
- **Corner holes.**
  - **4 × Ø2.5 at 30 mm square pitch**, centres 4 mm from the 38 mm PCB edges, with gold annular pads.
  - The official exploded diagram labels them *Mounting holes*, so they are for the user.
  - The GS rear cover has **Ø5.99 corner reliefs** (R4.75 outline) round them.
  - From the front, the round housing (r ≈ 17.6) clears them (hole centres at r = 21.2).
  - **However**, the tripod-block shoulders sit only about **2 mm** from the edge of the two **lower** holes [measured on gs_side.png front view; check]. Screw heads or standoffs larger than ~Ø4 on the front side of the lower holes may clash. The shoulder screws are also there.
- **Housing front plane** [measured, gs_side.png at 10.08 px/mm]:
  - housing body about **Ø35**;
  - top tab 10.16 wide, top edge about **22.0 mm** above the axis;
  - tripod block 13.97 wide, bottom about **31.0 mm** below the axis;
  - all front faces lie in one plane 10.35 ahead of the PCB front face;
  - the tripod block runs back 12.04 mm, to about the PCB rear;
  - **the 1/4"-20 hole position along x is unmeasured**.
- **Tripod mount screws.** Two socket-head screws sit on the angled shoulders either side of the tripod block. They are visible from the front (Adafruit 5702-03/-04 photos; FILTER_ON photo in RPi docs) and drawn on the brief covers. With the *Optional tripod mount* label, they most likely fix the block to the housing **[unconfirmed]**.

---

## 4. C-CS adapter (Q4)

- **Function.** It moves the reference face forward by 5.000 mm (C 17.526 vs CS 12.526). It has **1"-32 UN** male (into BFAR) and female (lens) threads ([Edmund C-mount drawings](https://www.edmundoptics.eu/document/download/487343); generic).
- **RPi adapter geometry** [inference from the official drawing, section 0 item 4]:
  - knurl/scallop crest **OD ≈ Ø30.75** (inner scalloped outline in the front view, labelled Ø30.75; side view measures Ø≈31.1);
  - **visible band ≈ 5.8 mm** long in the drawing. The nominal face-to-face is 5.0, so either the drawing includes a lip or the BFAR is not fully in **[unconfirmed]**;
  - exploded diagram: a coarse straight knurl (gear-like teeth) all round.
- **Material and mass.** Aluminium, black **[unconfirmed]**, about **4 g** [inference; adapter plus cap is 7 g per brief].
- **Use as a clamp surface** [inference]. The ~5 mm knurled band is the only part between the BFAR head and the lens that a split collar or V-block can grip. It is clamped to the BFAR only by thread friction (no lock), so torque on it can unscrew it.

---

## 5. Reported problems with heavy lenses and the fixes people use (Q5)

No report found of a **cracked HQ/GS mount, mount creep, or screw pull-out**. Searches covered RPi forums, Arducam, Pimoroni and StereoPi forums, and the general web. The mount is aluminium. Reported issues:

1. **Too heavy for the tripod screw.** A Canon EF-S 55-250 user found the lens too heavy to hang on the camera's tripod screw and could not find a collar. Advice: put the tripod on the **lens** (a lens tripod collar/ring), not the camera ([t=297292](https://forums.raspberrypi.com/viewtopic.php?t=297292)).
2. **Max lens weight.** There is no official maximum ([t=282003](https://forums.raspberrypi.com/viewtopic.php?t=282003)).
   - RPi engineer **6by9** advises: "mount the lens and let the module float on the back". This is the approach the original HQ launch blog used with a large Canon lens.
   - A telescope user puts the lens in an **adjustable cradle on two aluminium rods** (optical bench) and warns that only two small screws hold the board.
   - A user with a **600 g** lens found the mount sturdy but planned extra support.
3. **Lens wobble when the BFAR or lens is screwed out to its last threads** (wrong adapter configuration) ([t=343219](https://forums.raspberrypi.com/viewtopic.php?t=343219); [t=276558](https://forums.raspberrypi.com/viewtopic.php?t=276558) via search). Thread engagement controls the play.
4. **BFAR turning while focusing** unless the lock screw is tight ([PiShop HowTo](https://support.pishop.us/article/72-raspberry-pi-hq-camera-howto)). **BFAR seized** in one unit ([t=307002](https://forums.raspberrypi.com/viewtopic.php?t=307002)).
5. **Back-focus setting below standard** when screwed fully in ([t=380193](https://forums.raspberrypi.com/viewtopic.php?t=380193)).

**Fixes and products seen** (none found that clamps the BFAR itself):

- Lens-side tripod collars or cradles, with the camera module floating (forum advice above).
- 15 mm LWS rod lens supports: [SmallRig BSL2680/2681](https://www.cathayphoto.com.sg/photo-video-accessories/tripods-supports-rigs/smallrig-15mm-lws-universal-lens-support-bsl2680) (sold to remove weight stress from the camera's lens mount, height-adjustable); 3D-printable [RigJunkie 15mm long lens support](https://makerworld.com/models/1549226) and a [velcro-loop remix](https://makerworld.com/models/1576141).
- [Entaniya VC-MPC die-cast mounting plate for HQ/GS](https://e-products.entaniya.co.jp/en/list/raspberry-pi/interchangeable-lens-camera-module/mounting-plate-for-raspberry-pi-hq-gs-camera/). It is a 1/4"-20 plate with spacers and screws; how it attaches to the camera is **[unconfirmed]**.
- 3D-printed cine bodies: [CinePi Frame8](https://makerworld.com/models/1438499) (HQ + Pi 4, 1/4"-20 points). Its lens-support method is **[not verified]**. The CinePi XL coverage mentions only a larger physical lens mount ([MagPi](https://magazine.raspberrypi.com/articles/cinepi-xl)).
- The Computar H6Z0812AIVD (auto-iris variant) listing mentions a 1/4"-20 mounting screw ([B&H](https://www.bhphotovideo.com/c/product/889131-REG/computar_H6Z0812AIVD_1_2_8_to.html)). **The manual H6Z0812 drawing shows no tripod foot.**

---

## 6. Material data for design, and cine practice (Q6)

### 6.1 Printed ASA (and PETG/PC) under sustained load at 40–50 °C

**Data found:**

- **Polymaker ASA TDS** ([Polymaker wiki](https://wiki.polymaker.com/polymaker-wiki-pt/produtos-polymaker/mais-sobre-nossos-produtos/documentos/fichas-tecnicas/abs-asa/polymaker-tm-asa)):

  | Property | X-Y | Z (across layers) |
  |---|---|---|
  | Young's modulus | 2379 MPa | 1965 MPa |
  | Tensile strength | 43.8 MPa | **32 MPa** (Z/XY = 0.73) |
  | Elongation at break | 6.7 % | **1.65 %** (brittle across layers) |
  | Notched Charpy | 10.3 kJ/m² | 6.7 kJ/m² |

  Tg is 98 °C, Vicat 105 °C, HDT 100 °C (1.8 MPa) and 103 °C (0.45 MPa). **These are best-case specimens** (100 % infill, 260 °C nozzle, **90 °C chamber**, fan off). Prints from an open or cooler chamber have weaker interlayer bonds.
- **Bambu ASA:** HDT 92 °C (1.8 MPa) and 100 °C (0.45 MPa) ([TDS via search](https://polyalkemi.no/wp-content/uploads/2024/01/Bambu_ASA_Technical_Data_Sheet.pdf); search snippet only, the PDF returned 404).
- **Injection-grade ASA (Luran S 776S):** 1000-h tensile creep modulus about **1200 MPa** (ISO 899-1), against a short-term modulus of ~2300 ([Material Data Center](https://www.materialdatacenter.com/ms/en/Luran%C2%AE+S+776S/d081c8cc/4483); search snippet, full sheet needs registration) **[unconfirmed]**. Creep modulus therefore roughly halves in 1000 h even at room temperature.
- **Dogan 2022**, Strojniski vestnik 68(7-8) 451–460 ([paper](https://ojs30.sv-jme.eu/index.php/sv-jme/article/view/191)).
  - Method: printed then CNC-milled specimens; **3-hour** creep tests at 25, 40 and 60 °C, at 10 and 20 MPa.
  - Creep rate rose with temperature and stress, and **stress mattered more than temperature**.
  - **ABS ruptured in ~3 min at 60 °C / 20 MPa.**
  - CPE (Ultimaker CPE is a copolyester of the PETG family, although the paper expands it as chlorinated polyethylene) did better than ABS.
  - **PC was least affected and did not fail** under any condition.
  - PLA was worst. Nylon crept most but did not rupture.
  - The authors rate ABS and CPE fit for medium loads at moderate temperatures, not for high load and high temperature.

**Suggested allowables [engineering judgement, not from a source; check against the main session's own data]:**

- ASA is an amorphous styrenic close to ABS, with Tg ~98–100 °C. At 45–50 °C it keeps perhaps 70–80 % of its 23 °C short-term strength and stiffness, but creep is several times faster than at 23 °C.
- For sustained loads over months in a warm camera, keep **strain ≤ 0.5 %** and stress at **≤ ~4–5 MPa in-plane (XY)** and **≤ ~2–3 MPa across layers (Z)**. That is roughly 10–15 % of short-term strength after the 0.73 Z factor.
- Example: 3 MPa sustained in XY with an effective 1000-h modulus of ~800–1000 MPa at 50 °C gives ε ≈ 0.3–0.4 %. That is acceptable for strength but **not** for a 0.3° tilt budget if the part is a long lever.
- Design the joint so plastic is **in compression on broad faces** (bearing ≤ ~5 MPa), not in bending or in tension across layers.
- **PETG** (Tg ~80 °C) sits closer to Tg at 50 °C, so expect more creep than ASA there [inference].
- **PC** (Tg ~145 °C) is far better (Dogan 2022) and is the material of choice for a printed lens cradle or clamp if it can be printed well.
- Creep also applies to the camera's own joint: **nylon washers and the sticky gasket** under the two M2 housing screws will relax at 40–50 °C [inference]. This is a probable real sag mechanism if the PCB is the support.

### 6.2 Cine practice for lens supports

- **Purpose.** Rod-mounted lens supports take the lens weight off the camera's lens mount. Height is adjusted after the lens is mounted, and placement is fine-tuned under the barrel to cut micro-movement and keep alignment ([SmallRig BSL2681](https://videoguys.com.au/a/p/products/smallrig-bsl2681-15mm-lws-universal-lens-support-with-2-1-vertical-adjustment); [Bright Tangerine 15 mm LWS support](https://brighttangerine.com/products/15mm-lws-lens-support)).
- **Common practice [inference/general knowledge]:**
  - the support bears on a **non-rotating, non-translating** part of the barrel, or on the lens's own support foot (big zooms);
  - it should **carry weight without lifting** the lens, because a support that pushes up stresses the mount and can tilt the image;
  - adjust it after the lens is fully seated and locked;
  - never clamp a rotating ring or a translating focus group.
  - The mechanically clean form is one stiff datum (the mount) plus one height-adjustable or compliant support. Two rigid supports over-constrain the lens unless the second is set in place.
- **Rod standards** ([OConnor Labs](https://www.ocon.com/inspiration/labs/rod-standards-explained/)): 15 mm LWS is 60 mm centre-to-centre and 85 mm from the optical centre; 15 mm Studio is 100 / 118 mm (offset 17.25); 19 mm Studio is 104 / 120 mm. Supports hang off the camera's base structure, not the lens mount.

---

## 7. Lens mechanics (Q7)

### 7.1 Kowa LM6HC

Sources: official Kowa drawing, LM6HC outline drawing 2, HR1059NCN, rev 2019-03-20 ([datasheet PDF](https://www.kowa-lenses.com/media/c9/8e/1d/1712657779/LM6HC%20Datasheet.pdf?ts=1716797780); [product page](https://www.kowa-lenses.com/en/lm6hc-5mp-wide-angle-industrial-lens-c-mount)); photo ([Machine Vision Direct](https://machinevisiondirect.com/products/kowa-lm6hc)).

**Basic data:**
- Ø54, length 56.2 (∞) or **56.6 (0.1 m MOD)**, so the front moves 0.4 mm over the focus range.
- 215 g, **no filter thread**, front effective Ø46.0, rear effective Ø16.8.
- Back focus 11.1 in air; rear protrusion behind the flange 6.7; C thread 1-32UNF; rear spigot Ø22.5.
- **Two M2 thumb screws**: one locks focus, one locks iris.

**Sections, measured from the flange forward** [measured on the drawing, ±0.5 mm]:

| From flange (mm) | Section | Ø | Moves? |
|---|---|---|---|
| −6.7 … 0 | C thread / rear spigot | 25.4 / 22.5 | fixed |
| 0 … 2.2 | rear spigot step | ≈31.5 | fixed |
| **2.2 … 7.6** | **knurled ring (silver in photo)** | **42** | **fixed [inferred]**: the photo shows the focus index tick on this ring under ∞, so it is the mount/grip ring |
| 7.6 … 10.6 | groove | ≈39 | — |
| 10.6 … 22.4 | **focus ring** (distance scale 0.1…∞ m); **M2 thumb screw at ≈14.4** | ≈41.7 | rotates |
| 23.1 … 29.2 | label barrel (f=6mm/F1.8) | ≈38.6 | probably translates with focus, does not rotate **[unconfirmed]** |
| 30.9 … 36.6 | **iris ring** (1.8…11); **M2 thumb screw at ≈33.0** | ≈38.5 | rotates |
| 37.6 … 41.4 | step | ≈41.5 | moves with front group **[unconfirmed]** |
| 41.7 … 50.5 | **front barrel / hood** | **≈53.5–54** | moves with front group (0.4 mm) **[unconfirmed]** |
| … 56.2 | front dome | — | — |

**Thumb-screw heads:** about Ø3.8 and about 3–3.5 mm proud of their rings, reaching r ≈ 23–24 (inside the Ø54 envelope). Both are drawn at the bottom of the side view, but their angular position on a mounted lens depends on the ring settings.

**Differences from D2's `LENSES['kowa_lm6hc']`:**
- D2 puts the iris ring at 5–15 and the focus ring at 23–45, with radius 27 over 23–45. The drawing shows **focus at the rear and iris at the front**, diameters only 38.5–42 behind 41.7 mm, and **Ø54 only over 41.7–50.5**.
- D2's lock screws at 10 / 34 should be about **14.4 (focus) / 33.0 (iris)**.

**Support location:**
- The only certainly-fixed band is the Ø42 knurl at **2.2–7.6 mm** (plus the Ø31.5 spigot).
- The front barrel is not a safe fixed datum if it translates with focus. A V-cradle under it must allow 0.4 mm axial slip and must not drag the focus [inference].

### 7.2 Computar H6Z0812

Source: official Computar spec sheet, 2004.5 ([PDF](https://computarganz.s3.amazonaws.com/Computar+Active+Resources/H6Z0812+Spec.pdf); [product page](https://www.computar.com/products/h6z0812)).

**Basic data:**
- 8–48 mm f/1.2, 1/2", manual zoom, focus and iris.
- **305 g**, **Ø51.75 × 97 mm** (∞), **filter M49 × 0.75**.
- MOD 1.2 m; back focal length 11.4; rear protrusion 6 behind the flange (C thread 4 long), rear Ø22.2 / Ø29.5.
- Focus, zoom and iris rings are **geared**: module 0.45, 115 teeth, pitch diameter Ø51.75.

**Sections, measured from the flange forward** [measured on the drawing, ±0.5 mm]:

| From flange (mm) | Section | Ø | Moves? |
|---|---|---|---|
| **≈1 … 25.5** | **rear barrel (plain)** | **48.5** | **fixed [inferred]**: no ring or scale; housing of the rear group |
| 25.5 … 35.6 | **iris ring** (gear at 25.5–30); thumb screw ≈28.3 | gear 51.75 | rotates |
| 38.4 … 47.2 | **zoom ring** (gear 38.4–42.4); thumb screw ≈39.7 | gear 51.75 | rotates |
| 47.2 … 68.2 | plain mid barrel | ≈46 | fixed **[unconfirmed]** |
| 68.2 … 77.9 | focus scale ring; thumb screw ≈73.1 | ≈46 | rotates with focus |
| 78.9 … 85.2 | **focus ring** (gear) | 51.75 | rotates |
| 86.9 … 97 | front barrel | 51 | moves with focus **[unconfirmed]** |

- **Lock thumbscrews** sit on the focus (scale) ring, the zoom ring and the iris ring, all drawn at the top.
- **No lens tripod foot** is shown on the manual H6Z0812. The auto-iris AIVD listing mentions 1/4"-20, **[unconfirmed]**.
- **Support location:** the **Ø48.5 fixed rear barrel, about 1 to 25 mm ahead of the flange**, which is a long, plain cylinder ideal for a cradle or split clamp.
- The centre of mass is not published. It is probably 35–45 mm ahead of the flange **[guess]**.

---

## 8. Cross-checks against D2's `layout.py` (computed; verify before acting)

### 8.1 Axial stack

**Official numbers:**
- From the cover rear: cover 6.49 + PCB 1.4 + housing 10.35, so the **housing front plane is 18.24 mm** ahead of the cover rear.
- The BFAR face is +1.2 ahead of that as drawn, or +1.56 using the 19.8 mm spec.
- The C flange is BFAR face + 5.0.
- **As drawn:** C flange = housing front + 6.2…7.0, which is PCB front + ~17.35.
- **At the CS standard** (sandyol, +1⅔ turns ≈ +1.25): housing front **+7.5…8.3**.

**Sanity check:**
- The IR glass (1.1 mm, n≈1.5) pushes focus back by ≈0.37 mm **[inference]**, so the image plane is C flange − 17.9.
- At the standard setting the image plane falls ≈ PCB front + 0…0.7 mm, which is plausible for the die height plus the sensor cover glass.
- In the fully-in, as-drawn position it would fall 0.5–1.4 mm behind the PCB front, which is impossible. That agrees with the forum finding that fully in is short of the standard.

**D2 values:**
- Seat (x −5.2) is treated as the front of a 39.5 square land, with 19.27 behind it.
- Then ring 5.8 + CS ring 5 + adapter 5, giving **C flange +10.6**.
- D2's bare camera is 30.07 deep, against **19.8 official**.

**Real stack:**

| Assumption | Cover rear | C flange |
|---|---|---|
| Housing-front plane (top-tab and tripod-block faces) seats on the wall at x −5.2 | −23.44 | **≈ +2.3…+3.1** |
| D2's cover-rear x −24.47 kept | — | **≈ +1.3…+2.1** |

**Consequences [inference]:**
- The lens would sit **≈8–9 mm further back** than D2 models.
- With the Kowa, the Ø31.5 spigot and the **Ø42 knurled ring (flange +2.2…+7.6)** would lie at x ≈ +3…+11. That is inside the hood plate/turret zone (x −2.5…+8.5, bore Ø36.5), so they collide.
- The lens CoM moves back by the same amount. Its moment about the housing front becomes ≈ (7.5…8.3 + 28.3) × 2.11 N ≈ **0.076 N·m** (Kowa, static).
- J7 needs re-deriving from a sensor-plane datum (C flange = image plane + 17.526) and caliper measurements.

### 8.2 Seat and support faces that actually exist

**Fixed (non-rotating) aluminium faces in the housing front plane:**
- the **top split tab** (10.16 wide, r ≈ 18.25…22.0 outside a Ø36.5 bore);
- the **tripod block and shoulders** (13.97 wide, r ≈ 18.25…31.0).

**PCB front face:** 10.35 further back, with 4 free Ø2.5 holes on a 30 square.

**Metal anchors that bypass the PCB:**
- the **1/4"-20 tripod hole** (aluminium, axis vertical, pointing down);
- the housing OD (≈Ø35, but the lock-screw tab and slot are at the top);
- the C-CS adapter knurl (Ø30.75 × ~5);
- the lens's own fixed barrel.

**Load paths that avoid the M2 + nylon-washer + gasket + PCB joint** [inference]:
1. Support the lens at its fixed barrel (Kowa Ø42 rear knurl; Computar Ø48.5 rear barrel), and let the module float, as 6by9 advises.
2. Clamp or preload the aluminium housing directly: front-plane faces against the wall, plus a 1/4"-20 screw into the tripod block.

A preload is needed either way. A nose-down moment otherwise lifts the top-tab face off the wall while the tripod face pivots.

### 8.3 Ring/bore assumption

- D2's bore Ø36.5 around a Ø36 BFAR assumes the BFAR is a long cylinder at a fixed x. In reality it is a **~1.2–1.6 mm thick scalloped head** that **moves forward about 0.75–0.8 mm per turn** (≈1.25 mm to reach the CS standard; up to ~5 mm total **[unconfirmed]**).
- The adapter (Ø30.75) is the long element.

---

## 9. Measure on the real camera before designing (calipers / dial indicator)

1. **BFAR:**
   - head OD and thickness;
   - protrusion ahead of the housing front plane, fully in and at the setting that focuses the Kowa at ∞;
   - pitch (turns over a measured travel);
   - total travel.
2. **Adapter:** OD over the knurl, band length outside the BFAR face, spigot length, mass.
3. **Housing:**
   - OD;
   - flatness and coplanarity of the tab and tripod-block front faces;
   - x-position, depth and thread length of the 1/4"-20 hole;
   - size of the tripod-block screws and of the lock screw.
4. **Joint compliance:** dial-indicator deflection at the lens front for a known hanging mass, with the module held (a) by the PCB holes only and (b) by the housing faces plus the tripod screw. Do this with the lock screw loose and with it tight.
5. **Kowa:** confirm which sections rotate and which translate with focus (watch the knurled Ø42 ring and the Ø54 front barrel), and find the CoM by balancing on a knife edge.

---

## 10. Key sources (also inline above)

**Local Raspberry Pi files** (`research/m12-drawings/`):
- gs_side.png, gs_p1–p5 (GS brief: overview, spec 19.8 / 29.5 mm, 34 / 41 g, drawing, rear-cover drawing, rear photo);
- hq_p1–p6, hq_draw.png (HQ brief: milled aluminium mount, drawings).

**Raspberry Pi official:**
- [docs: camera, filter removal (HQ + GS)](https://www.raspberrypi.com/documentation/accessories/camera.html#filter-removal) and [adoc source](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/accessories/camera/filters.adoc);
- [HQ product page](https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/) and its [exploded diagram](https://images.prismic.io/rpf-products/4f9d3f75-0df4-4303-96c0-72d749e64569_200217+HQ+Cam+Diagram+Compliance-01.png);
- [GS launch post](https://www.raspberrypi.com/news/new-raspberry-pi-global-shutter-camera/);
- [MagPi HQ getting started](https://magazine.raspberrypi.com/articles/get-started-with-the-high-quality-camera).

**Forums:**
- [t=314326 BFAR thread](https://forums.raspberrypi.com/viewtopic.php?t=314326);
- [t=278608 16 mm HowTo](https://forums.raspberrypi.com/viewtopic.php?t=278608);
- [t=380193 BFAR vs CS standard](https://forums.raspberrypi.com/viewtopic.php?t=380193);
- [t=307002 stuck BFAR](https://forums.raspberrypi.com/viewtopic.php?t=307002);
- [t=282003 max lens weight](https://forums.raspberrypi.com/viewtopic.php?t=282003);
- [t=297292 heavy telephoto](https://forums.raspberrypi.com/viewtopic.php?t=297292);
- [t=343219 wobble](https://forums.raspberrypi.com/viewtopic.php?t=343219);
- [t=274926 filter/housing](https://forums.raspberrypi.com/viewtopic.php?t=274926).

**Reviews and photos:**
- [CNX GS review](https://www.cnx-software.com/2023/03/09/review-raspberry-pi-global-shutter-camera/);
- [Adafruit 5702 photos](https://www.adafruit.com/product/5702).

**Lenses:**
- [Kowa LM6HC datasheet/drawing](https://www.kowa-lenses.com/media/c9/8e/1d/1712657779/LM6HC%20Datasheet.pdf?ts=1716797780);
- [Machine Vision Direct LM6HC](https://machinevisiondirect.com/products/kowa-lm6hc);
- [Computar H6Z0812 spec PDF](https://computarganz.s3.amazonaws.com/Computar+Active+Resources/H6Z0812+Spec.pdf).

**Materials:**
- [Polymaker ASA TDS](https://wiki.polymaker.com/polymaker-wiki-pt/produtos-polymaker/mais-sobre-nossos-produtos/documentos/fichas-tecnicas/abs-asa/polymaker-tm-asa);
- [Dogan 2022 creep paper](https://ojs30.sv-jme.eu/index.php/sv-jme/article/view/191).

**Supports:**
- [OConnor rod standards](https://www.ocon.com/inspiration/labs/rod-standards-explained/);
- [SmallRig lens support](https://videoguys.com.au/a/p/products/smallrig-bsl2681-15mm-lws-universal-lens-support-with-2-1-vertical-adjustment);
- [Entaniya VC-MPC](https://e-products.entaniya.co.jp/en/list/raspberry-pi/interchangeable-lens-camera-module/mounting-plate-for-raspberry-pi-hq-gs-camera/).

**Not reachable:** Baumer LM6HC PDFs (403), Basler (406), Material Data Center full sheets (registration). No downloads were made beyond what WebFetch cached for the two lens PDFs and the creep paper. One browser navigation to a Baumer PDF raised a save dialog for the user; I did not save it. No logins or purchases.
