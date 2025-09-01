
import subprocess
from pathlib import Path
import logging
import decimal

from osgeo import osr
from aemworkflow.config import get_ogr_path


logging.basicConfig(filename='out.log',
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


# p = 1
header = 0
# linename = -99999
dlrs = 10
ddd = dlinc = 30  # Set the initial value for dlinc
dpth = dlinc
xpo = 0.5
ypo = 0.5

decimal.getcontext().rounding = decimal.ROUND_HALF_UP


def active_gmt_metadata_to_bdf(gmt_file_path, bdf_file_path, mode):
    with open(bdf_file_path, mode) as out_bdf_file:
        with open(gmt_file_path) as in_gmt_file:
            counter = 0
            for line in in_gmt_file:
                if '@D' in line:
                    out_bdf_file.write(f"{Path(gmt_file_path).name}|{counter}|{line.strip()}\n")
                    counter += 1


def active_shp_to_gmt(shp_file_path, gmt_file_path):
    # ogr2ogr.main(["", "-f", "GMT", gmt_file_path, shp_file_path])
    cmd = [get_ogr_path(), "-f", "GMT", gmt_file_path, shp_file_path]
    subprocess.run(cmd, check=True)


def active_extent_control_file(extent_file_path, path_file_path,
                               output_file_path, out_active_extent_path,
                               crs, gis, mode):
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

# def main():
#     print("create AEM interp box and ground level ghost profiles", file=sys.stderr)
#     print("layer interval", dlinc, file=sys.stderr)
#     print("layer count", dlrs, file=sys.stderr)

#     # input_directory = r'C:\Temp\jira-pv-1728\run_03'
#     input_directory = r'C:\Temp\jira-pv-1930\input'
#     output_directory = r'C:\Temp\jira-pv-1930\output'

#     active_extent_out_file_path = r'C:\Temp\jira-pv-1728\run_03\active_extent_new.txt'
#     active_gmt_out_file_path = r'C:\Temp\jira-pv-1728\run_03\active_control_file_new.gmt'

#     shp_dir = input_directory
#     shp_list = sorted(glob.glob(os.path.join(shp_dir, '*_interp_*.shp')))
#     mode = 'w'
#     for shp in shp_list:
#         fname = Path(shp).stem
#         prefix = fname.split("_")[0]
#         extent_file_path = fr'{shp_dir}\{prefix}.extent.txt'
#         print(f'extent file {extent_file_path} exists: {os.path.isfile(extent_file_path)}')
#         path_file_path = fr'{shp_dir}\{prefix}.path.txt'
#         print(f'path file {path_file_path} exists: {os.path.isfile(path_file_path)}')
#         active_extent_control_file(extent_file_path, path_file_path, active_gmt_out_file_path,
#           active_extent_out_file_path, mode)

#         gmt_file_path = f'{shp_dir}\{prefix}_interp_new.gmt'
#         active_shp_to_gmt(shp, gmt_file_path)

#         bdf_file_path = f'{shp_dir}\met_new.bdf'
#         active_gmt_metadata_to_bdf(gmt_file_path, bdf_file_path, mode)

#         mode = 'a'

# if __name__ == "__main__":
#     main()
