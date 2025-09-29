import decimal
import os
import glob
import sys
import geopandas
import folium
import warnings

from osgeo import osr
from pathlib import Path
from aemworkflow.utilities import get_ogr_path, validate_file, run_command

header = 0
xpo = 0.5
ypo = 0.5

decimal.getcontext().rounding = decimal.ROUND_HALF_UP


def active_gmt_metadata_to_bdf(gmt_file_path, bdf_file_path, mode):
    try:
        with open(bdf_file_path, mode) as out_bdf_file:
            with open(gmt_file_path) as in_gmt_file:
                counter = 0
                for line in in_gmt_file:
                    if '@D' in line:
                        out_bdf_file.write(f"{Path(gmt_file_path).name}|{counter}|{line.strip()}\n")
                        counter += 1
    except Exception as e:
        print(f"Error processing GMT metadata: {e}", file=sys.stderr)
        sys.exit(1)


def active_shp_to_gmt(shp_file_path, gmt_file_path):
    cmd = [get_ogr_path(), "-f", "GMT", gmt_file_path, shp_file_path]
    if not validate_file(shp_file_path):
        return
    run_command(cmd)


def active_extent_control_file(extent_file_path, path_file_path,
                               output_file_path, out_active_extent_path,
                               crs, gis, mode):
    try:
        proj = osr.SpatialReference()
        proj.ImportFromEPSG(int(crs))
        result_wkt = proj.ExportToWkt()
        result_wkt = result_wkt.replace('"', '\\"')
        result_proj = proj.ExportToProj4()
        # print(f'epsg resutl is: {result_wkt}')
        # print(f'proj string is: {result_proj}')
        del proj

        with open(out_active_extent_path, mode) as out_active_ext_file:
            with open(extent_file_path) as extent_file:
                extent_line = extent_file.readline().strip()
                out_active_ext_file.write(f'{extent_line}\n')

        with open(output_file_path, mode) as out_file:
            if mode == 'w':
                out_file.write("# @VGMT1.0 @GLINESTRING\n")
                out_file.write(f'# @Jp"{result_proj}"\n')
                out_file.write(f'# @Jw"{result_wkt}"\n')
                out_file.write("# @Nlinenum\n")
                out_file.write("# @Tinteger\n")
                out_file.write("# FEATURE_DATA\n")

            line_name = None

            with open(path_file_path) as path_file:
                for path_line in path_file:
                    path_line = path_line.strip().split()

                    if line_name != path_line[0]:
                        line_name = path_line[0]
                        out_file.write(">\n")
                        out_file.write(f"# @D{line_name}\n")

                    out_file.write(f"{path_line[4]} {path_line[5]}\n")
    except Exception as e:
        print(f"Error processing extent or path file: {e}", file=sys.stderr)
        sys.exit(1)


def main(input_directory, output_directory, crs=28349, gis="esri_arcmap_0.5", lines=10, lines_increment=30):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        print("create AEM interp box and ground level ghost profiles", file=sys.stderr)
        print("layer interval", lines_increment, file=sys.stderr)
        print("layer count", lines, file=sys.stderr)
        Path(fr'{output_directory}{os.sep}interp').mkdir(exist_ok=True)
        active_extent_out_file_path = os.path.join(output_directory, 'interp', 'active_extent.txt')
        active_gmt_out_file_path = os.path.join(output_directory, 'interp', 'active_path.gmt')
        active_shp_out_file_path = os.path.join(output_directory, 'interp', 'active_path.shp')
        ogr2ogr_active_gmt_log = os.path.join(output_directory, 'interp', 'gdal_active.log')

        shp_dir = input_directory
        shp_list = sorted(glob.glob(os.path.join(shp_dir, '*_interp_*.shp')))
        mode = 'w'

        for shp in shp_list:
            fname = Path(shp).stem
            prefix = fname.split("_")[0]
            extent_file_path = os.path.join(shp_dir, f'{prefix}.extent.txt')
            print(f'extent file {extent_file_path} exists: {os.path.isfile(extent_file_path)}')
            path_file_path = os.path.join(shp_dir, f'{prefix}.path.txt')
            print(f'path file {path_file_path} exists: {os.path.isfile(path_file_path)}')
            active_extent_control_file(extent_file_path,
                                       path_file_path,
                                       active_gmt_out_file_path,
                                       active_extent_out_file_path,
                                       crs,
                                       gis,
                                       mode)

            gmt_file_path = os.path.join(output_directory, 'interp', f'{prefix}_interp.gmt')
            active_shp_to_gmt(shp, gmt_file_path)

            bdf_file_path = os.path.join(output_directory, 'interp', 'met.bdf')
            active_gmt_metadata_to_bdf(gmt_file_path, bdf_file_path, mode)

            mode = 'a'

            cmd = [
                get_ogr_path(),
                "-f", "ESRI Shapefile",
                active_shp_out_file_path,
                active_gmt_out_file_path,
                "--config", "CPL_DEBUG", "ON",
                "--config", "CPL_LOG", ogr2ogr_active_gmt_log
            ]
            if not validate_file(active_gmt_out_file_path):
                return
            run_command(cmd)

            # Create the active path interp geojson file for display on map.
            active_path_interp_shp: geopandas.GeoDataFrame = geopandas.read_file(active_shp_out_file_path)
            print(active_path_interp_shp.crs)
            active_path_interp_shp = active_path_interp_shp.to_crs(epsg=4326)
            print(active_path_interp_shp.crs)
            active_path_interp_shp.to_file(os.path.join(output_directory,
                                                        'interp',
                                                        'active_path.geojson'), driver='GeoJSON')

            # Create the folium map for the all_lines and update the map html file.
            def style_func(x):
                return {
                    'fillColor': 'red',
                    'color': 'red',
                    'opacity': 0.50,
                    'weight': 2,
                }

            m = folium.Map(location=[-30.80, 141.264160], zoom_start=5)
            folium.GeoJson(data=open(os.path.join(output_directory,
                                                  'interp',
                                                  'active_path.geojson'), 'r').read(),
                           name="interp", style_function=style_func).add_to(m)

            layer = folium.GeoJson(data=open(os.path.join(output_directory,
                                   'all_lines',
                                             'all_lines.geojson'), 'r').read(), name="all-lines").add_to(m)
            print(f'bounds are: {layer.get_bounds()}')

        folium.LayerControl().add_to(m)
        map_path = os.path.normpath(f"{output_directory}{os.sep}map.html")
        m.save(map_path)
        print('completed updating map')


if __name__ == "__main__":
    main()
