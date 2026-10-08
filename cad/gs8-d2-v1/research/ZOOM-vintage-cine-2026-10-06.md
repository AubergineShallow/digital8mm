# Vintage cine C-mount parfocal zooms for GS8 D2

Research only, 2026-10-06. Nothing bought, no one contacted. eBay, Etsy, ManualsLib, super8wiki, collectiblend and
Carousell pages refuse automated fetches. Prices therefore come from search-result snippets plus a few dealer pages.
Mass figures marked **[derived]** are a camera's "weight with lens" minus its "body" weight from the same source.
Anything not confirmed by a source is marked [unconfirmed]. Sources are numbered [Sn] at the end.

## 0. Key findings

1. **Only Super 8 / Single-8 interchangeable-lens zooms reach a useful wide end.** These are the Beaulieu and Fujica ZC1000 lenses.
   They start at 6-8 mm, which is 41-55 mm equivalent on D2. Every 16 mm C-mount zoom starts at 9.5 mm or longer (66 mm eq or more);
   the common ones start at 12-17 mm (83-117 mm eq).
2. **Every candidate is 2.5-4.5x D2's 200 g lens budget.** None weighs less than about 500 g. The Beaulieu f/1.2-1.4 zooms are
   about 900 g. Expect to add a lens support or front foot, or to rebalance the grip. No light vintage cine parfocal zoom with a wide end exists in C-mount.
3. **D2's adjustable back focus helps.** Its 12.5-22.4 mm back-focus range [S34] covers any lens whose true flange distance lies
   anywhere between CS and C+5 mm. The reported odd flange of the Beaulieu Optivaron [S14] can therefore be trimmed out, and parfocal
   tracking can be set on the bench.
4. **Rear protrusion should be short, but is unmeasured.** Beaulieu and ZC1000 bodies use a 45 deg mirror shutter right behind the mount
   [S2][S22], so their lenses had to stay short at the rear [inference]. No published rear-protrusion or rear-element figures were found
   for any candidate, so measure before committing. The Fujinon's rear cover ring is known to foul a Beaulieu mount face [S23].
5. **Avoid RX lenses, and watch for non-C mounts.** Bolex RX zooms are corrected for a reflex prism and are soft on a camera without
   one [S32]. Several near-misses are not C-mount: the Leicina Optivaron, the Bauer Angenieux 6-90, the Vario-Switar POE (Bolex
   bayonet), and every D-mount 8 mm zoom.

## 1. D2 fit constraints used for scoring

- Sensor: 5.02 x 3.75 mm, 6.27 mm diagonal. Crop factor 43.27/6.27 = **6.90**. Horizontal field = 2*atan(2.51/f): 6 mm = 45.4 deg,
  7.5 mm = 37.0 deg, 8 mm = 34.8 deg, 12 mm = 23.6 deg, 17 mm = 16.8 deg.
- The Super 8 frame (7.08 mm diagonal) is larger than the sensor, so any lens that covers Super 8 covers D2 with margin.
  An EOS M crop-mode test of the Optivaron 6-66 gave a clean 1392x1028 px at 4.3 um, about 5.99 x 4.42 mm or 7.4 mm diagonal [S14][S16].
  The Angenieux 8-64 gave 1408x1030 clean [S14] and is sold as "no vignetting in a Max 8 frame" [S11].
- The IR filter is 1.1 mm glass [S33], close to the sensor. Raspberry Pi publishes no rear-clearance limit [S33], so measure it on the D2 mount stack.
- Balance target: about 200 g at the front (current Kowa LM6HC is 215 g).

## 2. Priority 1: Super 8 / Single-8 interchangeable zooms in C-mount

| Lens (mount, source) | Range -> 35 mm eq | Max f | Mass | Filter | Price used, USD (SGD at 1.28) |
|---|---|---|---|---|---|
| Schneider-Kreuznach Beaulieu **Optivaron 6-66 mm Macro** (C; Beaulieu 4008 ZM II/5008 S) [S2][S4][S18] | 6-66 -> **41-455** | 1.8 | ~600 g [derived: 4008 ZM II 1500 g total, 900 g body; S2] | 62 mm? [unconfirmed; S35 hood] | 250-450 (320-580). A near-mint listing with hood was US$399.99 [S35] |
| **Angenieux 8-64 mm** Type 8x8 (C; Beaulieu 2008 S/4008 ZM, Pro8mm Classic) [S1][S10] | 8-64 -> **55-442** | 1.9 | **500 g** with Reglomatic [S1] | **49 mm** [S10] | eBay listings 329-450 (420-575) [S35]. Pro8mm collimated price 1,495 (1,914) [S11] |
| **Angenieux 6-80 mm** (C; Beaulieu 5008 S/6008/7008) [S4][S5][S17] | 6-80 -> **41-552** | 1.2 (T1.4) | ~880 g [derived: 2.55 kg with lens [S5], 1.67 kg body [S4]] | [unconfirmed] | 250-600 (320-770) [unconfirmed; no current lens-only sale captured] |
| Schneider-Kreuznach Beaulieu **Optivaron 6-70 mm** (C; 4008 ZM4, 6008 S) [S3][S6] | 6-70 -> **41-483** | 1.4 | ~900 g [derived: 1800-900 g [S3]; 2570-1670 g [S4]] | **77 mm** [S6] | 250-600 (320-770) [unconfirmed] |
| **Angenieux 6-90 mm Macro** 15x (C, Beaulieu version; 6008 Pro/7008/9008) [S19][S20] | 6-90 -> **41-621** | 1.4 | >=900 g [unconfirmed] | [unconfirmed] | ~1,000+ (1,280+) [unconfirmed; Re:Voir rental deposit is EUR 1,100 [S19]] |
| **EBC Fujinon MA-Z 7.5-75 mm** macro (C; Fujica ZC1000) [S21] | 7.5-75 -> **52-518** | 1.8 | [unconfirmed]; ZC1000 with lens is 1950-1980 g, body-only figure not found [S21][S22] | **62 mm** [S21] | 300-800 (384-1,024) [unconfirmed; lens alone is rarely sold. Japanese list price was JPY 69,300] |
| Schneider **Variogon 8-40 mm** (C; Beaulieu 2008 S option) [S9] | 8-40 -> 55-276 | 1.8 | [unconfirmed]; probably lighter than the 8-64 | [unconfirmed] | rare [unconfirmed] |
| Schneider **Optivaron 8-50 mm** macro (C; 4008 ZM4 option, 3008 S) [S3] | 8-50 -> 55-345 | 1.4 | [unconfirmed] | [unconfirmed] | rare [unconfirmed] |

**Shared traits (all rows):**
- **Parfocal:** Yes. All are mechanically compensated zooms built for focus-at-tele-then-zoom reflex cameras (ground glass on Beaulieu
  and ZC1000). An EOS M user reports "good parfocal performance" from the Optivaron once the adapter was shimmed [S14].
- **Macro breaks parfocality.** On the Optivaron the macro lever sits near the mount [S35]; the 8-64 has a macro setting [S12]; the
  Fujinon's macro reaches 0.02 m [S21]. In macro mode focus moves to the zoom group, so parfocality is lost [general; unconfirmed per lens].
  The 6-90 is different: it focuses to 60 cm at every focal length [S19], which keeps tracking.
- **Couplings:** All have manual focus, zoom and iris rings. The motor arrangement depends on the generation.
  - 2008/4008 era (8-64, 6-66): the Reglomatic micromotor is "mounted under the lens" and "geared to the interchangeable lens" [S8].
    The 4008 manual warns not to hold the lens "only by the Reglomatic device" [S13], so the motor box travels with the lens.
    It adds mass and a side bulge, but it is also a ready-made iris servo. Pro8mm lists manual-zoom, manual+macro and power-zoom
    versions of the 8-64 [S10]. For D2, prefer a manual one.
  - 5008/6008 era (6-80, 6-70, 6-90): iris and zoom are driven "by the motors located inside the camera body through the gears and
    pinions" [S17]. The lens itself is purely mechanical with gear rings. It can be motorized later. How stiff these rings are by hand is [unconfirmed].
  - Fujinon: manual zoom [S21]. Its AE iris linkage to the ZC1000 is [unconfirmed]; check that the aperture ring works without a body.
- **Rear protrusion:** No figure published for any of these lenses. Mirror-shutter bodies imply a short rear [inference].
  The Fujinon's rear cover protrudes past the barrel face and had to be removed or machined before it would seat on a Beaulieu [S23].

**Per-lens notes:**
- **Optivaron 6-66:** Regarded as the reference Super 8 zoom: a ZM II with it was called the "Holy Grail" of Super 8 cameras [S38].
  An EOS M user found its flange is not standard C, attributed to an "internal filter" [S14]; D2's back-focus ring absorbs this.
  Vignetting begins just past about 7.4 mm diagonal [S16], so the 6.27 mm IMX296 is covered with little margin. Check the corners at 6 mm.
- **Angenieux 8-64:** Generous coverage (Max 8) [S11]. One user suggests it descends from a 9.5 mm-format design [S14] [unconfirmed].
  It is still serviced and collimated commercially: Pro8mm fits it to the new C-mount Kodak Super 8 camera [S12].
- **Angenieux 6-80:** Its "very small image circle" still exceeds Super 8 [S17]. On digital it shows "so-so sharpness and lots of
  chromatic aberrations" [S17], which is one user's verdict. It is the fastest lens here.
- **Optivaron 6-70 / Angenieux 6-90:** Fast and long, but both are heavy. The 77 mm filter of the 6-70 [S6] shows its size.
- **Age risk:** All were made between 1965 and 1990. Check for haze, fungus and balsam faults. No thoriated glass is reported for these lenses [unconfirmed].

## 3. Priority 2: 16 mm cine C-mount zooms (2x-plus crop; none is wide on D2)

| Lens (mount) | Range -> 35 mm eq | f | Mass | Notes | Price USD (SGD) |
|---|---|---|---|---|---|
| **Angenieux 12-120** Type 10x12 A/B (C; RX versions marked "RX") [S26][S27] | 12-120 -> 83-828 | 2.2 | 794 g (1 lb 12 oz); 1077 g with viewfinder | Series IX filter. Close focus 5 ft (viewfinder version). Parfocal. **Avoid RX on D2** [S32] | Sold 300 (Aug 2025) and 406.70; asks 400-1,250 (384-1,600) [S35] |
| **Angenieux 17-68** Type L1/L2 (C) [S28] | 17-68 -> 117-469 | 2.2 | [unconfirmed] | 45 mm filter, 1 m close focus, "not very sharp wide open". It is a 16 mm lens, not true S16 | ~400 fair; asks to 2,000 (512-2,560) [S28] |
| Angenieux 10-150 Type 15x10B (C/Bolex) [S35] | 10-150 -> 69-1035 | 2.0 | heavy [unconfirmed, >1.5 kg] | Mostly parts or repair listings seen | [unconfirmed] |
| Angenieux 12.5-75 Type 6x12.5A (C) | 12.5-75 -> 86-518 | 2.2 | [unconfirmed] | Seen used in C-mount on eBay [S35] | [unconfirmed] |
| Angenieux 9.5-57 | 9.5-57 -> 66-393 | 1.6 | [unconfirmed] | Mostly Arri/Eclair mounts; C-mount examples rare [unconfirmed] | high [unconfirmed] |
| SOM Berthiot **Pan Cinor 85** 17-85 (C) [S29] | 17-85 -> 117-587 | 2.0 | 1.02 kg | Built-in reflex finder; close focus 6 ft | [unconfirmed] |
| SOM Berthiot Pan Cinor 70, 17.5-70 (C) [S35] | 17.5-70 -> 121-483 | 2.4 | [unconfirmed] | Viewfinder type | [unconfirmed] |
| Kern Vario-Switar **86 EE** 18-86 (C, **RX**) [S30] | 18-86 -> 124-593 | 2.5 | 1.02 kg | Built-in EE auto-iris; RX-corrected | [unconfirmed] |
| Schneider Variogon 18-90 (C) [S31] | 18-90 -> 124-621 | 2.0 | [unconfirmed] | 74 mm filter. One user: wide end "doesn't quite focus to infinity" (a flange issue, which D2 can trim) | EUR 500 (2017) |
| Canon 12.5-50 (C, "tiny", sold for Bolex) [S35] | 12.5-50 -> 86-345 | 1.8 | [unconfirmed] | Probably a TV-era design [unconfirmed] | [unconfirmed] |

- **Not found:** a Schneider Variogon 16-80 f/2.8 in C-mount [unconfirmed whether it exists], and any Kinoptik zoom
  (Kinoptik C-mount output found was primes only [unconfirmed]).
- **Conclusion for 16 mm lenses:** about 800 g or more for an 83 mm-equivalent wide end. They act as telephoto zooms on D2 and lose to the Super 8 lenses on every criterion except price.

## 4. Excluded (not C-mount, or not removable)

- **D-mount 8 mm zooms** (Bolex H8), e.g. Kern Vario-Switar 8-36 f/1.9 and Angenieux 9-36 f/1.8 Type K1 in D [S36]:
  - D flange is 12.29 mm, below C's 17.526 mm, and also 0.21 mm below D2's minimum 12.5 mm CS back focus [S34]. They cannot reach infinity without machining.
  - "D-RX" variants are additionally prism-corrected [S36].
- **Optivaron 6-66 in Leicina Special mount.** "Originally M-mount and not C-mount" [S25]. Do not confuse it with the Beaulieu C version:
  the EUR 299 eBay sale in Aug 2025 was a Leicina lens [S35].
- **Angenieux 6-90 f/1.4 in Bauer (S 715 XL) mount** [S24]. Buy only the Beaulieu C-mount 6-90.
- **Kern Vario-Switar 16-100 POE:** Bolex bayonet, 1290 g [S30].
- **Fixed-lens cameras**, whose lenses cannot be removed: Canon DS-8 (7.5-60 f/1.4) [S37], Canon Scoopic 16/16M [S39], and Nizo, Canon 1014 and similar.

## 5. Singapore availability (Carousell SG, via indexed web search only)

Domain-restricted searches on 2026-10-06 found **no indexed Carousell SG listing for any candidate**. The queries were "Angenieux zoom
lens", "super 8 Beaulieu camera lens", "C mount cine zoom lens 16mm Bolex", "Bolex H16 reflex lens Switar Angenieux" and "Fujica single 8
ZC1000 Fujinon". Hits were unrelated: an Angenieux 28-70 AF, a Kern Switar 16 mm f/1.8 C-mount prime, a Digital Bolex D16, and an Eumig
Super 8 camera. Carousell is poorly indexed, so a manual in-app search by the user is still worthwhile. Otherwise buy from eBay (Japan
and EU sellers are common for Beaulieu and ZC1000 lenses) or from Pro8mm for a collimated 8-64.

## 6. Ranked shortlist for D2

1. **Schneider Optivaron 6-66 f/1.8 Macro (Beaulieu C).**
   - Why: the only common lens that keeps D2's 6 mm / 41 mm-eq wide end. It is parfocal, about 600 g [derived], about US$250-450 (S$320-580), and covers the sensor with a small margin.
   - Watch: its flange offset (trim it with the back-focus ring) and the Reglomatic box.
2. **Angenieux 8-64 f/1.9 Type 8x8 (Beaulieu C).**
   - Why: the lightest true parfocal Super 8 zoom (500 g with motor box; a manual version is lighter), with a small 49 mm filter and generous Max-8 coverage. About US$330-450 (S$420-575), or Pro8mm collimated for US$1,495.
   - Cost: the wide end narrows to 55 mm eq.
3. **Angenieux 6-80 f/1.2 (Beaulieu 5008/6008 C).**
   - Why: 41 mm-eq wide end and the fastest aperture; gear-ring iris and zoom suit a later servo.
   - Cost: about 880 g [derived] and reported CA and softness on digital.
4. **EBC Fujinon MA-Z 7.5-75 f/1.8 (Fujica ZC1000 C).**
   - Why: a modern EBC-coated design for a mirror-shutter body (no prism correction), 52 mm eq.
   - Cost: rare as a standalone lens, mass unknown, and the rear cover may foul D2's mount face.
5. **Schneider Optivaron 6-70 f/1.4 (Beaulieu 4008 ZM4/6008 C).**
   - Why: 41 mm eq at f/1.4.
   - Cost: about 900 g [derived] with a 77 mm front. Pick it only if speed matters more than balance. The Beaulieu-mount Angenieux 6-90 f/1.4 is the pricier alternative here.
- **16 mm fallback:** the Angenieux 12-120 non-RX (cheap and plentiful, but it starts at 83 mm eq) only if a long tele zoom is the goal.

## 7. Checks before buying

- Confirm the "C" mount, not Leicina, Bauer or D. Prefer the manual-zoom version, and check the Reglomatic or motor box for side
  clearance against the D2 grip and front.
- Ask the seller for:
  - rear protrusion behind the flange face;
  - rear barrel and cover OD within 3 mm of the flange;
  - rear element diameter.
  Compare these against the D2 C-CS adapter, the back-focus ring and the 1.1 mm IR filter.
- Bench-set parfocal tracking with the back-focus ring: focus at tele, zoom out, and trim until the wide end stays sharp. Lock the ring.
- Inspect for haze, fungus and separation. Check that the iris ring turns by hand with no body attached (5008/6008 gear lenses, Fujinon).
- Plan a front lens support. Every candidate shifts the centre of mass well forward of the grip.

## Sources

- S1 https://www.filmkorn.org/super8data/database/cameras_list/cameras_beaulieu/beaulieu_4008zm.htm (8-64, C, lens 500 g, body 900 g)
- S2 https://www.filmkorn.org/super8data/database/cameras_list/cameras_beaulieu/beaulieu_4008zm2.htm ; https://www.super8wiki.com/index.php/Beaulieu_4008_ZM_2 (snippet: 1500 g body+lens; mirror shutter via https://www.straight8.net/beaulieu-4008)
- S3 https://www.filmkorn.org/super8data/database/cameras_list/cameras_beaulieu/beaulieu_4008zm4.htm (6-70 f/1.4; 900/1800 g; 8-50 f/1.4 option)
- S4 https://www.filmkorn.org/super8data/database/cameras_list/cameras_beaulieu/beaulieu_5008s.htm (body 1670 g; 2570 g with Schneider)
- S5 https://en.wikipedia.org/wiki/Beaulieu_5008_S (2.55 kg with Angenieux 6-80 f/1.2-1.4)
- S6 https://www.filmkorn.org/super8data/database/cameras_list/cameras_beaulieu/beaulieu_6008s.htm (6-70 f/1.4, 77 mm filter); S7 https://kamerastore.com/products/beaulieu-6008s-c-mount (1982 g with 6-70)
- S8 https://www.filmkorn.org/super8data/database/cameras_list/cameras_beaulieu/beaulieu_2008s_automatic.htm (Reglomatic under the lens)
- S9 https://www.filmkorn.org/super8data/database/cameras_list/cameras_beaulieu/beaulieu_2008s_reflexcontrol.htm (Variogon 8-40 f/1.8)
- S10 https://www.filmkorn.org/super8data/database/cameras_list/cameras_pro8mm/pro8mm_classic-pro.htm (8-64 f/1.9, 49 mm, 3 versions)
- S11 https://pro8mm.com/products/angenieux-lens (US$1,495, collimation, Max 8 coverage)
- S12 https://www.pro8mm.com/blogs/blog/pro8mm-announces-lens-services-for-the-new-kodak-super-8-camera
- S13 https://www.manua.ls/beaulieu/4008-zm-ii/manual
- S14 https://www.eoshd.com/comments/topic/26577-is-the-eos-m-the-digital-super-8-camera/page/3/ and /page/4/
- S15 https://www.eoshd.com/comments/topic/26577-is-the-eos-m-the-digital-super-8-camera/page/5/ (6-80 on EOS M)
- S16 https://www.matrixsynth.com/2018/02/eos-m-raw-schneider-optivaron-6-66mm.html
- S17 https://forum.mflenses.com/angenieux-movie-camera-lens-t78340.html (6-80: body motors via gears, image quality)
- S18 https://forum.mflenses.com/schneider-kreuznach-beaulieu-optivaron-6-66mm-1-8-help-t82536.html
- S19 https://re-voir.com/en/pages/angenieux-zoom-f1-4-6-90mm-beaulieu-6008
- S20 https://ausgeknipst.de/en/blogs/questions-and-answers/beaulieu-super-8-cameras-the-big-comparison-of-all-models
- S21 https://www.filmkorn.org/super8data/database/cameras_list/cameras_fuji/fujica_zc_1000.htm (MA-Z 7.5-75 f/1.8, 62 mm, C)
- S22 https://www.super8wiki.com/index.php/Fujica_ZC1000 (search snippets: mirror shutter, 1950-1980 g)
- S23 https://filmshooting.com/forum/viewtopic.php?t=21303 (Fujinon rear cover vs Beaulieu mount)
- S24 https://forum.mflenses.com/angenieux-zoom-macro-1-4-6-90mm-what-is-that-mount-t51794.html (Bauer-mount 6-90)
- S25 https://ft-forum.com/8mm/vbb/forum/8mm-forum/2933-did-anyone-mod-the-optivaron-1-8-6-66mm-for-the-bolex-h8-rx
- S26 https://www.cinelenswiki.com/_export/xhtml/lens:angenieux12-120mmf_2.2
- S27 https://cinelenswiki.com/_export/xhtml/lens:angenieux12-120mmf_2.2viewfinder
- S28 https://www.vintagelensesforvideo.com/angenieux-17-68mm/
- S29 https://cinelenswiki.com/_export/raw/lens:somberthioth16pancinor17-85mmf_2ver2
- S30 https://collections.eastman.org/objects/568830/1886mm-f25-varioswitar-lens ; https://re-voir.com/en/products/objectif-kern-vario-switar-16-100mm-f-1-9
- S31 https://vintagelensesforvideo.com/schneider-18-90mm
- S32 https://indietalk.com/threads/bolex-lens-standard-and-rx-on-non-reflex-and-reflex-cameras.3944/latest (RX prism correction)
- S33 https://www.raspberrypi.com/documentation/accessories/camera.html (IR filter about 1.1 mm)
- S34 https://www.pishop.us/product/raspberry-pi-global-shutter-camera/ (back focus 12.5-22.4 mm)
- S35 eBay search snippets (pages refuse fetch):
  - https://www.ebay.de/itm/156987319366 (Optivaron US$399.99)
  - https://www.ebay.de/itm/187526463664 , /146904979945 , /335964222885 (8-64 US$329-450)
  - https://www.ebay.de/itm/376638762705 (Optivaron 62 mm matte box)
  - https://www.ebay.com/itm/156786293005 and related (12-120 sold/asks)
  - https://www.ebay.de/itm/335533942620 (10-150)
  - https://www.ebay.de/itm/157416633953 (Pan Cinor 70)
  - https://www.ebay.de/itm/286897991611 (Canon 12.5-50)
  - https://ebay.com/b/C-Mount-Manual-Angenieux-Camera-Lenses/3323/bn_25072832 (12.5-75)
- S36 https://www.ebay.de/itm/146403723781 (Angenieux 9-36 K1); https://kamerastore.com/en-eu/products/bolex-h-8-d-mount.oembed (H8 D-mount)
- S37 https://global.canon/en/c-museum/product/cine276.html ; https://www.filmkorn.org/super8data/database/cameras_list/cameras_canon/canon_ds8_zoom.htm
- S38 https://www.super8camera.com/cameras/beaulieu-4008/
- S39 https://global.canon/en/c-museum/product/cine288.html (Scoopic 16M fixed 12.5-75 f/1.8)
