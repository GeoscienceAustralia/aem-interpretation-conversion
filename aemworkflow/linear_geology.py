import os
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
from loguru import logger

from aemworkflow.utilities import get_ogr_path, run_command


def parse_folder_lst(folder_lst_path: str) -> List[Tuple[str, int]]:
    """
    Parse folder.lst returning a list of (shapefile_stem, column_index) tuples.
    Each row format: {stem} {directory} {column_index}
    The directory is ignored — map shapefiles are located by stem in map_data_dir.
    """
    entries = []
    with open(folder_lst_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                stem = parts[0]
                col = int(parts[2])
                entries.append((stem, col))
    return entries


def path_to_point_gmt(path_file: str, output_gmt: str, crs_in: int, crs_out: int = 4283,
                      logger_session=logger) -> None:
    """
    Translate all_pts_i_gmt.awk: convert a .path.txt file into a GMT point file.
    Each row in the path file becomes a point feature with linenum and flib attributes.
    Columns used: col1=linenum, col2=flib, col5=x(easting), col6=y(northing).
    """
    logger_session.info(f"Converting path file to GMT: {Path(path_file).name}")

    with open(output_gmt, 'w') as out:
        out.write("# @VGMT1.0 @GPOINT\n")
        out.write(f"# @Je{crs_in}\n")
        out.write("# @Nlinenum|flib|date|Survey|Company|Status\n")
        out.write("# @Tinteger|integer|integer|string|string|string\n")
        out.write("# FEATURE_DATA\n")

        with open(path_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 6:
                    continue
                linenum = parts[0]
                flib = parts[1]
                x = parts[4]
                y = parts[5]
                out.write(">\n")
                out.write(f"# @D{linenum}|{flib}\n")
                out.write(f"{x} {y}\n")

    logger_session.info(f"GMT point file written: {Path(output_gmt).name}")


def path_gmt_to_shp(gmt_file: str, shp_file: str, crs_in: int, crs_out: int,
                    logger_session=logger) -> None:
    """Convert a GMT point file to a shapefile, reprojecting from crs_in to crs_out."""
    cmd = [
        get_ogr_path(),
        "-f", "ESRI Shapefile",
        "-s_srs", f"EPSG:{crs_in}",
        "-t_srs", f"EPSG:{crs_out}",
        shp_file,
        gmt_file,
    ]
    run_command(cmd)
    logger_session.info(f"Point shapefile written: {Path(shp_file).name}")


def spatial_join(point_shp_dir: str, polygon_shp: str, output_dir: str,
                 logger_session=logger) -> None:
    """
    Translate test_point_poly_join_mgn2.py: spatial join all point shapefiles in
    point_shp_dir against the polygon shapefile, writing *_new.shp to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    polygons = gpd.read_file(polygon_shp)
    logger_session.info(f"Loaded polygon shapefile: {Path(polygon_shp).name} ({len(polygons)} features)")

    for filename in os.listdir(point_shp_dir):
        if not filename.endswith(".shp"):
            continue
        path = os.path.join(point_shp_dir, filename)
        points = gpd.read_file(path)
        points = points.to_crs(polygons.crs)
        joined = gpd.sjoin(points, polygons, how="left", predicate="within")
        new_filename = f"{filename.split('.')[0]}_new.shp"
        joined.to_file(os.path.join(output_dir, new_filename))
        logger_session.info(f"Spatial join written: {new_filename}")


def build_polygon_gmt(joined_shp: str, output_gmt: str, column_index: int,
                      logger_session=logger) -> None:
    """
    Translate lin_geology_5p_clm.awk: read the joined point shapefile (converted
    to GMT), group consecutive points by column_index value, and write 5-point
    rectangular polygons (height=20 image units) to a GMT polygon file.

    The joined shapefile is first converted to GMT format by the caller, then this
    function reads that GMT directly.
    """
    logger_session.info(f"Building polygon GMT from: {Path(joined_shp).name}, column index: {column_index}")

    # Convert joined shapefile to intermediate GMT so we can read @D metadata
    stem = Path(joined_shp).stem
    work_dir = str(Path(joined_shp).parent)
    path_surfgeo_gmt = os.path.join(work_dir, f"{stem}_path_SurfGeo.gmt")

    cmd = [get_ogr_path(), "-f", "GMT", path_surfgeo_gmt, joined_shp]
    run_command(cmd)

    # Parse the GMT and build polygons
    h1 = ""
    h2 = ""
    first = True
    current_key = None
    x_pts: list = []
    header_written = False

    with open(path_surfgeo_gmt, 'r') as fin, open(output_gmt, 'w') as fout:
        def _write_polygon(x_list: list) -> None:
            if not x_list:
                return
            fout.write(f"{x_list[-1]} 0\n")
            fout.write(f"{x_list[-1]} 20\n")
            fout.write(f"{x_list[0]} 20\n")
            fout.write(f"{x_list[0]} 0\n")

        for raw in fin:
            line = raw.strip()
            if not line:
                continue

            parts = line.split()

            if len(parts) >= 2 and parts[1].startswith("@Nlinenum"):
                h1 = line
                continue
            if len(parts) >= 2 and parts[1].startswith("@Tinteger"):
                h2 = line
                continue

            if len(parts) >= 2 and "@D" in parts[1]:
                fields = line.split("|")
                # column_index is 1-based as in the AWK (clm variable)
                key = fields[column_index - 1] if len(fields) >= column_index else None

                if not header_written:
                    fout.write("# @VGMT1.0 @GPOLYGON\n")
                    fout.write("# @NId\n")
                    fout.write(f"{h1}\n")
                    fout.write(f"{h2}\n")
                    fout.write("# FEATURE_DATA\n")
                    header_written = True

                if first:
                    fout.write(">\n")
                    fout.write(f"{line}\n")
                    fout.write("# @P\n")
                    x_pts = [fields[1]]
                    current_key = key
                    first = False
                else:
                    if key == current_key:
                        x_pts.append(fields[1])
                    else:
                        _write_polygon(x_pts)
                        fout.write(">\n")
                        fout.write(f"{line}\n")
                        fout.write("# @P\n")
                        x_pts = [fields[1]]
                        current_key = key

        if x_pts:
            _write_polygon(x_pts)

    logger_session.info(f"Polygon GMT written: {Path(output_gmt).name}")


def find_map_data_dir(input_directory: str) -> str:
    """Return the map_data subfolder path, case-insensitive. Empty string if not found."""
    parent = Path(input_directory)
    for child in parent.iterdir():
        if child.is_dir() and child.name.lower() == "map_data":
            return str(child)
    return ""


def run_linear_geology(input_directory: str, output_directory: str, crs: str,
                       logger_session=logger) -> bool:
    """
    Run the full linear geology pipeline for all map datasets.

    Expected input_directory structure:
        *.path.txt           — flight line geometry files
        map_data/ (or Map_data/) — polygon shapefiles; optionally folder.lst

    If folder.lst is present it controls which shapefiles are processed and which
    column index to use per dataset. If absent, all *.shp files in map_data/ are
    processed using the default column index (6).

    Output goes to output_directory/lin_geo/{map_stem}/ per dataset.
    Returns True on success, False on any failure.
    """
    DEFAULT_COLUMN = 6

    try:
        crs_in = int(crs)
        map_data_dir = find_map_data_dir(input_directory)

        if not map_data_dir:
            logger_session.error("No map_data folder found in input directory.")
            return False

        folder_lst = os.path.join(map_data_dir, "folder.lst")

        if Path(folder_lst).is_file():
            entries = parse_folder_lst(folder_lst)
            if not entries:
                logger_session.error("folder.lst is empty or could not be parsed.")
                return False
            logger_session.info(f"Using folder.lst: {len(entries)} dataset(s) defined.")
        else:
            shp_files = sorted(Path(map_data_dir).glob("*.shp"))
            if not shp_files:
                logger_session.error("No shapefiles found in map_data directory.")
                return False
            entries = [(s.stem, DEFAULT_COLUMN) for s in shp_files]
            logger_session.warning(
                f"folder.lst not found — processing {len(entries)} shapefile(s) with default column {DEFAULT_COLUMN}."
            )

        path_files = sorted(Path(input_directory).glob("*.path.txt"))
        if not path_files:
            logger_session.error("No .path.txt files found in input directory.")
            return False

        lin_geo_root = os.path.join(output_directory, "lin_geo")

        # Stage 1: convert all path files to point GMT + SHP
        point_shp_dir = os.path.join(lin_geo_root, "_point_shp")
        os.makedirs(point_shp_dir, exist_ok=True)

        for path_file in path_files:
            stem = path_file.stem.split(".")[0]
            gmt_out = os.path.join(point_shp_dir, f"{stem}.gmt")
            shp_out = os.path.join(point_shp_dir, f"{stem}.shp")
            path_to_point_gmt(str(path_file), gmt_out, crs_in, logger_session=logger_session)
            path_gmt_to_shp(gmt_out, shp_out, crs_in, 4283, logger_session=logger_session)

        # Stage 2 + 3: per map dataset
        for map_stem, col_idx in entries:
            polygon_shp = os.path.join(map_data_dir, f"{map_stem}.shp")
            if not Path(polygon_shp).is_file():
                logger_session.warning(f"Map shapefile not found, skipping: {polygon_shp}")
                continue

            logger_session.info(f"Processing map dataset: {map_stem}")

            joined_dir = os.path.join(lin_geo_root, map_stem, "joined")
            poly_dir = os.path.join(lin_geo_root, map_stem, "polygons")
            os.makedirs(joined_dir, exist_ok=True)
            os.makedirs(poly_dir, exist_ok=True)

            # Stage 2: spatial join
            spatial_join(point_shp_dir, polygon_shp, joined_dir, logger_session=logger_session)

            # Stage 3: build polygon GMT + SHP per joined file
            for joined_shp in sorted(Path(joined_dir).glob("*_new.shp")):
                nm = joined_shp.stem.replace("_new", "")
                poly_gmt = os.path.join(poly_dir, f"{nm}_{map_stem}_pl.gmt")
                poly_shp = os.path.join(poly_dir, f"{nm}_{map_stem}.shp")

                build_polygon_gmt(str(joined_shp), poly_gmt, col_idx, logger_session=logger_session)

                cmd = [get_ogr_path(), "-f", "ESRI Shapefile", poly_shp, poly_gmt]
                run_command(cmd)
                logger_session.info(f"Polygon shapefile written: {Path(poly_shp).name}")

        logger_session.info("Linear geology pipeline completed.")
        return True

    except Exception as e:
        logger_session.error(f"Linear geology pipeline failed: {e}")
        return False
