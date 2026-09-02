# Changelog

## [Version 3.0.0] 

### What changed and why

Version 3 reworks the export and validation stages of the workflow to support new output formats (3D shapefiles, GA Portal / Earth Sciences format) and stricter interpretation validation against confidence, contact-type, and interpretation-basis lookups. Export outputs are now consolidated into a single `export/` directory instead of being written in `SORT/`.

All new CLI commands and usage examples are documented in [README.rst](README.rst).

### New export outputs

- **CSV export (`--csv`)**: functionally the same as v2's EGS export (same CSV column layout), just renamed and relocated. Produces a single `export/output.csv` combining all survey lines, instead of `SORT/output.egs`.
- **MDC/MDCH export (`--mdc`/`--mdch`)**: now also produces an individual `export/<line>.mdc`/`.mdch` file per survey line, in addition to the combined `export/output.mdc`/`.mdch` file (which was the only output in v2).
- **GA Portal / Earth Sciences export (`--es`)**: new format for publishing interpretation lines to the GA Portal / EarthSci viewer. For each survey line, produces `export/<line>.pl` (GOCAD PLine geometry) and `export/<line>.xml` (an EarthSci layer definition referencing the `.pl` file, with display name, coordinate system, and data cache path). A combined `export/dataset.xml` is also produced, listing every generated `.xml` layer under a single dataset so the whole set can be loaded into EarthSci together.
- **3D shapefile export (`--3d`)**: new format producing an individual 3D ESRI shapefile (`export/<line>.shp`, `.shx`, `.dbf`, `.prj`) per survey line, projected to the CRS given via `--crs` (default EPSG:28349). Unlike the existing 2D shapefile export (`ZF_SHP/<line>_zf.shp`), these shapefiles carry 3D geometry.

### New validation outputs

- `Confidence_validation_summary_{date}.txt`, `Contact_type_validation_summary_{date}.txt`, `Interpretation_basis_validation_summary_{date}.txt`, `Comma_validation_summary_{date}.txt`, and `error_list.log` are now produced by `validate`.

### Breaking changes

- **`validate` CLI command** now requires three additional options: `--c` (confidence lookup file), `--ct` (contact-type lookup file), `--ib` (interpretation-basis lookup file). Existing invocations without these will fail with a missing-option error.
- **`export` CLI command**: the `--egs` flag has been removed and replaced by `--csv`, which produces the same CSV output but writes to `export/output.csv` instead of `SORT/output.egs`.
- **`export` CLI command with `--es`** (new flag): produces the GA Portal / Earth Sciences output — a per-line `export/<line>.pl`/`.xml` pair, plus a combined `export/dataset.xml` listing every generated layer.
- **`export` CLI command with `--3d`** (new flag): produces a per-line 3D ESRI shapefile (`export/<line>.shp/.shx/.dbf/.prj`).
- **`export` CLI command with `--mdc`/`--mdch`**: now also writes an individual `export/<line>.mdc`/`.mdch` file per survey line, in addition to the combined `export/output.mdc`/`.mdch` file (which was the only output in v2). It now take an additional required parameter, the split-file path.
- **`validation` CLI command now requires three additional positional arguments: `confidence_lookup`, `contact_type_lookup`, `interpretation_basis_lookup`.
- **Output file locations**: export outputs (CSV, MDC/MDCH, Earth Sciences, 3D shapefiles) are now written to a new `export/` directory instead of `SORT/`. Scripts that read output from `SORT/` will need to look in `export/` instead.
- **MDC/MDCH metadata field changes**: `*metadata*Line` renamed to `*metadata*SURVEY_LINE`; `*metadata*BoundaryNm` removed; `*metadata*Organization` corrected to `*metadata*Organisation`; `OvrStrtCod`/`UndStrtCod` renamed to `OvrStratNo`/`UndStratNo`; `WithinType` removed; new fields added: `OverAge`, `UnderAge`, `ContactTyp`, `HydStrtType`, `HydStrConf`, `BOMNAFUnt`, `BOMNAFNo`, `Date`. These label names are not cosmetic — in v2 several metadata header labels did not line up with the data value actually written under them (e.g. the `BoundaryNm` label was printing what was really the `BoundConf` value, one field out of place); the field list above reflects the corrected label/data alignment, so v2 output produced under the old labels should not be assumed correct and downstream consumers should re-derive any values they depend on from the field position, not the old label name.
- **Validation summary file renamed**: `AEM_validation_summary_{date}.txt` is now `ASUD_validation_summary_{date}.txt`.

### New required input files

- `validate` now requires a confidence lookup file (`--c`), a contact-type lookup file (`--ct`), and an interpretation-basis lookup file (`--ib`), in addition to the existing ASUD file (`--a`).
- These three lookup files will be made available for download from the eCat dependencies page.


### Fixed

- `conversion_zedfix_gmt_to_srt` now clears stale per-line output files (`met.bdf`, `{nm}_*.srt`, `{nm}_hdr.hdr`) before regenerating them, preventing old and new data from mixing when re-running conversion against a directory with leftover files from a prior run.
- `validation_qc_units` previously appended to `asud_nf.asc` across runs, causing duplicate accumulation; it now truncates the file at the start of each run.
- `validation_qc_units` previously logged a mismatch on all of the over/under/within unit checks whenever any single one failed; each of the three pairs (`OvrStrtUnt`/`OvrStratNo`, `UndStrtUnt`/`UndStratNo`, `WithinStrt`/`WithinStNo`) is now checked and logged independently.
- `validation_qc_units` ASUD lookup and summary logic has changed for blank strat unit/number fields. Each strat name/number pair is now evaluated as follows: if both the strat unit and strat number are blank, the pair is skipped entirely (no ASUD lookup, no entry in the summary); if only one of the pair is blank, the pair is still checked and reported as "no match"; if both are populated, the pair is checked against ASUD as normal and reported as matched or no match. Previously, blank pairs could still be counted in the `ASUD_validation_summary`, even though no ASUD lookup was actually performed for them. The `ASUD_validation_summary` now only reflects strat unit/number pairs that were actually checked against ASUD, so summary counts from v2 and v3 are not directly comparable.
- Fixed CLI export skipping the first survey line.
- Fixed MDC/MDCH metadata headers being misaligned with the data values written beneath them (e.g. `*metadata*BoundaryNm` was previously printing the `BoundConf` value); headers now correctly correspond to the field written on each line, and several previously-missing fields (`ContactTyp`, `HydStrtType`, `HydStrConf`, `BOMNAFUnt`, `BOMNAFNo`, `OverAge`, `UnderAge`, `Date`) are now included.

### Migration guide

1. Update `validate` commands to provide the new mandatory lookup files using `--c`, `--ct`, and `--ib`.

2. Replace `--egs` with `--csv` for the equivalent CSV export.

3. Use `--es` if GA Portal / Earth Sciences output is required.

4. Use `--3d` for per-line 3D shapefile output. Specify `--crs` if a CRS other than the default EPSG:28349 is required.
