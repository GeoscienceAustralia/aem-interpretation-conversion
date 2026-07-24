import csv
import os
import re
import sys
from pathlib import Path
from typing import List

import pandas as pd
from loguru import logger


def gmtsddd_to_egs(wrk_dir: str, alt_colors: str, nm_list: List[int]) -> None:
    # Initialize dictionaries for over and under age
    ov = {}
    un = {}

    # Open the CSV file for writing
    try:
        with open(os.path.join(wrk_dir, 'SORT', 'output.egs'), 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')
            # Write the header to stderr and the CSV file
            sys.stderr.write("Export EGGS CSV\n")
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
        logger.error(f"Error during gmtsddd_to_egs conversion: {e}")


def gmtsddd_to_mdc(wrk_dir: str, colors: str, nm_list: List[int]) -> None:
    r = {}
    g = {}
    b = {}

    # Open the CSV file for writing
    try:
        with open(os.path.join(wrk_dir, 'SORT', 'output.mdc'), 'w', newline='') as csvfile:
            csvwriter_sort = csv.writer(csvfile, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')
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
                    open(os.path.join(wrk_dir, 'export', f'{filename}.mdc'), 'w', newline='') as expfile
                ):
                    csvwriter_export = csv.writer(expfile, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')

                    def write_row(row):
                        csvwriter_sort.writerow(row)
                        csvwriter_export.writerow(row)
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
        with open(os.path.join(wrk_dir, 'SORT', 'output.mdch'), 'w', newline='') as csvfile:
            csvwriter_sort = csv.writer(csvfile, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')

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
                    open(os.path.join(wrk_dir, 'export', f'{filename}.mdch'), 'w', newline='') as expfile
                ):
                    csvwriter_export = csv.writer(expfile, quoting=csv.QUOTE_NONE, quotechar=None, escapechar='\\')

                    def write_row(row):
                        csvwriter_sort.writerow(row)
                        csvwriter_export.writerow(row)

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


def gmts_2_egs(wrk_dir: str, alt_colors: str, nm_lst: List[int]) -> None:
    """
    Implements the following action from the AWK script:
    awk -f gmts_2_egs.awk LU_SPLIT_FEATURE_CLASSES_20220215.prn $1.gmts > $1.egs

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    alt_colors: str
        The path to the other *.prn file with RGB values for geo features
    nm_lst: List[int]
        The list of path identifiers from the the common extent file
    """

    try:
        srt_dir = Path(wrk_dir) / "SORT"
        if not (srt_dir).exists():
            logger.error("SORT folder missing")
            sys.exit(0)

        header = "Vertex,SegmentID,X,Y,ELEVATION,PixelX," \
            "PixelY,AusAEM_DEM,DEPTH,Type,OverAge,UnderAge," \
            "BoundConf,ContactTyp,BasisOfInt,OvrStrtUnt," \
            "OvrStratNo,OvrConf,UndStrtUnt,UndStratNo," \
            "UndConf,WithinStrt,WithinStNo,WithinConf," \
            "HydStrtType,HydStrConf,BOMNAFUnt,BOMNAFNo," \
            "InterpRef,Comment,Annotation,NewObs,Operator," \
            "" \
            "Date,SURVEY_LINE\n"

        regex2 = re.compile('[+-]?([0-9]*[.])?[0-9]+')

        cdf = pd.read_csv(alt_colors, sep=r"\s{2,}", header=0, index_col=False, engine="python")
        cdf.fillna('', inplace=True)
        seg = 0

        for nm in nm_lst:
            gmts = Path(srt_dir) / f"{nm}.gmtsddd"
            if not gmts.exists():
                continue
            lines = gmts.read_text().split("\n")
            with open(Path(srt_dir) / f"{nm}.egs", "w") as fou:
                fou.write(header)
                while lines:
                    try:
                        line = lines.pop(0)
                    except IndexError:
                        logger.info(f"{nm}.gmts processed")
                        break
                    if "@D" in line:
                        seg += 1
                        m_lst = line.split("|")
                        gnm = m_lst[2]
                        row = cdf[cdf["TYPE"] == gnm]
                        # row = cdf.query("TYPE == @gnm")
                        met = f"{gnm},{row['OVERAGE'].iloc[0]},"
                        f"{row['UNDERAGE'].iloc[0]},"
                        f"{','.join(str(x) for x in m_lst[2:24])}"
                        line = lines.pop(0)

                        try:
                            while regex2.match(line.split()[0]):
                                los = line.split()
                                fou.write(f"{los[9]},{los[8]},{los[2]},"
                                          f"{los[3]},{los[4]},{los[0]},"
                                          f"{los[1]},{los[5]},{los[6]},"
                                          f"{met},{nm}\n")
                                line = lines.pop(0)
                        except IndexError:
                            pass
    except Exception as e:
        logger.error(f"Error during gmts_2_egs conversion: {e}")
        sys.exit(1)


def gmts_2_mdc(wrk_dir: str, colors: str, nm_lst: List[int]) -> None:
    """
    Implements the following action from the AWK script:
    awk -f gmts_2_mdc_colr.awk New_feature_classes_20210623.prn $1.gmts > $1.mdc

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    colors: str
        The path to the *.prn file with RGB values for geo features
    nm_lst: List[int]
        The list of path identifiers from the the common extent file
    """

    try:
        fsctn = ("GOCAD PLine 1\n"
                 "HEADER {{\n"
                 "name:{}_{}_{}\n"
                 "*atoms:false\n"
                 "*line*color:{:.6f} {:.6f} {:.6f} 1\n"
                 "use_feature_color: false\n"
                 "width:5\n"
                 "*metadata*Line: {}\n"
                 "*metadata*Type: {}\n"
                 "*metadata*BoundaryNm: {}\n"
                 "*metadata*BoundConf: {}\n"
                 "*metadata*BasisOfInt: {}\n"
                 "*metadata*OvrStrtUnt: {}\n"
                 "*metadata*OvrStrtCod: {}\n"
                 "*metadata*OvrConf: {}\n"
                 "*metadata*UndStrtUnt: {}\n"
                 "*metadata*UndStrtCod: {}\n"
                 "*metadata*UndConf: {}\n"
                 "*metadata*WithinType: {}\n"
                 "*metadata*WithinStrt: {}\n"
                 "*metadata*WithinStNo: {}\n"
                 "*metadata*WithinConf: {}\n"
                 "*metadata*InterpRef: {}\n"
                 "*metadata*Comment: {}\n"
                 "*metadata*Annotation: {}\n"
                 "*metadata*NewObs: {}\n"
                 "*metadata*Operator: {}\n"
                 "*metadata*Organization: Geoscience Australia\n"
                 "}}\n"
                 "PROPERTIES px py gl depth\n"
                 "GOCAD_ORIGINAL_COORDINATE_SYSTEM\n"
                 'NAME " gocad Local"\n'
                 'PROJECTION " GDA94 / MGA zone 53"\n'
                 'DATUM " Mean Sea Level"\n'
                 "AXIS_NAME X Y Z\n"
                 "AXIS_UNIT m m m\n"
                 "ZPOSITIVE Elevation\n"
                 "END_ORIGINAL_COORDINATE_SYSTEM\n"
                 "GEOLOGICAL_FEATURE {}\n"
                 "ILINE\n"
                 )
        fmt = "PVRTX {:0.0f} {:6.1f} {:7.1f} {:.1f} {:.6f} {:.6f} {:.1f} {:.1f}\n"

        srt_dir = Path(wrk_dir) / "SORT"
        if not (srt_dir).exists():
            logger.error("SORT folder missing")
            sys.exit(0)

        regex2 = re.compile('[+-]?([0-9]*[.])?[0-9]+')

        cdf = pd.read_csv(colors, sep=r"\s{2,}", header=0, index_col=False, engine="python")
        cdf.iloc[:, 1:4] /= 256.0

        for nm in nm_lst:
            gmts = Path(srt_dir) / f"{nm}.gmtsddd"
            if not gmts.exists():
                continue
            lines = gmts.read_text().split("\n")
            with open(Path(srt_dir) / f"{nm}.mdc", "w") as fou:
                while lines:
                    try:
                        line = lines.pop(0)
                    except IndexError:
                        logger.info(f"{nm}.gmts processed")
                        break
                    if "@D" in line:
                        met = line.split("|")
                        gname = met[2]
                        row = cdf[cdf["Feature classes"] == gname]
                        # row = cdf.query("`Feature classes` == @gname")
                        line = lines.pop(0)
                        segn, frst = line.split()[8: 10]
                        frst = int(frst)
                        # segn = int(segn)
                        fou.write(fsctn.format(nm, segn, met[2],
                                  row['Red'].iloc[0], row['Green'].iloc[0], row['Blue'].iloc[0],
                                  nm,
                                  *met[2:21],
                                  nm
                                  ))
                        try:
                            while regex2.match(line.split()[0]):
                                los = [int(_l) if i == 7 else float(_l) for i, _l in enumerate(line.split())]
                                fou.write(fmt.format(los[9], los[2], los[3], los[4], los[0], los[1], los[5], los[6]))
                                last = int(los[9])
                                line = lines.pop(0)
                        except IndexError:
                            pass
                        for i in range(frst, last):
                            fou.write(f"seg {i} {i + 1}\n")
                        fou.write("END\n")
    except Exception as e:
        logger.error(f"Error during gmts_2_mdc conversion: {e}")
        sys.exit(1)


def main(input_directory: str, output_directory: str, boundary: str, split: str,
         export_mdc=False, export_mdch=False, export_egs=False) -> None:
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

    if export_egs:
        split_file_path = os.path.join(path_dir, split)
        gmtsddd_to_egs(work_dir, split_file_path, nm_list)


if __name__ == "__main__":
    main()
