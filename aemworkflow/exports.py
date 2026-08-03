import csv
import os
import re
import sys
from pathlib import Path
from typing import List

import pandas as pd
from loguru import logger

from aemworkflow.utilities import get_ogr_path, run_command, validate_file


def gmtsddd_to_csv(wrk_dir: str, alt_colors: str, nm_list: List[int]) -> None:
    # Initialize dictionaries for over and under age
    ov = {}
    un = {}

    # Open the CSV file for writing
    try:
        with open(os.path.join(wrk_dir, 'export', 'output.csv'), 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')
            # Write the header to stderr and the CSV file
            sys.stderr.write("Export CSV\n")
            csvwriter.writerow(["Vertex", "SegmentID", "X", "Y", "ELEVATION", "PixelX", "PixelY", "AusAEM_DEM", "DEPTH",
                                "Type", "OverAge", "UnderAge", "BoundConf", "ContactTyp", "BasisOfInt", "OvrStrtUnt",
                                "OvrStratNo", "OvrConf", "UndStrtUnt", "UndStratNo", "UndConf", "WithinStrt",
                                "WithinStNo", "WithinConf", "HydStrtType", "HydStrConf", "BOMNAFUnt", "BOMNAFNo",
                                "InterpRef", "Comment", "Annotation", "NewObs", "Operator", "Date", "SURVEY_LINE"])

            # Read the input file
            with open(alt_colors, 'r') as prn_file:
                for line in prn_file:
                    # parts = line.strip().split(',')
                    parts = re.split(r'\s{2,}', line.strip())
                    ov[parts[0]] = ' ' if len(parts) < 2 else parts[1]
                    un[parts[0]] = ' ' if len(parts) < 3 else parts[2]

            for filename in nm_list:
                with open(os.path.join(wrk_dir, 'SORT', f'{filename}.gmtsddd'), 'r') as file:
                    for line in file:
                        # Process the subsequent files
                        if line.startswith('# @D0'):
                            # Handle lines starting with '#'
                            # seg += 1
                            parts = line.strip().split('|')
                            # l = parts[3].split('_')
                            met = [parts[2]] + [ov.get(parts[2], '')] + [un.get(parts[2], '')] + parts[3:25]
                        elif line[0].isdigit():
                            # Handle lines starting with a digit
                            parts = line.strip().split(' ')
                            row_to_write = parts[9:10] + parts[8:9] + parts[0:7] + met + [filename]
                            csvwriter.writerow(row_to_write)
    except Exception as e:
        logger.error(f"Error during gmtsddd_to_csv conversion: {e}")


def gmtsddd_to_mdc(wrk_dir: str, colors: str, nm_list: List[int]) -> None:
    r = {}
    g = {}
    b = {}

    # Open the CSV file for writing
    try:
        with open(os.path.join(wrk_dir, 'export', 'output.mdc'), 'w', newline='') as combined_file:
            csvwriter_combined = csv.writer(combined_file, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')
            # Read the input file
            with open(colors, 'r') as prn_file:
                prn_file.readline()
                for line in prn_file:
                    # data = line.strip().split()
                    data = re.split(r'\s{2,}', line)
                    if len(data) > 4:
                        r[data[0]] = float(data[1])
                        g[data[0]] = float(data[2])
                        b[data[0]] = float(data[3])

            for filename in nm_list:
                with (
                    open(os.path.join(wrk_dir, 'SORT', f'{filename}.gmtsddd'), 'r') as file,
                    open(os.path.join(wrk_dir, 'export', f'{filename}.mdc'), 'w', newline='') as individual_file
                ):
                    csvwriter_individual = csv.writer(individual_file, quoting=csv.QUOTE_NONE, quotechar=None,
                                                      escapechar='\\')

                    def write_row(row):
                        csvwriter_combined.writerow(row)
                        csvwriter_individual.writerow(row)
                    for line in file:
                        if line.startswith("# @D0"):
                            filen = [filename, '']  # filename.split(".")
                            line = line.strip().split("|")
                            second_line = file.readline().strip().split()
                            segn = second_line[8]

                            write_row(["GOCAD PLine 1"])
                            write_row(["HEADER {"])
                            write_row([f"name:{filen[0]}_{segn}_{line[2]}"])
                            write_row(["*atoms:false"])
                            write_row(["*line*color:%f %f %f 1" % (r[line[2]] / 256,
                                                                            g[line[2]] / 256,
                                                                            b[line[2]] / 256)])
                            write_row(["use_feature_color: false"])
                            write_row(["width:5"])
                            write_row([f"*metadata*Line: {filen[0]}"])
                            write_row([f"*metadata*Type: {line[2]}"])
                            write_row([f"*metadata*BoundaryNm: {line[3]}"])
                            write_row([f"*metadata*BoundConf: {line[4]}"])
                            write_row([f"*metadata*BasisOfInt: {line[5]}"])
                            write_row([f"*metadata*OvrStrtUnt: {line[6]}"])
                            write_row([f"*metadata*OvrStrtCod: {line[7]}"])
                            write_row([f"*metadata*OvrConf: {line[8]}"])
                            write_row([f"*metadata*UndStrtUnt: {line[9]}"])
                            write_row([f"*metadata*UndStrtCod: {line[10]}"])
                            write_row([f"*metadata*UndConf: {line[11]}"])
                            write_row([f"*metadata*WithinType: {line[12]}"])
                            write_row([f"*metadata*WithinStrt: {line[13]}"])
                            write_row([f"*metadata*WithinStNo: {line[14]}"])
                            write_row([f"*metadata*WithinConf: {line[15]}"])
                            write_row([f"*metadata*InterpRef: {line[16]}"])
                            write_row([f"*metadata*Comment: {line[17]}"])
                            write_row([f"*metadata*Annotation: {line[18]}"])
                            write_row([f"*metadata*NewObs: {line[19]}"])
                            write_row([f"*metadata*Operator: {line[20]}"])
                            write_row(["*metadata*Organization: Geoscience Australia"])
                            write_row(["}"])
                            write_row(["PROPERTIES px py gl depth"])

                            # Coordinate reference system
                            write_row(["GOCAD_ORIGINAL_COORDINATE_SYSTEM"])
                            write_row(["NAME \" gocad Local\""])
                            write_row(["PROJECTION \" GDA94 / MGA zone 53\""])
                            write_row(["DATUM \" Mean Sea Level\""])
                            write_row(["AXIS_NAME X Y Z"])
                            write_row(["AXIS_UNIT m m m"])
                            write_row(["ZPOSITIVE Elevation"])
                            write_row(["END_ORIGINAL_COORDINATE_SYSTEM"])

                            # Feature class used to group section components (AEM section)
                            write_row([f"GEOLOGICAL_FEATURE {filen[0]}"])
                            write_row(["ILINE"])

                            line = second_line
                            first = last = int(line[9])
                            while True:
                                last = int(line[9])
                                write_row([f"PVRTX {int(line[9])} {float(line[0]):.1f} "
                                           f"{float(line[1]):.1f} {float(line[2]):.1f} "
                                           f"{float(line[3])} {float(line[4])} "
                                           f"{float(line[5]):.1f} {float(line[6]):.1f}"])
                                line = file.readline().strip().split()
                                if not line or not line[0].replace('.', '').isdigit():
                                    break

                            for i in range(first, last):
                                write_row([f"seg {i} {i + 1}"])

                            write_row(["END"])
    except Exception as e:
        logger.error(f"Error during gmtsddd_to_mdc conversion: {e}")


def gmtsddd_to_mdch(wrk_dir: str, colors: str, nm_list: List[int]) -> None:
    r = {}
    g = {}
    b = {}

    # Open the CSV file for writing
    try:
        with open(os.path.join(wrk_dir, 'export', 'output.mdch'), 'w', newline='') as combined_file:
            csvwriter_combined = csv.writer(combined_file, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')

            # Read the input file
            with open(colors, 'r') as prn_file:
                prn_file.readline()
                for line in prn_file:
                    # data = line.strip().split()
                    data = re.split(r'\s{2,}', line)
                    if len(data) > 4:
                        r[data[0]] = float(data[1])
                        g[data[0]] = float(data[2])
                        b[data[0]] = float(data[3])

            for filename in nm_list:
                with (
                    open(os.path.join(wrk_dir, 'SORT', f'{filename}.gmtsddd'), 'r') as file,
                    open(os.path.join(wrk_dir, 'export', f'{filename}.mdch'), 'w', newline='') as individual_file
                ):
                    csvwriter_individual = csv.writer(individual_file, quoting=csv.QUOTE_NONE, quotechar=None,
                                                      escapechar='\\')

                    def write_row(row):
                        csvwriter_combined.writerow(row)
                        csvwriter_individual.writerow(row)

                    for line in file:
                        if line.startswith("# @D0"):
                            filen = [filename, 'gmtsddd']  # filename.split(".")
                            line = line.strip().split("|")
                            second_line = file.readline().strip().split()
                            segn = second_line[8]

                            write_row(["GOCAD PLine 1"])
                            write_row(["HEADER {"])
                            write_row([f"name:{filen[0]}_{segn}_{line[2]}"])
                            write_row(["*atoms:false"])
                            write_row(["*line*color: %f %f %f 1" % (r[line[2]] / 256,
                                                                     g[line[2]] / 256,
                                                                             b[line[2]] / 256)])
                            write_row(["use_feature_color: false"])
                            write_row(["width: 5"])
                            write_row([f"*metadata*Line: {filen[0]}"])
                            write_row([f"*metadata*Type: {line[2]}"])
                            write_row([f"*metadata*BoundaryNm: {line[3]}"])
                            write_row([f"*metadata*BoundConf: {line[4]}"])
                            write_row([f"*metadata*BasisOfInt: {line[5]}"])
                            write_row([f"*metadata*OvrStrtUnt: {line[6]}"])
                            write_row([f"*metadata*OvrStrtCod: {line[7]}"])
                            write_row([f"*metadata*OvrConf: {line[8]}"])
                            write_row([f"*metadata*UndStrtUnt: {line[9]}"])
                            write_row([f"*metadata*UndStrtCod: {line[10]}"])
                            write_row([f"*metadata*UndConf: {line[11]}"])
                            write_row([f"*metadata*WithinType: {line[12]}"])
                            write_row([f"*metadata*WithinStrt: {line[13]}"])
                            write_row([f"*metadata*WithinStNo: {line[14]}"])
                            write_row([f"*metadata*WithinConf: {line[15]}"])
                            write_row([f"*metadata*InterpRef: {line[16]}"])
                            write_row([f"*metadata*Comment: {line[17]}"])
                            write_row([f"*metadata*Annotation: {line[18]}"])
                            write_row([f"*metadata*NewObs: {line[19]}"])
                            write_row([f"*metadata*Operator: {line[20]}"])
                            write_row(["*metadata*Organization: Geoscience Australia"])
                            write_row(["}"])
                            write_row(["PROPERTIES px py gl depth"])

                            # Coordinate reference system
                            write_row(["GOCAD_ORIGINAL_COORDINATE_SYSTEM"])
                            write_row(["NAME \" gocad Local\""])
                            write_row(["PROJECTION \" GDA94 / MGA zone 53\""])
                            write_row(["DATUM \" Mean Sea Level\""])
                            write_row(["AXIS_NAME X Y Z"])
                            write_row(["AXIS_UNIT m m m"])
                            write_row(["ZPOSITIVE Elevation"])
                            write_row(["END_ORIGINAL_COORDINATE_SYSTEM"])

                            # Feature class used to group section components (AEM section)
                            write_row([f"GEOLOGICAL_FEATURE {line[2]}"])
                            write_row(["ILINE"])

                            line = second_line
                            first = last = int(line[9])
                            while True:
                                last = int(line[9])
                                write_row([f"PVRTX {int(line[9])} {float(line[0]):.1f} "
                                           f"{float(line[1]):.1f} {float(line[2]):.1f} "
                                           f"{float(line[3])} {float(line[4])} "
                                           f"{float(line[5]):.1f} {float(line[6]):.1f}"])
                                line = file.readline().strip().split()
                                if not line or not line[0].replace('.', '').isdigit():
                                    break

                            for i in range(first, last):
                                write_row([f"seg {i} {i + 1}"])

                            write_row(["END"])
    except Exception as e:
        logger.error(f"Error during gmtsddd_to_mdch conversion: {e}")


def gmtsddd_to_es(wrk_dir: str, colors: str, nm_list: List[int], crs: str,) -> None:
    """
    Create GA Portal / Earth Sciences outputs.

    Input:
        SORT/<line>.gmtsddd

    Output:
        export/<line>.pl
        export/<line>.xml
    """
    r = {}
    g = {}
    b = {}

    sort_directory = Path(wrk_dir) / "SORT"
    export_directory = Path(wrk_dir) / "export"

    xml_files = []
    try:
        # Read the input file
        with open(colors, 'r') as prn_file:
            prn_file.readline()
            for line in prn_file:
                data = re.split(r'\s{2,}', line)
                if len(data) > 4:
                    r[data[0]] = float(data[1])
                    g[data[0]] = float(data[2])
                    b[data[0]] = float(data[3])

        for filename in nm_list:
            feature_segment_counts = {}

            input_path = sort_directory / f'{filename}.gmtsddd'
            pl_output_path = export_directory / f'{filename}.pl'
            xml_output_path = export_directory / f'{filename}.xml'

            with (
                open(input_path, 'r') as file,
                open(pl_output_path, 'w', newline='') as expfile
            ):
                csvwriter_export = csv.writer(expfile, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')

                for line in file:
                    if line.startswith("# @D0"):
                        metadata = line.strip().split("|")
                        feature_type = metadata[2]

                        if feature_type not in r:
                            raise ValueError(f"Feature class '{feature_type}' was not found in {colors}")

                        feature_segment_counts[feature_type] = feature_segment_counts.get(feature_type, 0) + 1
                        segment_number = feature_segment_counts[feature_type]

                        line = file.readline().strip().split()

                        if len(line) < 7:
                            raise ValueError(f"Invalid coordinate row in {input_path}")

                        red = r[feature_type] / 256
                        green = g[feature_type] / 256
                        blue = b[feature_type] / 256

                        csvwriter_export.writerow(["GOCAD PLine 1"])
                        csvwriter_export.writerow(["HEADER {"])
                        csvwriter_export.writerow([f"name:{filename}_{segment_number}_{feature_type}"])
                        csvwriter_export.writerow(["*atoms:false"])
                        csvwriter_export.writerow([f"*line*color:{red:g} {green:g} {blue:g} 1"])
                        csvwriter_export.writerow(["width:5"])
                        csvwriter_export.writerow(["}"])
                        csvwriter_export.writerow(["PROPERTIES px py gl depth"])
                        csvwriter_export.writerow(["ILINE"])

                        vertex_number = 1

                        while True:
                            csvwriter_export.writerow([f"PVRTX {vertex_number} {float(line[0]):.1f} "
                                                       f"{float(line[1]):.1f} {float(line[2]):.1f} "
                                                       f"{float(line[3]):.6f} {float(line[4]):.6f} "
                                                       f"{float(line[5]):.1f} {float(line[6]):.1f}"])
                            line = file.readline().strip().split()

                            if not line or not line[0].replace('.', '', 1).replace('-', '', 1).isdigit():
                                break

                            vertex_number += 1

                        for i in range(1, vertex_number):
                            csvwriter_export.writerow([f"SEG {i} {i + 1}"])

                        csvwriter_export.writerow(["END"])

            with open(xml_output_path, 'w') as xmlfile:
                xmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                xmlfile.write('<Layer version="1" layerType="ModelLayer">\n')
                xmlfile.write(f"<DisplayName>{filename} Interp</DisplayName>\n")
                xmlfile.write(f"<URL>{filename}.pl</URL>\n")
                xmlfile.write("<DataFormat>GOCAD</DataFormat>\n")
                xmlfile.write("<LineWidth>5</LineWidth>\n")
                xmlfile.write(f"<DataCacheName>GA/EFTF/AEM/{filename}.pl</DataCacheName>\n")
                xmlfile.write(f"<CoordinateSystem>EPSG:{crs}</CoordinateSystem>\n")
                xmlfile.write("</Layer>\n")

            logger.info("Created Earth Sciences outputs")

            xml_files.append(xml_output_path)
        create_earthsci_wrapper(wrk_dir, xml_files=xml_files)

    except Exception as e:
        logger.exception(f"Error during gmtsddd_to_es conversion: {e}")


def create_earthsci_wrapper(wrk_dir: str, xml_files: List[Path]) -> None:
    """
    Create a combined EarthSci XML from individual XML files.

    Output:
        export/dataset.xml
    """
    export_directory = Path(wrk_dir) / "export"
    wrapper_path = export_directory / "dataset.xml"
    dataset_name = Path(wrk_dir).resolve().name

    if not xml_files:
        raise ValueError("Cannot create EarthSci wrapper because no XML files were created.")

    with open(wrapper_path, "w", encoding="utf-8") as wrapper_file:
        wrapper_file.write("<DatasetList>\n")
        wrapper_file.write(f'<Dataset name="{dataset_name}">\n')

        for xml_file in xml_files:
            layer_name = xml_file.name.split("_", 1)[0]
            wrapper_file.write(f'<Layer name="{layer_name}" url="{xml_file.name}" />\n')

        wrapper_file.write("</Dataset>\n")
        wrapper_file.write("</DatasetList>\n")

    logger.info("Created combined EarthSci wrapper")


def gmtsddd_to_3d(wrk_dir: str, nm_list: List[int], crs: str) -> None:
    '''
    Create individual 3D shapefiles for each survey line.

    Input:
        SORT/<line>.gmtsddd

    Output:
        export/<line>.shp
        export/<line>.shx
        export/<line>.dbf
        export/<line>.prj
    '''

    try:
        sort_directory = Path(wrk_dir) / "SORT"
        export_directory = Path(wrk_dir) / "export"

        for line_number in nm_list:
            input_path = sort_directory / f"{line_number}.gmtsddd"
            output_path = export_directory / f"{line_number}.shp"

            if not validate_file(input_path):
                return

            cmd = [
                get_ogr_path(),
                '-f', 'ESRI Shapefile',
                '-s_srs', f'EPSG:{crs}',
                '-t_srs', f'EPSG:{crs}',
                '-lco', 'SHPT=ARCZ',
                str(output_path),
                str(input_path),
            ]

            run_command(cmd)

    except Exception:
        logger.exception("Error during gmtsddd_to_3d conversion")


def main(input_directory: str, output_directory: str, boundary: str, split: str,
         export_mdc=False, export_mdch=False, export_csv=False, export_es=False, export_3d=False, crs=28349) -> None:
    active_extent_out_file_path = os.path.join(output_directory, 'interp', 'active_extent.txt')
    exdf = pd.read_csv(active_extent_out_file_path, sep=r'\s+', usecols=[0])
    nm_list = exdf.iloc[:, 0].tolist()

    work_dir = output_directory
    path_dir = input_directory
    if export_mdc:
        boundary_file_path = os.path.join(path_dir, boundary)
        gmtsddd_to_mdc(work_dir, boundary_file_path, nm_list)

    if export_mdch:
        boundary_file_path = os.path.join(path_dir, boundary)
        gmtsddd_to_mdch(work_dir, boundary_file_path, nm_list)

    if export_csv:
        split_file_path = os.path.join(path_dir, split)
        gmtsddd_to_csv(work_dir, split_file_path, nm_list)

    if export_es:
        boundary_file_path = os.path.join(path_dir, boundary)
        gmtsddd_to_es(work_dir, boundary_file_path, nm_list, crs)

    if export_3d:
        gmtsddd_to_3d(work_dir, nm_list, crs)


if __name__ == "__main__":
    main()
