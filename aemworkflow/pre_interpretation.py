import decimal
from osgeo import osr
import sys
import os
from pathlib import Path
import glob
import subprocess
import argparse

from aemworkflow.config import get_ogr_path

# logging.basicConfig(filename='out.log',
#                     filemode='w',
#                     format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#                     datefmt='%H:%M:%S',
#                     level=logging.DEBUG)

# p = 1
header = 0
# linename = -99999
dlrs = 10
ddd = dlinc = 30  # Set the initial value for dlinc
dpth = dlinc
# xpo = 0.5
# ypo = 0.5

decimal.getcontext().rounding = decimal.ROUND_HALF_UP


def all_lines(path_file_path, output_file_path, crs, gis, mode):
    proj = osr.SpatialReference()
    proj.ImportFromEPSG(int(crs))
    result_wkt = proj.ExportToWkt()
    result_wkt = result_wkt.replace('"', '\\"')
    result_proj = proj.ExportToProj4()
    # print(f'epsg resutl is: {result_wkt}')
    # print(f'proj string is: {result_proj}')
    del proj

    with open(output_file_path, mode) as out_file:
        if mode == 'w':
            out_file.write("# @VGMT1.0 @GLINESTRING\n")
            out_file.write(f'# @Jp"{result_proj}"\n')
            out_file.write(f'# @Jw"{result_wkt}"\n')
            out_file.write("# @Nlinenum|flightnum|date|Survey|Company|Status\n")
            out_file.write("# @Tinteger|integer|integer|string|string|string\n")
            out_file.write("# FEATURE_DATA\n")

        with open(path_file_path) as file:
            first_line = file.readline().strip().split()
            out_file.write(">\n")
            out_file.write(f"# @D{first_line[0]}\n")
            out_file.write(f"{first_line[4]} {first_line[5]}\n")
            for line in file:
                # Parse the input fields from the line
                fields = line.strip().split()
                if len(fields) > 0:
                    out_file.write(f"{fields[4]} {fields[5]}\n")


def print_boxes(pl, pt, pr, pb, out_file, xpo, ypo):
    out_file.write(">\n")
    out_file.write("# @Dextent\n")
    out_file.write(f"{pl - xpo} {pt + ypo}\n")
    out_file.write(f"{pr - xpo} {pt + ypo}\n")
    out_file.write(f"{pr - xpo} {pb + ypo}\n")
    out_file.write(f"{pl - xpo} {pb + ypo}\n")
    out_file.write(f"{pl - xpo} {pt + ypo}\n")

    out_file.write(">\n")
    out_file.write("# @Dupper_left\n")
    out_file.write(f"{pl - xpo} {pt + ypo}\n")
    out_file.write(f"{pl + 1 - xpo} {pt + ypo}\n")
    out_file.write(f"{pl + 1 - xpo} {pt - 1 + ypo}\n")
    out_file.write(f"{pl - xpo} {pt - 1 + ypo}\n")
    out_file.write(f"{pl - xpo} {pt + ypo}\n")

    out_file.write(">\n")
    out_file.write("# @Dlower_right\n")
    out_file.write(f"{pr - xpo} {pb + ypo}\n")
    out_file.write(f"{pr - 1 - xpo} {pb + ypo}\n")
    out_file.write(f"{pr - 1 - xpo} {pb + 1 + ypo}\n")
    out_file.write(f"{pr - xpo} {pb + 1 + ypo}\n")
    out_file.write(f"{pr - xpo} {pb + ypo}\n")

    out_file.write(">\n")
    out_file.write("# @Dground_level\n")


def box_elevation(extent_file_path, path_file_path, output_file_path, depth_lines, line_increments, xpo, ypo):
    global header
    global dlrs
    global ddd
    global dpth
    global dlinc

    last = None
    yy = []

    dlrs = int(depth_lines)
    ddd = dpth = dlinc = int(line_increments)

    # This function will be modified to do the following:
    # - Look for all path and extent files in folder
    # - check that the numbers are equal, if not report on the ones that are missing.
    # - modify jointjs icons to show actual numbers
    # - create box.gmt files for all combination of path and extent files.

    with open(output_file_path, 'w') as out_file:

        with open(extent_file_path) as file:
            for line in file:
                # Parse the input fields from the line
                fields = line.strip().split()
                if len(fields) > 0:
                    nr1, pt, pl, pr, pb, nr2, dt, nr3, db = map(float, fields)
                    y_of = dt
                    y_fact = (db - dt) / (pb - pt)

                    out_file.write("# @VGMT1.0 @GLINESTRING\n")
                    out_file.write("# @Nlinename\n")
                    out_file.write("# @Tstring\n")
                    out_file.write("# FEATURE_DATA\n")

                    print_boxes(pl, pt, pr, pb, out_file, xpo, ypo)

        with open(path_file_path) as path_file:
            for line in path_file:
                path_fields = line.strip().split()

                if len(path_fields) > 0:
                    ppt = int(path_fields[1])
                    py = (y_of - float(path_fields[8])) / y_fact
                    out_file.write(f"{int(path_fields[1]) - 1} "
                                   f"{round(decimal.Decimal((-py + ypo) - (2 / y_fact)), 4).normalize()}\n")
                    yy.insert(ppt - 1, py * -1)
                    last = ppt

        for j in range(1, dlrs + 1):
            out_file.write(">\n")
            out_file.write(f"# @D{dpth}\n")

            for i in range(0, last):
                # ly=(yy[i]-(ddd/y_fact))
                # print i-1" "ly+ypo

                ly = round(decimal.Decimal(str(yy[i] - (ddd / y_fact) - (2 / y_fact))), 4).normalize()
                out_file.write(f'{i} {round(ly + decimal.Decimal(ypo), 4).normalize()}\n')

            ddd += dlinc
            dpth += dlinc


def main():
    print("create AEM interp box and ground level ghost profiles", file=sys.stderr)
    print("layer interval", dlinc, file=sys.stderr)
    print("layer count", dlrs, file=sys.stderr)

    ap = argparse.ArgumentParser()
    ap.add_argument("--input_directory", "-i", required=True, help="Input directory with path and extent files")
    ap.add_argument("--output_directory", "-o", required=True, help="Output directory for generated files")
    ap.add_argument("--crs", "-c", required=False, help="Coordinate reference system")
    ap.add_argument("--gis", "-g", required=False, help="GIS")
    ap.add_argument("--lines", "-l", required=False, help="Depth lines, defaults to 10")
    ap.add_argument("--lines_increment", "-li", required=False, help="Depth lines increment, defaults to 30")

    ARG = vars(ap.parse_args())

    input_directory = ARG["input_directory"]
    output_directory = ARG["output_directory"]
    crs = ARG["crs"]
    gis = ARG["gis"]
    lines = ARG["lines"] if ARG["lines"] else 10
    lines_increment = ARG["lines_increment"] if ARG["lines_increment"] else 30
    extent_files_list = sorted(glob.glob(os.path.join(input_directory, '*.extent.txt')))
    path_files_list = sorted(glob.glob(os.path.join(input_directory, '*.path.txt')))
    all_lines_shp_output_path = os.path.join(output_directory, 'all_lines', 'all_lines.shp')

    Path(os.path.join(output_directory, 'all_lines')).mkdir(exist_ok=True)

    mode = 'w'
    for path_file_path in path_files_list:
        all_lines_gmt_output_file_path = os.path.join(output_directory, 'all_lines', 'all_lines.gmt')
        all_lines(path_file_path, all_lines_gmt_output_file_path, crs, gis, mode)
        mode = 'a'

    # After the loop, process the all_lines_gmt_output_file_path
    ogr2ogr_all_lines_log = os.path.join(output_directory, 'all_lines', 'gdal_all_lines.log')

    Path(fr'{output_directory}{os.sep}box').mkdir(exist_ok=True)
    if len(extent_files_list) != len(path_files_list):
        print(f"Path an Extent numbers not matching up:{len(path_files_list)}:{len(extent_files_list)}")
    else:
        print(f"Path an Extent numbers are matching up:{len(path_files_list)}:{len(extent_files_list)}")
        ogr2ogr_gmt_log = os.path.join(output_directory, 'box', 'gdal_gmt.log')

        for path_file_path, extent_file_path in zip(path_files_list, extent_files_list):
            file_path = os.path.basename(path_file_path)
            flight_path_number = file_path.split('.')[0]
            gmt_ouput_file_path = os.path.join(output_directory, 'box', f'{flight_path_number}.box.gmt')

            xpo = ypo = float(gis.split('_')[-1])
            box_elevation(extent_file_path, path_file_path, gmt_ouput_file_path, lines, lines_increment, xpo, ypo)

            shp_output_file_path = os.path.join(output_directory, 'box', f'{flight_path_number}.box.shp')
            cmd = [get_ogr_path(), "-f", "ESRI Shapefile", shp_output_file_path, gmt_ouput_file_path, "--config", "CPL_LOG", ogr2ogr_gmt_log]
            subprocess.run(cmd, check=True)
    
# ---- End of the first code block --- #
    mode = 'w'
    Path(os.path.join(output_directory, 'all_lines')).mkdir(exist_ok=True)

    for path_file_path in path_files_list:
        all_lines_gmt_output_file_path = os.path.join(output_directory, 'all_lines', 'all_lines.gmt')
        all_lines(path_file_path, all_lines_gmt_output_file_path, crs, gis, mode)
        mode = 'a'

    all_lines_shp_output_path = os.path.join(output_directory, 'all_lines', 'all_lines.shp')
    ogr2ogr_all_lines_log = os.path.join(output_directory, 'all_lines', 'gdal_all_lines.log')
    cmd = [
        get_ogr_path(),
        "-f", "ESRI Shapefile",
        all_lines_shp_output_path,
        all_lines_gmt_output_file_path,
        "--config", "CPL_DEBUG", "ON",
        "--config", "CPL_LOG", ogr2ogr_all_lines_log
    ]
    subprocess.run(cmd, check=True)

# TODO is this needed for CLI?
    # Create the all_lines geojson file for display on map.
    all_lines_shp: geopandas.GeoDataFrame = geopandas.read_file(all_lines_shp_output_path)
    print(all_lines_shp.crs)
    all_lines_shp = all_lines_shp.to_crs(epsg=4326)
    print(all_lines_shp.crs)
    all_lines_shp.to_file(os.path.join(output_directory, 'all_lines', 'all_lines.geojson'), driver='GeoJSON')

    # Create the folium map for the all_lines and update the map html file.
    m = folium.Map(location=[-30.80, 141.264160], zoom_start=5)
    layer = folium.GeoJson(data=open(os.path.join(output_directory,
                                                  'all_lines',
                                                  'all_lines.geojson'), 'r').read(), name="all-lines").add_to(m)
    print(f'bounds are: {layer.get_bounds()}')

    # Create interpretation artifacts if we have found any.
    if form.interp_count > 0:
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
            extent_file_path = fr'{shp_dir}{os.sep}{prefix}.extent.txt'
            print(f'extent file {extent_file_path} exists: {os.path.isfile(extent_file_path)}')
            path_file_path = fr'{shp_dir}{os.sep}{prefix}.path.txt'
            print(f'path file {path_file_path} exists: {os.path.isfile(path_file_path)}')
            inter.active_extent_control_file(extent_file_path,
                                             path_file_path,
                                             active_gmt_out_file_path,
                                             active_extent_out_file_path,
                                             form.crs.data,
                                             form.gis.data,
                                             mode)

            gmt_file_path = os.path.join(output_directory, 'interp', f'{prefix}_interp.gmt')
            inter.active_shp_to_gmt(shp, gmt_file_path)

            bdf_file_path = os.path.join(output_directory, 'interp', 'met.bdf')
            inter.active_gmt_metadata_to_bdf(gmt_file_path, bdf_file_path, mode)

            mode = 'a'

        cmd = [
            get_ogr_path(),
            "-f", "ESRI Shapefile",
            active_shp_out_file_path,
            active_gmt_out_file_path,
            "--config", "CPL_DEBUG", "ON",
            "--config", "CPL_LOG", ogr2ogr_active_gmt_log
        ]
        subprocess.run(cmd, check=True)

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

        # m = folium.Map(location = [-30.80, 141.264160], zoom_start=5)
        folium.GeoJson(data=open(os.path.join(output_directory,
                                              'interp',
                                              'active_path.geojson'), 'r').read(),
                                              name="interp",
                                              style_function=style_func).add_to(m)

        print(f'bounds are: {layer.get_bounds()}')

    folium.LayerControl().add_to(m)
    print(f'path is: {current_app.instance_path}')
    print(f'path is: {current_app.root_path}')
    session['map_path'] = os.path.normpath(f"{output_directory.rstrip(session['uuid'])}{os.sep}map.html")
    m.save(session['map_path'])
    print('completed updating map')
    cmd = [get_ogr_path(), "-f", "ESRI Shapefile", all_lines_shp_output_path, all_lines_gmt_output_file_path]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
