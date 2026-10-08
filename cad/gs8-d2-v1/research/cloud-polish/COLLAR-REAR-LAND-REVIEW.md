# Collar rear-entry correction

The strengthened final-release guard correctly stopped the Fujinon build on one previously unclassified sample:
(0.3, 7.68, 44.51), secondary-screen thickness 0.902 mm. Exact probes at the actual bore edge showed why: the old
Fujinon cone began 0.4 mm after the rear face, and the Kowa cone 0.5 mm after it. Chords 0.03 mm into these free edges
were 0.43 and 0.53 mm. They were unused inner entry feathers, before the band-contact seat, rather than the broad
outer collar wall measured by the existing probe.

The serialized in-memory study compared the original profiles, 1.2 mm lands and 1.6 mm lands for both lenses.
Both thicker options removed the unclassified screen points without lens interference. The fork adopts 1.6 mm,
matching the loaded-feature minimum rather than introducing an exception.

## Exact 1.6 mm trial evidence

- Both profiles: valid single solid, zero additional material, unchanged bounding box and cone/band seat.
- Kowa: entry radius 18.7 -> 19.8 mm, start X 0.8 -> 1.9; seat remains (X 2.8, R 20.7), bore R 21.15.
  Removed 138.085 mm3 from the unused inner edge; lens contact gap and overlap both zero.
- Fujinon: entry radius 17.3 -> 18.5 mm, start X 0.7 -> 1.9; seat remains (X 2.6, R 19.2), bore R 19.65.
  Removed 133.466 mm3; lens contact gap and overlap both zero.
- Seven exact axial probes around each rear edge: 1.63 mm, excluding the declared slit only.
- Production-resolution thin screens: Kowa minimum 1.248 mm; Fujinon 1.247 mm; no unclassified points.
- Existing lens-support checks: no failures.

The final source limits cone drop by the available axial space after a >=1.6 mm cylindrical rear land. It adds
mandatory planned/solid-measured entry checks. The solid check first measures the actual rear bore radius, then
measures axial chords at that real edge; sampling only the new nominal radius would miss a planted old feather.
`test_collar_rear_land.py` preserves that failure case and verifies unchanged outer geometry and lens contact.

## Unbuilt candidate boundary

The data-only Computar band is at flange +1.0 mm, leaving only 1.3 mm from the collar rear face to the seat. A
1.6 mm land cannot fit there without changing the design. No unmeasured band dimension is moved to make it pass.
The analytical candidate remains explicitly a load comparison only; its rear-entry warning is reported, direct
collar export raises a clear error, and promoting it into the production lens table makes the entry check fail.
It needs a separate measured design before any printability or fit claim.

Physical G-LENS, slicer review and G-COL-1 remain open. The final fresh Kowa/Fujinon builds, receipt rehash and
serialized STL/STEP audits must pass after this source correction before the fork's final output is handed over.
