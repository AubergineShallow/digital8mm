# GS8 D2: second-hand hardware on Carousell Singapore (snapshot 2026-10-05, about 23:00 SGT)

A snapshot of what was listed on carousell.sg on 2026-10-05, matched against the D2 BOM (`BOM.md`).

**How it was done**
- 52 searches were run in a browser, the way any visitor would use the site. No login, no seller contact and nothing bought.
- Seven analysis agents matched the listings against the D2 requirements, and a skeptic agent tried to refute every pick.
- The finalists' listing pages were opened to confirm what is actually included.

**Before you rely on it**
- Prices and availability change daily. Confirm with the seller before you travel.
- Seller names and locations are deliberately not recorded here. Each link opens the listing.
- "Brand new" from a shop is new retail, not second-hand.

**Verdict:** second-hand helps most with the **Raspberry Pi 5** and with **tools and test gear**. The camera-specific parts are not on Carousell, so buy them new:
- the Global Shutter camera;
- the X1203;
- the EVF kit and eyepiece;
- the 6 mm C-mount lens;
- the encoder and the switch;
- the battery cells and pack.

## 1. Worth buying (camera parts)

| BOM | Listing | Price | Condition, age | New reference | What was confirmed on the listing page | Ask / check before paying |
|---|---|---|---|---|---|---|
| D2-01 + D2-66 | [Raspberry Pi 5 8GB Complete Starter Kit with Power Supply](https://www.carousell.sg/p/1465023314/) | S$220 | Like new, listed 5 days ago | S$307 (board S$279.18 + 27 W PSU S$28) | Pi 5 **8 GB**; Cytron 27 W USB-C PD supply, 5.1 V 5 A (a Pi 5 type, so it covers D2-66); dual-fan heatsink (**not** the official Active Cooler); micro-HDMI cable; seller says "tested 30 Sept 2026" | Boots and shows 8 GB; no bent pins or burn marks; at first boot no "5 A supply" warning with the Cytron PSU. **Saves about S$87.** |
| D2-02 | [Raspberry Pi5 Active Cooler](https://www.carousell.sg/p/1447325605/) | S$10 | "Brand new", unopened (bought an extra by mistake), 1 month | S$15 | Unopened and unused | Must be the **official** SC1148 (Raspberry Pi logo, retail box): D2's CAD uses its envelope. Pairs with the kit above, which has no official cooler. Saves S$5. |
| D2-01 + D2-02 (alternative) | [Raspberry Pi 5 4GB + Official Active Cooler](https://www.carousell.sg/p/1451760982/) | S$199, or S$219 with the official 27 W PSU | Like new, 2 months | about S$190-220 new for a 4 GB board + cooler + PSU (Pi 5 prices rose in 2025-26; check current retail) | Pi 5 **4 GB** (enough for D2) + genuine official Active Cooler; official PSU +S$20 | Only if you prefer the official PSU and cooler in one deal. The 8 GB kit + S$10 cooler (S$230) is better value. |
| D2-66 (only if you skip the kit) | [Official Raspberry Pi 27W USB-C PSU, UK plug](https://www.carousell.sg/p/1466002592/) | S$18 | Like new, original box, listed 8 h ago | S$28 | Official unit, 5.1/9/12/15 V outputs | Housing and cable undamaged. Saves S$10. |
| D2-67 | [SkyRC B6neo charger](https://www.carousell.sg/p/1331349488/) ("offer S$45") | S$48 | **New stock from a shop**, listed over a year ago | S$53 (BOM) | Exact BOM model; 1-6 cell Li-ion; DC 10-28 V or USB-C PD 12-20 V input; 0.2-10 A | Still available? SkyRC verification label. You also need a 15/20 V USB-C PD charger (a laptop charger works) and an XT60-to-XT30 lead. Small saving, but it's the exact part. |

**Test lens, not the D2 lens:** [Official Raspberry Pi 6 mm CS-mount lens](https://www.carousell.sg/p/1367268824/), S$25, plus an Arducam 6 mm CS lens at S$20 (the HQ camera in that listing is already sold).
- It is a cheap way to bring up the Global Shutter camera while the real lens is still undecided.
- It is **not** a D2 lens option. It is CS-mount (it goes on without the C-CS adapter), and at about 53 g it does not give the grip balance the CAD assumes (about 200 g at the front).

## 2. Worth buying (tools and test gear, if you don't already own them)

| BOM | Listing | Price | Condition, age | New reference | Confirmed | Ask / check |
|---|---|---|---|---|---|---|
| D2-63 iron (best) | [Hakko FX-951 digital station](https://www.carousell.sg/p/1441107252/) | S$200 | Like new, about 1 month | about S$390 | Iron, stand and sponge included | 220-240 V rating plate. Genuine T12 tips (budget S$25-40 for a chisel tip for the 18 AWG pads). |
| D2-63 iron (budget) | [YIHUA 928D](https://www.carousell.sg/p/1465859700/), or [TS100](https://www.carousell.sg/p/1465895254/) | S$25, or S$45 | Like new (5 spare tips) / well used (with adapter) | about S$56 / about S$60 | Temperature control on the handle; standard plug | Heats and holds 350 C. Good enough for D2's 12 joints. |
| D2-64 meter | [Fluke 17B+](https://www.carousell.sg/p/1465242951/) | S$175 | Well used, "tested, fully working", 4 days | about S$279 | Test leads included | **Is the K-type temperature probe included?** (D2 needs temperatures for G-W5/G-W11; a generic probe costs about S$10-20.) Both current fuses OK. Cheaper route: [Fluke 101](https://www.carousell.sg/p/1465918012/) at S$40 + a separate K-type thermometer. |
| D2-65 bench supply | [Tenma 72-2925, 0-30 V 0-10 A](https://www.carousell.sg/p/1406062545/) | S$250 | Lightly used, over 3 months | about S$300+ for a new linear 30 V 10 A (a 30 V 10 A switch-mode supply is about S$110 new) | Digital control, CV/CC, OCP/OVP | **The only working 10 A supply found** (D2 needs 10 A at 5.36 V). At pickup: set 5.36 V with a 10 A limit and check it current-limits into a short. Only worth it if you prefer a linear supply; otherwise buy a new switch-mode one. |
| D2-73 scope | [Siglent SDS1202X-E, 200 MHz, 2 ch](https://www.carousell.sg/p/1464903923/) | S$350 | Used, "rarely used", probes included, 6 days | about S$530 | Probes included | Self-calibration passes; clean square wave on both channels. **Saves about S$180.** |
| D2-68 heat gun | [Black & Decker HG 991](https://www.carousell.sg/p/1465184811/) | S$19 | Lightly used, 5 days | about S$25-40 | | 230 V; fan runs while the heater is on. |

**Optional, only if you have no enclosed printer:** [Bambu Lab P1S](https://www.carousell.sg/p/1452157022/), S$520, like new, bought July 2025, no AMS. New it is about S$675-690.
- Check the print hours and the nozzle.
- Have the seller unbind it from their Bambu account.
- A local FDM print service that does ASA is the other route; send it a sliced 3MF with the modifier meshes, not loose STLs.

## 3. Rejected after checking

| Listing | Why |
|---|---|
| [TTi TSX3510P bench supply, S$400](https://www.carousell.sg/p/1356078495/) | The listing says "power on but freeze ... selling as is ... for spare and repair". |
| [SanDisk Extreme Pro 256GB, S$100](https://www.carousell.sg/p/1465502082/) | It is an SD card (Memory & SD Cards category), not the SDCZ880 USB stick, and D2 has no SD reader in the recording chain. |
| [Raspberry Pi 5 (8gb) kit, S$328](https://www.carousell.sg/p/1465899178/), [Pi 5 + PoE M.2 HAT, S$380](https://www.carousell.sg/p/1450404989/), [Pi 5 + aluminium case, S$390](https://www.carousell.sg/p/1454306821/) | Dearer than buying the parts D2 uses new. |
| Multi-variant Pi 5 listings at S$120-240 (2-3 years old) | Reseller listings with launch-era prices; not second-hand. |
| Fluke 179 S$600, Fluke 175 S$400 | Close to new price for what D2 needs. |
| Kikusui PLZ164WA e-load S$1,450, 5 years old | Overkill and stale. |
| iMAX B6 clones, used Samsung 35E "charger and batteries" | Clone charge-cutoff accuracy; used cells of unknown history. |
| AR glasses (Rokid, Xreal) as an EVF source | Different panel, no HDMI board, bonded optics. |
| Plain KY-040 rotary encoder module S$2 | D2 reads the Adafruit 5880 over I2C at address 0x37. |

## 4. Not on Carousell: buy new

| BOM | Item | Searches that found nothing usable |
|---|---|---|
| D2-05 | Raspberry Pi Global Shutter Camera (S$83.21) | "raspberry pi global shutter camera", "global shutter", "imx296", "sc0926" |
| D2-06 | 6 mm C-mount lens (Kowa LM6HC about S$720 new; Fujinon HF6XA-5M about S$560 new, agent estimates) | "c mount lens", "c-mount", "6mm c mount", "kowa lens", "fujinon c mount", "cctv lens", "cs mount lens", "machine vision lens", "tv lens", "computar". The only C/CS lenses listed were 3.5 mm, 4 mm, 12.5 mm, 25 mm and 50 mm, a varifocal 3.5-8 mm CCTV lens (S$21; partial at best), and lenses bundled with S$600+ industrial cameras. |
| D2-03 | Geekworm X1203 | "geekworm", "x1203", "raspberry pi ups", "pi 5 ups". Also not advisable used: it sits in the charge path. |
| D2-07, D2-08 | HMX039 micro-OLED kit, 0PE039-16X eyepiece | "micro oled display" |
| D2-09 | SanDisk Extreme PRO USB 256 GB (SDCZ880) | One sealed-looking unit at S$150 (shop). Buy it new from an authorised seller: fake and worn flash is common, and it must pass G-W10. **The BOM's S$55.80 estimate is too low; budget about S$100-125.** |
| D2-10, D2-11, D2-12 | Adafruit 5880 encoder, 18/24 rotary switch (kept as a switch), run button | "adafruit rotary encoder", "rotary switch" |
| D2-13, D2-14, D2-14F | Cells/pack, XT30U, fuse | Never second-hand for this build (8.6 A inside a closed body); "xt30" found only Fujifilm X-T30 cameras. |
| D2-75 | DC electronic load of 10 A or more | "electronic load", "dc electronic load", "dc load", "atorch" (only a USB load and a S$1,450 Kikusui) |
| D2-73 (part) | USB-C power meter with logging | One FNB58 at S$55 (shop, new) is about the new price. Buy one new. |

## 5. Rough total if you take the main picks

The four camera picks come to **S$303** (the Pi 5 8 GB kit with its PSU, the official cooler, the B6neo charger, and the S$25 test lens), against about **S$413** new for the same items (S$279.18 + S$28 + S$15 + S$53 + about S$37 for a new 6 mm lens). The saving is about **S$110**, or about S$97 without the test lens.

The four tool picks come to **S$569** (Fluke 17B+, Siglent scope, YIHUA iron, heat gun), against about **S$890** new for comparable gear. The saving is about **S$320**.

Everything else in the BOM is bought new.
