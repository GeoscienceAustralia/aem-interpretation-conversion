import os
from pathlib import Path
from typing import Dict, List, Tuple

import geopandas as gpd
from loguru import logger

from aemworkflow.utilities import get_ogr_path, run_command


def get_map_data_defaults(map_data_dir: str) -> Dict[str, int]:
    """Return {stem: 1} for every .shp in map_data_dir."""
    return {shp.stem: 1 for shp in sorted(Path(map_data_dir).glob("*.shp"))}


def path_to_point_gmt(path_file: str, output_gmt: str, logger_session=logger) -> None:
    """
    Translate all_pts_i_gmt.awk: convert a .path.txt file into a GMT point file.
    Uses cols 7,8 (geographic lon/lat in EPSG:4283) — these are already in the
    target CRS and match the polygon shapefiles, avoiding projection zone errors.
    Columns: col1=linenum, col2=flib, col7=longitude, col8=latitude.
    """
    logger_session.info(f"Converting path file to GMT: {Path(path_file).name}")

    with open(output_gmt, 'w') as out:
        out.write("# @VGMT1.0 @GPOINT\n")
        out.write("# @Je4283\n")
        out.write("# @Nlinenum|flib|date|Survey|Company|Status\n")
        out.write("# @Tinteger|integer|integer|string|string|string\n")
        out.write("# FEATURE_DATA\n")

        with open(path_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 8:
                    continue
                linenum = parts[0]
                flib = parts[1]
                lon = parts[6]
                lat = parts[7]
                out.write(">\n")
                out.write(f"# @D{linenum}|{flib}\n")
                out.write(f"{lon} {lat}\n")

    logger_session.info(f"GMT point file written: {Path(output_gmt).name}")


def path_gmt_to_shp(gmt_file: str, shp_file: str, logger_session=logger) -> None:
    """Convert a GMT point file to a shapefile (no reprojection needed)."""
    run_command([get_ogr_path(), "-f", "ESRI Shapefile", shp_file, gmt_file])
    logger_session.info(f"Point shapefile written: {Path(shp_file).name}")


def spatial_join(point_shp_dir: str, polygon_shp: str, output_dir: str,
                 logger_session=logger) -> None:
    """
    Translate test_point_poly_join_mgn2.py: spatial join all point shapefiles in
    point_shp_dir against polygon_shp, writing *_new.shp to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    polygons = gpd.read_file(polygon_shp)
    logger_session.info(f"Loaded polygon shapefile: {Path(polygon_shp).name} ({len(polygons)} features)")

    for filename in os.listdir(point_shp_dir):
        if not filename.endswith(".shp"):
            continue
        points = gpd.read_file(os.path.join(point_shp_dir, filename))
        points = points.to_crs(polygons.crs)
        joined = gpd.sjoin(points, polygons, how="left", predicate="within")
        new_filename = f"{filename.split('.')[0]}_new.shp"
        joined.to_file(os.path.join(output_dir, new_filename))
        logger_session.info(f"Spatial join written: {new_filename}")


def build_polygon_gmt(joined_shp: str, output_gmt: str, column_index: int,
                      logger_session=logger) -> None:
    """
    Translate lin_geology_5p_clm.awk: group consecutive points by the value at
    column_index and write 5-point rectangular polygons (height=20 image units).
    """
    logger_session.info(f"Building polygon GMT: {Path(joined_shp).name}, col={column_index}")

    stem = Path(joined_shp).stem
    path_surfgeo_gmt = os.path.join(str(Path(joined_shp).parent), f"{stem}_path_SurfGeo.gmt")
    run_command([get_ogr_path(), "-f", "GMT", path_surfgeo_gmt, joined_shp])

    h1 = h2 = ""
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
    for child in Path(input_directory).iterdir():
        if child.is_dir() and child.name.lower() == "map_data":
            return str(child)
    return ""


def run_linear_geology(input_directory: str, output_directory: str,
                       entries: List[Tuple[str, int]],
                       logger_session=logger) -> bool:
    """
    Run the full linear geology pipeline.

    Args:
        input_directory: contains *.path.txt and map_data/ folder
        output_directory: root output dir; results go under lin_geo/
        entries: list of (shapefile_stem, column_index) from the UI selection
    """
    try:
        map_data_dir = find_map_data_dir(input_directory)
        if not map_data_dir:
            logger_session.error("No map_data folder found in input directory.")
            return False

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
            path_to_point_gmt(str(path_file), gmt_out, logger_session=logger_session)
            path_gmt_to_shp(gmt_out, shp_out, logger_session=logger_session)

        # Stage 2 + 3: per selected map dataset
        for map_stem, col_idx in entries:
            polygon_shp = os.path.join(map_data_dir, f"{map_stem}.shp")
            if not Path(polygon_shp).is_file():
                logger_session.warning(f"Map shapefile not found, skipping: {map_stem}.shp")
                continue

            logger_session.info(f"Processing map dataset: {map_stem} (column {col_idx})")

            joined_dir = os.path.join(lin_geo_root, map_stem, "joined")
            poly_dir = os.path.join(lin_geo_root, map_stem, "polygons")
            os.makedirs(joined_dir, exist_ok=True)
            os.makedirs(poly_dir, exist_ok=True)

            spatial_join(point_shp_dir, polygon_shp, joined_dir, logger_session=logger_session)

            for joined_shp in sorted(Path(joined_dir).glob("*_new.shp")):
                nm = joined_shp.stem.replace("_new", "")
                poly_gmt = os.path.join(poly_dir, f"{nm}_{map_stem}_pl.gmt")
                poly_shp = os.path.join(poly_dir, f"{nm}_{map_stem}.shp")
                build_polygon_gmt(str(joined_shp), poly_gmt, col_idx,
                                  logger_session=logger_session)
                run_command([get_ogr_path(), "-f", "ESRI Shapefile", poly_shp, poly_gmt])
                logger_session.info(f"Polygon shapefile written: {Path(poly_shp).name}")

        logger_session.info("Linear geology pipeline completed.")
        return True

    except Exception as e:
        logger_session.error(f"Linear geology pipeline failed: {e}")
        return False
