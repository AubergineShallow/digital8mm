# GS8 D2: parfocal C-mount zooms (machine vision, CCTV, broadcast)

Research date 2026-10-06. Web research only; nothing bought or contacted. Items marked [unconfirmed] are not backed by a maker document.
Conventions: IMX296 is 5.02 x 3.75 mm, 6.27 mm diagonal, crop 6.90. "eq" means the 35 mm-equivalent focal length.
Pixel Nyquist is 145 lp/mm. Prices convert at 1.28 SGD/USD; EUR is taken as about 1.08 USD [assumption].
Baseline for comparison: the D2 default Kowa LM6HC 6 mm (41 mm eq, 55.2 deg diagonal, 215 g).

## 1. Camera-side facts (Raspberry Pi Global Shutter Camera)

- **No published maximum rear protrusion.** The product brief and the mechanical drawing do not give one. They give:
  - lens back focus "Adjustable (12.5-22.4mm)";
  - CS mount, plus a C-CS adapter for C mount;
  - a 6.3 mm sensor diagonal;
  - the drawing shows a 1-32UN mount and a ø22.4 mm inner opening in the mount.
- **The ring can only lengthen the back focus.** C lenses sit at 17.5-27.4 mm with the 5 mm adapter fitted. To track parfocal, a C lens is set at exactly its own flange distance (nominally 17.526 mm). A lens whose ideal distance is shorter than 17.526 mm needs a spacer thinner than 5 mm instead of the stock adapter.
- **The IR filter sits in the lens-mount assembly.** On the HQ camera, which uses the same mount assembly as the GS, the filter (about 9 x 9 x 1.1 mm) is attached to the back of that assembly, just above the sensor (RPi forum t=274926).
- **A known-safe clearance figure.** Raspberry Pi's own recommended 6 mm CS lens has a back focal length of 7.53 mm (RPi camera docs). Its rear glass therefore sits about 5.0 mm behind the CS flange. With the C-CS adapter, that is about 10 mm behind a C flange.
  - Every lens below has its rear glass at most 6.1 mm behind the C flange, so all should clear the filter.
  - Measure the actual filter depth with a depth gauge before buying anything protruding over 6 mm [unconfirmed].
- **Zoom vs varifocal by maker definition.**
  - Computar's parent CBC Co. defines it in patent US9544477B2: the zoom lens "is configured not to move a focus (image forming) position even though a zooming ... operation is performed". The varifocal adjusts zoom and focus units individually.
  - Fujinon's CCTV catalog also lists "Vari-Focal" and "Zoom" as separate lens types.
  - So a maker-labelled "Manual Zoom" (Computar, Ricoh/Pentax, Kowa LMZ, ViewZ "Manual Zoom") is parfocal by design, provided the flange distance is right. None of these makers prints the word "parfocal" on these CCTV models; only Navitar does.
- **No wide parfocal zoom covers the full sensor.** Nothing in production or in common surplus covers 1/2" or larger and starts wider than **8 mm (55 mm eq)**. The only wider true zooms found are 1/3"-format CS lenses: 5.7 mm and 6.5 mm. Their 6.0 mm image circle is smaller than the 6.27 mm diagonal, so the corners may vignette.

## 2. Parfocal (true zoom) candidates

Abbreviations: M/M/M = manual zoom/focus/iris. Rear = where the rear glass sits relative to the C flange, from back focal length, plus the drawing protrusion where one exists. MOD = minimum object distance.

| # | Model | f (eq) / max f-no. | Format | Control | Mass | Dia x L (mm) | Rear | MOD | Res | Status / price |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Computar H6Z0812** (= Edmund #53-152) | 8-48 (55-331) / 1.2 | 1/2" (ø8) | M/M/M | 305 g | 51.75 x 97 | glass 6.1 mm behind; drawing about 6 mm protrusion, rear tube ø22.2 | 1.2 m | analog-era, no MP rating | Discontinued at Computar ("limited quantity"). EO new US$645 (S$826). eBay used US$47-100 (S$60-128); open-box US$175-185 |
| 2 | **Computar M6Z1212-3S** (= Edmund #53-153) | 12.5-75 (86-518) / 1.2 | 2/3" (ø11) | M/M/M + locks | 483 g | 59.5 x 114.5 | glass 2.1 mm behind; 4 mm thread | 1.0 m | **3 MP** | Discontinued at Computar. EO US$705 (S$902), 8 in stock on EO India. Used about US$85 (S$109) |
| 3 | **Kowa LMZ68M** | 8-48 (55-331) / **1.0** | 1/2" (ø8) | M/M/M + macro lever | **280 g** | 48 x 97.3 | glass 3.0 mm behind | 0.5 m (0.01 m macro) | 100/60 lp/mm | Status and price not found [unconfirmed]; sibling LMZ69M is discontinued |
| 4 | Kowa LMZ69M | 11.5-69 (79-476) / 1.4 | 2/3" | M/M/M + macro | 300 g | 48 x 102.7 | glass 0.4 mm in front of flange | 0.5 m | 100/60 lp/mm | Discontinued |
| 5 | **ViewZ VZ-B6X8M** | 8-48 (55-331) / 1.0 | 1/2" | M/M/M | 380 g | 58 x 91.7 | n/a | 1.0 m (0.3 m close-focus) | none stated | In production. US$317 (S$406); molded body US$276 (S$353) |
| 6 | ViewZ VZ-C6X11M | 11.5-69 (79-476) / 1.4 | 2/3" | M/M/M | 410 g | 58 x 107.8 | n/a | n/a | none stated | US$286 (S$366). Same spec as LMZ69M [same optics unconfirmed] |
| 7 | ViewZ VZ-C6X11DC-MP | 11-66 (76-455) / 1.8 | 2/3" | manual zoom; iris listed as manual despite "DC" in name [unconfirmed] | n/a | n/a | n/a | n/a | 3.6 MP | US$724 (S$927) |
| 8 | **Ricoh (Pentax/Cosmicar) FL-CC6Z1218-VG** (and A-VG with locks; C6Z1218) | 12.5-75 (86-518) / 1.8 | 2/3" | M/M/M | 320 g | 51 x 90 | **glass 0.9 mm in front of flange** | 1.0 m | none stated | Ricoh ended all security-lens sales 31 Mar 2019. Used: generic "12.5-75 f/1.8" US$60; one Pentax asking €370. Motorized C6Z1218M3 also made |
| 9 | Pentax/Cosmicar H6Z810 (C60812) | 8-48 (55-331) / 1.0 | 1/2" | M/M/M | 440 g | 58 x 100 | n/a | 1.2 m | none stated | Vintage. eBay US$55-200 (S$70-256) |
| 10 | Rainbow H6X8 | 8-48 / 1.0 | 1/2" | M/M/M | n/a | n/a | n/a | n/a | none stated | Vintage, seen new-in-box on eBay.de [weight unconfirmed] |
| 11 | Fujinon H6x12.5R | 12.5-75 (86-518) / 1.2 (T1.2) | 2/3" [unconfirmed] | M/M/M + zoom rod | n/a | n/a | **deep**: a dealer notes the "rear mount has been modified to clear most C-Mount cameras" | n/a | broadcast-era | eBay US$85-100 (S$109-128); Du-All US$350 (S$448) |
| 12 | Canon V6x16 | 16-100 (110-690) / 1.9 | 1" | M/M/M | 620 g | 62.8 x 132.6 | n/a | n/a | tube-era | Used only; an eBay seller calls it "Parfocal" |
| 13 | Navitar Zoom 7000 / 7000-2 (Thorlabs MVL7000 = rebrand; Kowa LMZ45T3 is similar, 595 g) | 18-108 or 18.6-111 (124-766) / 2.5 | 2/3" | M/M/M | 840 g | 67 x 178.2 | glass 8.3 mm in front of flange | 0.127 m | 100/60 lp/mm, 5 µm pixels | 7000-2 new on quote. Old 7000 used US$90-149 (S$115-191). **Maker: "Parfocal across entire zoom range"** |
| 14 | Computar T6Z5710AIDC | **5.7**-34.2 (39-236) / 1.0 | **1/3" CS** | manual zoom/focus, DC auto-iris | 440-490 g | 68.5 x 76.3 x 82.5 box [may be the motor body] | n/a | 1.2 m | none stated | Not on Computar's site; likely discontinued [unconfirmed] |
| 15 | ViewZ VZ-A6X65M | 6.5-39 (45-269) / 1.4 | 1/3" CS | M/M/M | n/a | n/a | n/a | n/a | none stated | Price not found |
| 16 | Kurokesu L067-FZA-12Z120-C | 12-120 (83-828) / 1.8 | 1/1.8" | M/M/M | n/a | n/a | n/a | n/a | n/a | €169 (about S$234). **Parfocal not stated [unconfirmed]** |

Motor-driven true zooms exist but are heavy:

- **Computar:** H6Z0812M/MS/MSP/AMS (8-48, about 400-440 g) and H10Z1218M/MS/MSP (12-120 1/2", 500-670 g).
- **Kowa:** LMZ7527 (7.5-127 1/2", 580 g) and LMZ0812-IR (8-120 1/2", 780 g).
- **Fujinon:** D8x7.8HA (1/2" CS, 7.8-62 f/1.2) and A4x7.5BMD-D28 (2/3" 7.5-30 "graphic lens", discontinued; mount unconfirmed).

## 3. Controls: what powered lenses imply

- **Auto-iris lenses close their iris when unpowered.** This covers both "AI"/video and "DC" types. Fujinon's catalog says that "When power is turned off iris will automatically close" (decoded from its D8x7.8HA page).
  - A video-type iris needs the camera's video signal.
  - A DC-type iris needs a drive voltage from the supervisor.
  - Prefer the plain manual-iris versions: H6Z0812 (not AIDC or AIVD), VZ-B6X8M, LMZ68M, FL-CC6Z1218-VG.
- **Motorized zooms run their zoom and focus motors on DC 6-12 V.** For Kowa, the maximum is 60 mA and an end-to-end move takes about 7-14 s (Kowa CCTV overview, wiring page).
  - Computar's 3-motor versions (M, MS, MSP) also motorize the iris.
  - The preset ("P") versions add potentiometers for position feedback.
  - None of these is light enough for D2's balance.

## 4. Image quality on 3.45 µm pixels

- **Only two families are rated for small pixels.**
  - Computar M6Z1212-3S is rated 3 MP on 2/3" (2048 x 1536 on 8.8 mm is about 4.3 µm pitch), the closest match to 3.45 µm.
  - ViewZ's 3.6 MP 11-66 is the other.
  - Kowa's LMZ68M/69M are rated 100 lp/mm centre and 60 lp/mm corner. That is below the 145 lp/mm pixel Nyquist, but adequate for 1456 x 1088 video.
- **Expect softness wide open on the analog-era lenses.** This applies to the H6Z0812, Pentax/Ricoh, Rainbow, Fujinon and Canon. Stop down to about f/2.8-4 [general expectation, unconfirmed per lens].
- **Broadcast 2/3" zooms built for 3-CCD prism blocks lose sharpness on a single sensor.** It is not known whether the Fujinon H6x12.5R is prism-corrected [unconfirmed]. The CCTV models above are for single sensors.

## 5. Singapore availability

- Three web searches for Carousell SG (C-mount, TV zoom, 8-48 or 12.5-75, Computar, Fujinon, Cosmicar) returned **no matching listing**. Carousell was not fetched, per instructions.
- Edmund Optics runs an SG storefront (edmundoptics.com.sg), so #53-152 and #53-153 should be orderable to Singapore. The SGD price was not checked.
- Kamerastore (EU) lists the Pentax 12.5-75 f/1.8 (300 g, 52 x 98, MOD 1 m) and the 8-48 f/1.0 (440 g), both currently sold out.

## 6. Ranked shortlist for GS8 D2

1. **Computar H6Z0812, manual-iris version** (or Edmund #53-152).
   - It is the widest true zoom that covers the sensor: 8 mm, 55 mm eq.
   - It is parfocal under Computar's own zoom definition, all-manual, and 305 g (about 1.5x the 200 g balance).
   - Rear glass sits 6.1 mm behind the flange, inside RPi's own 5 mm/10 mm precedent.
   - It is cheap used (US$47-100, S$60-128) or US$645 new.
2. **Kowa LMZ68M.**
   - It is the lightest true zoom found (280 g), at 8-48 mm f/1.0.
   - It has a 0.5 m MOD plus macro, and its 100 lp/mm rating is published.
   - Rear glass sits about 3 mm behind the flange.
   - Its status and price still need to be found, and parfocal is not stated by Kowa [unconfirmed].
3. **ViewZ VZ-B6X8M.**
   - It is the only 8-48 mm f/1.0 manual zoom confirmed in production, at US$317 (S$406), or US$276 (S$353) for the molded body.
   - It is heavier at 380 g, and its rear dimension is unknown.
4. **Ricoh/Pentax FL-CC6Z1218-VG** (12.5-75 f/1.8).
   - It is the best long zoom for balance and clearance: 320 g, with the rear glass 0.9 mm in front of the flange.
   - Used copies are cheap, but the wide end is only 86 mm eq.
5. **Computar M6Z1212-3S** (12.5-75 f/1.2, Edmund #53-153).
   - It is the only 3 MP-rated parfocal C zoom found, so it is the best match for 3.45 µm pixels.
   - It is 483 g (2.4x the balance) and 86 mm eq at the wide end. It costs US$705 (S$902) new or about US$85 used.

Cheaper used alternatives for slot 1 or 3: Pentax/Cosmicar H6Z810 (C60812), 8-48 f/1.0, 440 g, US$55-200; or Rainbow H6X8.

Only if a wider wide end beats coverage: Computar T6Z5710 (5.7 mm, 39 mm eq). It is 1/3" CS, so the corners may vignette. It is DC-iris and needs a driver, and it weighs 440 g or more.

## 7. Checked and ruled out (not parfocal C zooms)

- **Tamron M13VM / M118VM series:** varifocal ("VM" in the name); the maker sells them as varifocal.
- **Tokina TVR series** (e.g. TVR1020HD-IR): varifocal.
- **Theia SL183 and TL410:** varifocal per Theia; the TL410 adds motorized zoom and focus.
- **Goyo GMZ series** (e.g. GMZ16100MCN): the maker calls it a "Manual Varifocal Zoom".
- **Computar M3Z1228C-MP** (12-36 f/2.8 2/3"): varifocal. Its focus range differs between wide (0.05 m) and tele (0.2 m).
- **Computar MLH-10X** (13-130 f/5.6): macro only, focusing 0.15-0.45 m. B&H mislabels it "Varifocal".
- **Computar TEC-M55:** macro/telecentric; excluded per brief.
- **Kowa LMVZ series** (LMVZ990, LMVZ4411, LMVZ166HC, etc.): varifocal per Kowa's catalog.
- **Kowa LMZ50M** (8.5-90): a macro zoom for 1/3" only.
- **Fujinon DV and YV series:** varifocal ("V" in the code).
- **Fujinon CF…ZA/HA and HF…HA:** fixed focal; "ZA" is a series code, not zoom.
- **Navitar Zoom 6000 and 12X, and Edmund VZM:** macro zoom systems with limited working distance.
- **B&H titles M6Z1212-3S and Kowa LMZ7527 as "Varifocal".** This is a retailer mislabel; trust the maker's "Zoom" naming.
- **Spacecom:** only fixed C lenses found (e.g. JHF35M); no C-mount zoom found.
- **Schneider:** no C-mount parfocal MV zoom found.
- **Edmund and Thorlabs:** their zooms are rebrands (Computar, Navitar).
- **Canon J-series broadcast zooms:** B4 mount. A J6x12 was seen sold "no mount".
- **Out of scope here (cine, not CCTV):** Single-8/Super-8 C-mount cine zooms such as the Fujinon EBC 7.5-75 f/1.8 may cover 6.27 mm and start wider [unconfirmed]. Worth a separate cine-lens check.

## Sources

Camera:
- RPi GS product brief: https://pip-assets.raspberrypi.com/categories/810-raspberry-pi-global-shutter-camera/documents/RP-008196-DS-1-gs-camera-product-brief.pdf
- RPi GS mechanical drawing: https://pip-assets.raspberrypi.com/categories/810-raspberry-pi-global-shutter-camera/documents/RP-008195-DS-1-gs-camera-mechanical-drawing.pdf
- RPi camera docs: https://www.raspberrypi.com/documentation/accessories/camera.html
- IR filter location: https://forums.raspberrypi.com/viewtopic.php?t=274926

Zoom vs varifocal definitions:
- CBC patent: https://patents.google.com/patent/US9544477
- Fujinon 2012 CCTV catalog: https://www.rmaelectronics.com/content/Fujinon-Lens-PDF/FUJINON%202012%20CCTV%20lens%20catalog.pdf

Computar:
- H6Z0812 spec: https://computarganz.s3.amazonaws.com/Computar+Active+Resources/H6Z0812+Spec.pdf
- H6Z0812 product page: https://www.computar.com/products/h6z0812
- M6Z1212-3S spec: https://computarganz.s3.amazonaws.com/Computar+Active+Resources/M6Z1212-3S+Spec.pdf
- M6Z1212-3S product page: https://www.computar.com/products/m6z1212-3s
- Variant weights: https://www.123securityproducts.com/h6z0812g.html
- Used prices: https://www.ebay.de/itm/396520278651 and https://www.ebay.de/itm/116665260266
- T6Z5710: https://www.123securityproducts.com/t6z5710aidcg.html
- MLH-10X: https://machinevisiondirect.com/products/computar-mlh-10x
- M3Z1228C-MP: https://www.123securityproducts.com/m3z1228c-mpg.html

Edmund Optics:
- #53-152: https://www.edmundoptics.com/p/8-48mm-fl-6x-manual-zoom-video-lens/10695/
- #53-153: https://edmundoptics.in/p/125-75mm-fl-6x-manual-zoom-video-lens/10696
- Family page: https://www.edmundoptics.ca/f/manual-zoom-imaging-lenses/11363/

Kowa:
- LMZ68M: https://pyramidimaging.com/specs/Kowa/LMZ68M.pdf
- LMZ69M: https://pyramidimaging.com/specs/Kowa/LMZ69M.pdf
- Kowa CCTV lenses overview: https://cdn.graftek.com/system/files/12875/original/Kowa_CCTV_Lenses_Overview.pdf

Ricoh/Pentax:
- FL-CC6Z1218: https://adept.net.au/lenses/ricoh/pdf/FL-CC6Z1218-VG.pdf
- Pentax 12.5-75 f/1.8: https://kamerastore.com/en-us/products/pentax-12-5-75mm-f1-8-cctv-zoom-c-mount
- Pentax 8-48 f/1.0: https://kamerastore.com/products/pentax-8-48mm-f1-cosmicar-tv-zoom-c-mount
- H6Z810 listing: https://www.ebay.de/itm/357691762968

ViewZ:
- Lens index: https://viewzusa.com/lens/
- VZ-B6X8M: https://www.123securityproducts.com/vz-b6x8m.html
- VZ-C6X11M: https://www.123securityproducts.com/vz-c6x11m.html
- VZ-A6X65M: https://www.123securityproducts.com/products/accessories/cctv-lenses/manual-zoom-lenses/vz-a6x65m.html

Fujinon:
- H6x12.5R at Du-All: https://duallcamera.com/products/fujinon-12-5-70mm-t1-2-tv-zoom-lens-h6x12-5r-c-mount-s-998499
- H6x12.5R on eBay: https://www.ebay.de/itm/306600562265
- A4x7.5BMD: https://www.adorama.com/fua4x75bmd28.html

Navitar:
- Zoom 7000-2: https://www.navitar.com/products/imaging-solutions/zoom-7000-2-macro-lens
- Zoom 7000-2 store: https://store.navitar.com/zoom-7000-2-macro-lens/
- Zoom 7000 used: https://www.ebay.com/itm/277202856420

Others:
- Canon V6x16: https://www.ebay.de/itm/236478667187
- Rainbow H6X8: https://www.ebay.de/itm/275799902642
- Kurokesu L067: https://www.kurokesu.com/shop/lenses/L067-FZA-12Z120-C
- Theia: https://www.vision-systems.com/cameras-accessories/article/16745674/theia-introduces-c-mount-ultra-wide-undistorted-varifocal-lens
- Goyo GMZ: https://goyonorthamerica.com/lenses/gmz16100mcn/
- Tokina TVR: https://www.bhphotovideo.com/c/product/869731-REG/Tokina_TVR1020HD_IR_1_1_8_3_MP.html
