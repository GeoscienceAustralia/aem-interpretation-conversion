"""
GA AEM interpretation workflow, awk2python script translation
"""

from pathlib import Path
import os
import sys
import glob
import argparse
import subprocess
import re
import pandas as pd

from loguru import logger
from typing import List, Tuple, TextIO
from aemworkflow.config import get_ogr_path


def first(shp_dir: str, wrk_dir: str) -> None:
    """
    Converts all the shapefiles found in the shp_dir folder to ASCII format GMT files by calling
    the GDAL ogr2ogr utility. The '>' character is appended as in original the fix_gmt.awk script.
    It combines the following commands:
    ogr2ogr -f 'GMT' '$1'_interp.gmt '$1'_*_interp_*.shp
    gawk -f fix_gmt.awk '$1'_interp.gmt > '$1'_interp.gmtf

    Parameters:
    ----------
    shp_dir: str
        The path to the folder with shapefiles
    wrk_dir: str
        The path to the new/existing work folder
    """

    if not Path(wrk_dir).exists():
        Path(wrk_dir).mkdir(parents=True, exist_ok=False)
    else:
        logger.warning(f"{wrk_dir} folder already exists!")
    shp_list = sorted(glob.glob(os.path.join(shp_dir, '*_interp_*.shp')))
    for shp in shp_list:
        fname = Path(shp).stem
        prefix = fname.split("_")[0]
        out_gmt = Path(wrk_dir) / f"{prefix}_interp.gmt"

        # ogr = gdaltools.ogr2ogr()
        # ogr.set_encoding("UTF-8")
        # ogr.set_input(shp)
        # ogr.set_output(str(out_gmt))
        # ogr.execute()

        # ogr2ogr.main(["", "-f", "GMT", str(out_gmt), shp])
        cmd = [get_ogr_path(), "-f", "GMT", str(out_gmt), shp]
        subprocess.run(cmd, check=True)
        if out_gmt.exists():
            # with open(out_gmt, mode="a") as fin:
            # fin.write(">\n")
            logger.info(f"{fname}.shp successfully converted to {prefix}_interp.gmt")


def interpol(col_1: float, frst: int, last: int, tdf: pd.DataFrame) -> Tuple[float]:
    """
    Reduces the cognitive complexity of the zedfix_gmt() function below
    by carrying out interpolation/extrapolation

    Parameters:
    ----------
    col_1: float
        The 1st value from a line in *_interp.gmt file with 2 float columns
    frst: int
        The starting value of the 'fiduciary' column (minus 1) in the path file
    last: int
        The final value of the 'fiduciary' column (minus 1) in the path file
    tdf: dataframe
        The path file table

    Return:
    -------
    x, y, z: triples[float]
        The list of path identifiers read from the first column of the extent file
    """

    i_last = len(tdf)
    cdp = (tdf["fid"] - 1).tolist()
    if frst <= col_1 < last:
        # interpolate
        for idx in cdp:
            if cdp[idx] <= col_1 < cdp[idx + 1]:
                x1 = tdf['coordx'].iloc[idx]
                y1 = tdf['coordy'].iloc[idx]
                g1 = tdf['gl'].iloc[idx]
                x2 = tdf['coordx'].iloc[idx + 1]
                y2 = tdf['coordy'].iloc[idx + 1]
                g2 = tdf['gl'].iloc[idx + 1]
                l1 = cdp[idx + 1] - cdp[idx]
                l2 = col_1 - cdp[idx]
                lr = l2 / l1
                x = x1 + (x2 - x1) * lr
                y = y1 + (y2 - y1) * lr
                t = g1 + (g2 - g1) * lr
    elif int(col_1) <= frst:
        # extrapolate to the left
        x1 = tdf['coordx'].iloc[0]
        y1 = tdf['coordy'].iloc[0]
        g1 = tdf['gl'].iloc[0]
        x2 = tdf['coordx'].iloc[1]
        y2 = tdf['coordy'].iloc[1]
        g2 = tdf['gl'].iloc[1]
        l1 = cdp[1] - cdp[0]
        l2 = col_1 - cdp[0]
        lr = l2 / l1
        x = x1 + (x2 - x1) * lr
        y = y1 + (y2 - y1) * lr
        t = g1 + (g2 - g1) * lr
    elif col_1 >= last:
        # extrapolate to the right
        x1 = tdf['coordx'].iloc[i_last - 2]
        y1 = tdf['coordy'].iloc[i_last - 2]
        g1 = tdf['gl'].iloc[i_last - 2]
        x2 = tdf['coordx'].iloc[i_last - 1]
        y2 = tdf['coordy'].iloc[i_last - 1]
        g2 = tdf['gl'].iloc[i_last - 1]
        l1 = cdp[i_last - 1] - cdp[i_last - 2]
        l2 = col_1 - cdp[i_last - 1]
        lr = l2 / l1
        x = x2 + (x2 - x1) * lr
        y = y2 + (y2 - y1) * lr
        t = g2 + (g2 - g1) * lr
    return x, y, t


def get_make_srt_dir(wrk_dir: str):
    '''
    '''
    try:
        if not (wrk_dir).exists():
            logger.info('Making SORT directory...')
            wrk_dir.mkdir()
    except OSError as osx:
        logger.error(osx.args)
        sys.exit()


def zedfix_gmt(wrk_dir: str, path_dir: str, ext_file: str) -> List[int]:
    """
    Implements the following AWK action:
    awk -f zedfix_gmt.awk nm=$1 frame_top=$3 frame_bot=$5 t_top=$7 t_bot=$9 $1.path.txt $1*.gmt > $1zf.gmtf
    from the commandz.awk script

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    path_dir: str
        The path to the work folder with *.path.txt files
    ext_file: str
        The path to the combined 'extension' file for all the flight 'paths'

    Return:
    -------
    : List[int]
        The list of path identifiers read from the first column of the extent file
    """

    fm1 = "  {:{_f}}" * 7 + " {} {}\n"
    fm2 = " {:{_f}}" * 7 + " {} {}\n"
    # regex1 = re.compile('\d')   # this fails for negative numbers
    regex2 = re.compile('[+-]?([0-9]*[.])?[0-9]+')

    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    dcols = ("nm", "frame_l", "frame_top", "frame_r", "frame_bot", "t_l", "t_top", "t_r", "t_bot")
    exdf = pd.read_csv(ext_file, sep=r'\s+', names=dcols, header=None, index_col=False)

    logger.info("Testing GMT for +Z ")

    # pdf_list = []
    pcols = ("nm", "fid", "pix_x", "pix_y", "coordx", "coordy", "col7", "col8", "gl")
    for nm in exdf['nm']:
        ner = 0
        fidd = 0
        row = exdf.query("nm == @nm")
        y_scale = (row['t_bot'].iloc[0] - row['t_top'].iloc[0]) /\
                  (row['frame_bot'].iloc[0] - row['frame_top'].iloc[0])
        p_file = Path(path_dir) / f"{nm}.path.txt"
        tdf = pd.read_csv(p_file, sep=r'\s+', names=pcols, header=None, index_col=False)
        # pdf_list.append(tdf)
        frst = tdf["fid"].iloc[0] - 1
        last = tdf["fid"].iloc[-1] - 1

        gmt = Path(wrk_dir) / f"{nm}_interp.gmt"
        with open(gmt, "r") as fin:
            lin_lst = fin.readlines()
        logger.info(f"{gmt} successfully read.")
        lines = lin_lst.copy()
        with open(Path(srt_dir) / f"{nm}zf.gmtf", "w") as fou:
            while lines:
                try:
                    line = lines.pop(0).strip()
                except IndexError:
                    logger.info(f"{nm}.gmt processed")
                    break
                # if not regex1.match(line[0]) and ("@D" in line):
                if not regex2.match(line.split()[0]) and ("@D" in line):
                    with open(srt_dir / "met.bdf", mode="a") as fou1:
                        fou1.write(f"{gmt.name}|{fidd}|{line}\n")
                    fidd += 1
                    fou.write(f"# {line.split('|')[1]}\n")
                    fou.write(f"{line}\n")
                    srt_file = srt_dir / f"{nm}_{line.split('|')[1]}.srt"
                    with open(srt_file, mode="a") as fou3:
                        fou3.write(">\n")
                        fou3.write(f"{line}\n")
                # elif not regex1.match(line[0]):
                elif not regex2.match(line.split()[0]):
                    if ">" not in line:
                        with open(srt_dir / f"{nm}_hdr.hdr", mode="a") as fou2:
                            fou2.write(f"{line}\n")
                    idd = 1
                    fou.write(f"{line}\n")
                else:
                    col_1, col_2 = [float(_l) for _l in line.split()[:2]]
                    x, y, t = interpol(col_1, frst, last, tdf)
                    dpth = ((col_2 - row['frame_top'].iloc[0]) * y_scale) + row['t_top'].iloc[0]

                    if t <= dpth:
                        nyp = col_2 + (t - dpth) / y_scale
                        fou.write(fm1.format(col_1, nyp, x, y, t, t, 0, idd, fidd - 1, _f=".6f"))

                        with open(srt_file, mode="a") as fou3:
                            fou3.write(fm1.format(col_1, nyp, x, y, t, t, 0, idd, fidd - 1, _f=".6f"))
                        ner += 1
                    else:
                        fou.write(fm2.format(col_1, col_2, x, y, dpth, t, t - dpth, idd, fidd - 1, _f=".6f"))
                        with open(srt_file, mode="a") as fou3:
                            fou3.write(fm2.format(col_1, col_2, x, y, dpth, t, t - dpth, idd, fidd - 1, _f=".6f"))
                    idd += 1

            fou.write(">\n")
            logger.info(f"** Error count {ner} **\n")
            # logger.info("** See z_err.log **\n")
            fou.write("# @D0|DNDUTL|||||||||||||||||||||MAL|\n")
            for i in range(frst, last + 1):
                tmp = f"{-(row['t_top'].iloc[0] - tdf['gl'].iloc[i]) / y_scale: .6f}".rstrip('0').rstrip('.')
                fou.write(f"{i} {tmp}\n")
            fou.write(">\n")
    return exdf['nm'].tolist()


def sort_gmtp(wrk_dir: str, nm_lst: List[int]) -> None:
    """
    Implements the following actions:
    DEL /Q /F /S *Annotations.srt
    awk -f sort_gmtp.awk $1_hdr.hdr $1*.srt > $1.gmts
    ogr2ogr -f ESRI Shapefile" zf_shp/$1_zf.shp $1zf.gmtf
    from the commandz.awk script

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    nm_lst: List[int]
        The list of path identifiers from the the common extent file
    """

    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    zfshp_dir = Path(wrk_dir) / "ZF_SHP"
    if not Path(zfshp_dir).exists():
        Path(zfshp_dir).mkdir(parents=True, exist_ok=False)
    else:
        logger.warning(f"{zfshp_dir} folder already exists!")

    for nm in nm_lst:
        seg = 0
        vtx = 1
        fn = 1
        ano_list = sorted(glob.glob(os.path.join(srt_dir, "*Annotations.srt")))
        if ano_list:
            _ = [Path(_f).unlink() for _f in ano_list]
        srt_list = sorted(glob.glob(os.path.join(srt_dir, f"{nm}*.srt")))
        hdr = Path(srt_dir / f"{nm}_hdr.hdr")
        hlines = hdr.read_text().split("\n")[:-1]
        with open(Path(srt_dir) / f"{nm}.gmts", "w") as fou:
            for hline in hlines:
                fou.write(f"{hline}\n")
            for i, srt in enumerate(srt_list, 1):
                lines = Path(srt).read_text().split("\n")
                while lines:
                    try:
                        line = lines.pop(0)
                    except IndexError:
                        logger.info(f"{srt} completed")
                        break
                    if line.startswith(">"):
                        seg += 1
                        fou.write(f"{line}\n")
                        line = lines.pop(0)
                        fou.write(f"{line}\n")
                        if fn != i:
                            seg = 1
                            vtx = 1
                            fn += 1
                    elif line:
                        fou.write(f"{line} {vtx} {seg}\n")
                        vtx += 1

        in_gmtf = Path(srt_dir) / f"{nm}zf.gmtf"
        out_shp = Path(zfshp_dir) / f"{nm}_zf.shp"

        # ogr = gdaltools.ogr2ogr()
        # ogr.set_encoding("UTF-8")
        # ogr.set_input(str(in_gmtf))
        # ogr.set_output(str(out_shp))
        # ogr.execute()

        # ogr2ogr.main(["", "-f", "ESRI Shapefile", str(out_shp), str(in_gmtf)])
        cmd = [get_ogr_path(), "-f", "ESRI Shapefile", str(out_shp), str(in_gmtf)]
        subprocess.run(cmd, check=True)

        if out_shp.exists():
            logger.info(f"{nm}zf.gmtf successfully converted to {nm}_zf.shp")


def help_gr8(lin_lst: List[str], idx_d0: List[int]) -> List[int]:
    """
    Replacing the list comprehension
    idx_gr8 = [_i for _i, line in enumerate(lin_lst) if line.startswith(">")][1:]
    to find the first line starting with '>', after a meta '# @D0 ...' line
    Also removes the 'fake >' from lin_lst
    """
    idx_lst = []
    cnt = 0
    tmp = lin_lst.copy()
    for _i, line in enumerate(tmp):
        if line.startswith(">") and (_i > idx_d0[cnt]):
            idx_lst.append(_i)
            cnt += 1
    return idx_lst


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
             "ILINE\n")

    fmt = "PVRTX {:0.0f} {:6.1f} {:7.1f} {:.1f} {:.6f} {:.6f} {:.1f} {:.1f}\n"

    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    regex2 = re.compile('[+-]?([0-9]*[.])?[0-9]+')

    cdf = pd.read_csv(colors, sep=r"\s{2,}", header=0, index_col=False, engine="python")
    cdf.iloc[:, 1:4] /= 256.0

    for nm in nm_lst:
        gmts = Path(srt_dir) / f"{nm}.gmts"
        if not gmts.exists():
            continue
        lines = gmts.read_text().split("\n")
        with open(Path(srt_dir) / f"{nm}.mdc", "w") as fou:
            while lines:
                try:
                    line = lines.pop(0)
                except IndexError as _e:
                    logger.info(f"{nm}.gmts processed {_e}")
                    break
                if "@D" in line:
                    met = line.split("|")
                    gname = met[1]
                    row = cdf[cdf["Feature classes"] == gname]
                    # row = cdf.query(f"`Feature classes` == @{gname}")
                    line = lines.pop(0)
                    segn, frst = line.split()[8: 10]
                    frst = int(frst)
                    # segn = int(segn)

                    fou.write(fsctn.format(nm,
                                           segn,
                                           met[1],
                                           row['Red'].iloc[0],
                                           row['Green'].iloc[0],
                                           row['Blue'].iloc[0],
                                           nm,
                                           *met[1:20],
                                           nm))

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

    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    header = "Vertex,SegmentID,X,Y,ELEVATION,PixelX,PixelY,AusAEM_DEM,DEPTH,Type,OverAge," \
        "UnderAge,BoundConf,ContactTyp,BasisOfInt,OvrStrtUnt,OvrStratNo,OvrConf,UndStrtUnt," \
        "UndStratNo,UndConf,WithinStrt,WithinStNo,WithinConf,HydStrtType,HydStrConf,BOMNAFUnt," \
        "BOMNAFNo,InterpRef,Comment,Annotation,NewObs,Operator,Date,SURVEY_LINE\n"
    regex2 = re.compile('[+-]?([0-9]*[.])?[0-9]+')

    cdf = pd.read_csv(alt_colors, sep=r"\s{2,}", header=0, index_col=False, engine="python")
    cdf.fillna('', inplace=True)
    seg = 0

    for nm in nm_lst:
        gmts = Path(srt_dir) / f"{nm}.gmts"
        if not gmts.exists():
            continue
        lines = gmts.read_text().split("\n")
        with open(Path(srt_dir) / f"{nm}.egs", "w") as fou:
            fou.write(header)
            while lines:
                try:
                    line = lines.pop(0)
                except IndexError as _e:
                    logger.info(f"{nm}.gmts processed {_e}")
                    break
                if "@D" in line:
                    seg += 1
                    m_lst = line.split("|")
                    gnm = m_lst[1]
                    row = cdf[cdf["TYPE"] == gnm]
                    # row = cdf.query("TYPE == @gnm")
                    met = f"{gnm}",
                    f"{row['OVERAGE'].iloc[0]}",
                    f"{row['UNDERAGE'].iloc[0]}",
                    f"{','.join(str(x) for x in m_lst[2:24])}"
                    line = lines.pop(0)
                    try:
                        while regex2.match(line.split()[0]):
                            los = line.split()
                            fou.write(f"{los[9]},{los[8]},{los[2]},"
                                      f"{los[3]},{los[4]},{los[0]},"
                                      f"{los[1]},{los[5]},{los[6]},{met},{nm}\n")
                            line = lines.pop(0)
                    except IndexError:
                        pass


def second(wrk_dir: str) -> None:
    """
    From the geo-sections of the newly created GMT the files in wrk_dir folder *.asc files are
    extracted in a SORT subdirectory. If there are Annotations sections, their *.asc files will
    be deleted. It combines the following commands:
    gawk -f gmt_2_sorted.awk "$1"_interp.gmtf > sort/'$1'_interp.sort
    DEL /Q /F /S '*Annotations.asc'      (a DOS rm command)

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    """

    srt_dir = Path(wrk_dir) / "SORT"
    if not (srt_dir).exists():
        srt_dir.mkdir(parents=True, exist_ok=False)
    else:
        logger.warning(f"{srt_dir} folder already exists!")
    gmt_list = sorted(glob.glob(os.path.join(wrk_dir, '*_interp.gmt')))

    for gmt in gmt_list:
        filo = Path(gmt).name.split("_")[0]

        with open(gmt, "r") as fin:
            lin_lst = fin.readlines()

        logger.info(f"{gmt} successfully read.")
        idx_d0 = [_i for _i, line in enumerate(lin_lst) if "@D0" in line]
        # idx_gr8 = [_i for _i, line in enumerate(lin_lst) if line.startswith(">")][1:]
        idx_gr8 = help_gr8(lin_lst, idx_d0)

        if len(idx_d0) != len(idx_gr8):
            logger.warning(f"{gmt} problem: {len(idx_d0)} meta lines vs \n{len(idx_gr8)} '>' lines")
            tmp = idx_gr8[:-1]
            for _i, idx in enumerate(tmp):
                if "@D0" not in lin_lst[idx + 1]:
                    idx_gr8.pop(_i)

        for i_start, i_stop in zip(idx_d0, idx_gr8):
            if i_start > i_stop:
                logger.warning(f"GMT: {gmt}\n{i_start} > {i_stop}\n{idx_d0}\n{idx_gr8}")
            name = lin_lst[i_start].split("|")[1]

            if (srt_dir / f"{filo}_{name}.asc").exists():
                mode = "a"
            else:
                mode = "w"

            with open(srt_dir / f"{filo}_{name}.asc", mode=mode) as fout:
                fout.write(f"{name}\n")
                fout.write(lin_lst[i_start])
                fout.write("170 170 0\n")
                fout.write(f"{i_stop - i_start - 1}\n")
                fout.writelines(lin_lst[i_start + 1: i_stop])

    ano_list = sorted(glob.glob(os.path.join(srt_dir, "*Annotations.asc")))
    if ano_list:
        _ = [Path(_f).unlink() for _f in ano_list]


def third(wrk_dir: str, ext_file: str) -> List[int]:
    """
    Combines the content of the newly created *.asc files in the SORT folder with the column
    values of the common extent file to produce the *.s1 files for each flight path.
    It replaces the following command:
    gawk -f pix_2_depth.awk nm=$1 frame_top=$3 frame_bot=$5 t_top=$7 t_bot=$9 sort/$1*.asc > $1.s1

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    ext_file: str
        The path to the combined 'extension' file for all the flight 'paths'

    Return:
    -------
    : List[int]
        The list of path identifiers read from the first column of the extent file
    """

    def doer(n_vert: int, lines: List[str], row: pd.DataFrame, fout: TextIO, i_nxt: int = 0) -> int:
        """
        A helper function to avoid nested loops.
        It implements the for(x=k+1; x<=k+nv; x++){...} part of the pix_2_depth.awk script
        and returns the updated value of the index i_nxt (i.e., k=i in the script)
        """

        y_scale = (row['t_bot'].iloc[0] - row['t_top'].iloc[0]) /\
                  (row['frame_bot'].iloc[0] - row['frame_top'].iloc[0])
        for _ix in range(i_nxt + 1, n_vert + i_nxt + 1):
            los = [float(_f) for _f in lines.pop(0).split()]
            dpth = ((los[1] - row['frame_top'].iloc[0]) * y_scale) + row['t_top'].iloc[0]
            fout.write(f"PVRTX {_ix} {los[0]:.6f} {los[1]:.6f} 0.000000 {los[0]:.6f} {dpth:.6f}\n")
        for _i in range(i_nxt + 1, n_vert + i_nxt):
            fout.write(f"SEG {_i} {_i + 1}\n")
        return _i + 1

    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    dcols = ("nm", "frame_l", "frame_top", "frame_r", "frame_bot", "t_l", "t_top", "t_r", "t_bot")
    exdf = pd.read_csv(ext_file, sep=r'\s+', names=dcols, header=None, index_col=False)

    pnames = exdf['nm'].tolist()
    for nm in pnames:
        row = exdf.query("nm == @nm")
        oname = None
        if (srt_dir / f"{nm}.s1").exists():
            mode = "a"
            header = None
        else:
            mode = "w"

            header = ("GOCAD HomogeneousGroup 1\n",
                      "HEADER {\n",
                      f"name:{nm}_AEM_interp\n",
                      "}\n",
                      "TYPE PLine\n",
                      "BEGIN_MEMBERS\n")

        asc_list = sorted(glob.glob(os.path.join(srt_dir, f"{nm}*.asc")))
        if not asc_list:
            exdf.drop(exdf.index[exdf['nm'] == nm], inplace=True)
            logger.info(f"Dropping {nm} from here")
            continue
        print(nm, ": ", asc_list)
        with open(srt_dir / f"{nm}.s1", mode=mode) as fout:
            if header:
                fout.writelines(header)
                header = None

            for asc in asc_list:
                lines = Path(asc).read_text().split("\n")
                while lines:
                    try:
                        nname = lines.pop(0).split()[0]
                    except IndexError:
                        logger.info(f"{asc} completed")
                        break
                    meta = lines.pop(0) + "\n"
                    red, green, blue = (float(_c) / 255 for _c in lines.pop(0).split())
                    top8 = ("GOCAD PLine 1\n",
                            "HEADER {\n",
                            f"name:{nname}\n",
                            "*atoms:false\n",
                            f"*line*color:{red:1.6f} {green:1.6f} {blue:1.6f} 1\n",
                            "width:5\n",
                            "}\n",
                            "PROPERTIES px py gl depth\n")
                    if nname != oname:
                        if oname:
                            fout.write("END\n")
                        fout.writelines(top8)
                        i_nxt = 0
                    fout.writelines(("ILINE\n", meta))
                    n_vert = int(lines.pop(0))
                    if n_vert < 0:
                        logger.warning(f"WRX:{n_vert}\n{asc}\n")
                    try:
                        i_nxt = doer(n_vert, lines, row, fout, i_nxt)
                    except UnboundLocalError as _e:
                        logger.error(f"EX: {nm}\n{n_vert}\n{len(lines)}\n{row}\n{_e}")
                    oname = nname
            fout.write("END\n")
            fout.write("END_MEMBERS\n")
            fout.write("END")
    return exdf['nm'].tolist()


def fourth(wrk_dir: str, path_dir: str, nm_lst: List[int]) -> None:
    """
    Combines the content of the newly created *.s1 files in the SORT folder with the
    associated flight paths to produce the *.s2 files for each flight path, with
    interpolated and extrapolated coordinates.
    It replaces the following command:
    gawk -f interpolate_xyed_from_path.awk '$1'.path.txt '$1'.s1 > '$1'.s2'

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    path_dir: str
        The path to the folder with flight path files
    ext_file: str
        The path to the combined 'extension' file for all the flight 'paths'
    nm: List[int]
        The list of path identifiers from the the common extent file
    """
    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    dcols = ("nm", "fid", "pix_x", "pix_y", "coordx", "coordy", "col8", "col9", "gl")
    fmt = "PVRTX {} {:{_f}} {:{_f}} {:{_f}} {:{_f}} {:{_f}} {:{_f}} {:{_f}}\n"

    for nm in nm_lst:
        p_file = Path(path_dir) / f"{nm}.path.txt"
        tdf = pd.read_csv(p_file, sep=r'\s+', names=dcols, header=None, index_col=False)
        i_last = len(tdf)
        frst = tdf["fid"].iloc[0] - 0.5
        last = tdf["fid"].iloc[-1] - 1
        cdp = (tdf["fid"] - 1).tolist()
        s1_file = Path(srt_dir) / f"{nm}.s1"
        lines = s1_file.read_text().split("\n")

        with open(Path(srt_dir) / f"{nm}.s2", "w") as fou:
            while lines:
                try:
                    line = lines.pop(0)
                except IndexError:
                    logger.info(f"{nm}.s1 processed")
                    break
                if "PVRTX" not in line:
                    fou.write(f"{line}\n")
                else:
                    col = line.split()
                    col_5 = float(col[5])
                    if frst <= col_5 < last:
                        # interpolate
                        for idx in cdp:
                            if cdp[idx] <= col_5 < cdp[idx + 1]:
                                x1 = tdf['coordx'].iloc[idx]
                                y1 = tdf['coordy'].iloc[idx]
                                g1 = tdf['gl'].iloc[idx]
                                x2 = tdf['coordx'].iloc[idx + 1]
                                y2 = tdf['coordy'].iloc[idx + 1]
                                g2 = tdf['gl'].iloc[idx + 1]
                                l1 = cdp[idx + 1] - cdp[idx]
                                l2 = col_5 - cdp[idx]
                                lr = l2 / l1
                                x = x1 + (x2 - x1) * lr
                                y = y1 + (y2 - y1) * lr
                                t = g1 + (g2 - g1) * lr
                    elif int(col_5) <= frst:
                        # extrapolate to the left
                        x1 = tdf['coordx'].iloc[0]
                        y1 = tdf['coordy'].iloc[0]
                        g1 = tdf['gl'].iloc[0]
                        x2 = tdf['coordx'].iloc[1]
                        y2 = tdf['coordy'].iloc[1]
                        g2 = tdf['gl'].iloc[1]
                        l1 = cdp[1] - cdp[0]
                        l2 = col_5 - cdp[0]
                        lr = l2 / l1
                        x = x1 + (x2 - x1) * lr
                        y = y1 + (y2 - y1) * lr
                        t = g1 + (g2 - g1) * lr
                    elif int(col_5) >= last:
                        # extrapolate to the right
                        x1 = tdf['coordx'].iloc[i_last - 2]
                        y1 = tdf['coordy'].iloc[i_last - 2]
                        g1 = tdf['gl'].iloc[i_last - 2]
                        x2 = tdf['coordx'].iloc[i_last - 1]
                        y2 = tdf['coordy'].iloc[i_last - 1]
                        g2 = tdf['gl'].iloc[i_last - 1]
                        l1 = cdp[i_last - 1] - cdp[i_last - 2]
                        l2 = col_5 - cdp[i_last - 1]
                        lr = l2 / l1
                        x = x2 + (x2 - x1) * lr
                        y = y2 + (y2 - y1) * lr
                        t = g2 + (g2 - g1) * lr

                    fou.write(fmt.format(col[1], x, y,
                                         float(col[-1]),
                                         float(col[-2]),
                                         float(col[3]),
                                         t,
                                         float(col[-1]) - t,
                                         _f='.6f'))


def fifth(wrk_dir: str, colors: str, nm_lst: List[int], revamp: str = "") -> None:
    """
    Combines the content of the newly created *.s2 files in the SORT folder with the
    RGB color values for geo-entities from the colors file (a *.prn file) to produce
    either a *.gp or *.pl17 format file for each flight path (based on the revamp value).
    It replaces the following commands (depending on the value of the revamp parameter):
    gawk -f revamp_colr.awk New_feature_classes_20210623.prn '$1'.s2 > '$1'.gp
    gawk -f revamp_colr_2017.awk New_feature_classes_20210623.prn '$1'.s2 > '$1'.pl17

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    colors: str
        The path to the *.prn file with RGB values for geo features
    nm: List[int]
        The list of path identifiers from the the common extent file
    revamp: str
        Either '' or '2017'
    """

    fmt = "*line*color:{:{_f}} {:{_f}} {:{_f}} {}\n"
    f17 = ("GOCAD_ORIGINAL_COORDINATE_SYSTEM\n"
           'NAME " gocad Local"\n'
           'PROJECTION " GDA94 / MGA zone 53"\n'
           'DATUM " Mean Sea Level"\n'
           "AXIS_NAME X Y Z\n"
           "AXIS_UNIT m m m\n"
           "ZPOSITIVE Elevation\n"
           "END_ORIGINAL_COORDINATE_SYSTEM\n"
           "GEOLOGICAL_FEATURE {}_AEM_interp\n"
           )

    sfx_dic = {"": "gp", "2017": "pl17"}
    sfx = sfx_dic.get(revamp)

    cdf = pd.read_csv(colors, sep=r"\s{2,}", header=0, index_col=False)
    cdf.iloc[:, 1:4] /= 256.0

    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    for nm in nm_lst:
        s2_file = Path(srt_dir) / f"{nm}.s2"
        lines = s2_file.read_text().split("\n")[:-1]  # skip the empty bottom line
        with open(Path(srt_dir) / f"{nm}.{sfx}", "w") as fou:
            while lines:
                try:
                    line = lines.pop(0)
                except IndexError:
                    logger.info(f"{nm}.s2 processed")
                    break
                if ("GOCAD HomogeneousGroup 1" in line) and (revamp == "2017"):
                    for _ in range(6):
                        line = lines.pop(0)
                if ("END_MEMBERS" in line) and (revamp == "2017"):
                    logger.info(f"{nm}.s2 reached the EOF")
                    break
                if "GOCAD PLine 1" in line:
                    fou.write(f"{line}\n")
                    line = lines.pop(0)
                    fou.write(f"{line}\n")
                    line = lines.pop(0)
                    gname = line.split(":")[1].strip()
                    fou.write(f"{line}\n")
                    row = cdf[cdf["Feature classes"] == gname]
                    # row = cdf.query(f"`Feature classes` == @{gname}")
                    line = lines.pop(0)
                    fou.write(f"{line}\n")
                    fou.write(fmt.format(row['Red'].iloc[0],
                                         row['Green'].iloc[0],
                                         row['Blue'].iloc[0],
                                         1,
                                         _f='.6f'))
                    _ = lines.pop(0)
                    if revamp == "2017":
                        fou.write("use_feature_color: false\n")
                        line = lines.pop(0)
                        fou.write(f"{line}\n")
                        line = lines.pop(0)
                        fou.write(f"{line}\n")
                        fou.write(f17.format(nm))
                else:
                    fou.write(f"{line}\n")


def fifth_b(wrk_dir: str, colors: str, nm_lst: List[int], revamp: str = "") -> None:
    """
    Combines the content of the newly created *.s2 files in the SORT folder with the
    RGB color values for geo-entities from the colors file (a *.prn file) to produce
    either a 'Hrz' or 'Sctn' format file for each flight path (based on the revamp value).
    The file extensions are *.hmdc and *smdc, respectively.
    It replaces the following commands (depending on the value of the revamp parameter):
    gawk -f revamp_colr_met_hrz.awk New_feature_classes_20210623.prn '$1'.s2 > '$1'.hmdc
    gawk -f revamp_colr_met_sctn.awk New_feature_classes_20210623.prn '$1'.s2 > '$1'.smdc

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    colors: str
        The path to the *.prn file with RGB values for geo features
    nm: List[int]
        The list of path identifiers from the the common extent file
    revamp: str
        Either 'hrz' or 'sctn'
    """

    fsctn = ("GOCAD PLine 1\n"
             "HEADER {{\n"
             "name:{}_{}_{}\n"
             "*atoms:false\n"
             "*line*color:{:.6f} {:.6f} {:.6f} 1\n"
             "use_feature_color: false\n"
             "width:5\n"
             "*metadata*Line: {}\n"
             "*metadata*Type: {}\n"
             "*metadata*BoundConf: {}\n"
             "*metadata*ContactTyp: {}\n"
             "*metadata*BasisOfInt: {}\n"
             "*metadata*OvrStrtUnt: {}\n"
             "*metadata*OvrStratNo: {}\n"
             "*metadata*OvrConf: {}\n"
             "*metadata*UndStrtUnt: {}\n"
             "*metadata*UndStratNo: {}\n"
             "*metadata*UndConf: {}\n"
             "*metadata*WithinStrt: {}\n"
             "*metadata*WithinStNo: {}\n"
             "*metadata*WithinConf: {}\n"
             "*metadata*HydStrtType: {}\n"
             "*metadata*HydStrConf: {}\n"
             "*metadata*BOMNAFUnt: {}\n"
             "*metadata*BOMNAFNo: {}\n"
             "*metadata*InterpRef: {}\n"
             "*metadata*Comment: {}\n"
             "*metadata*Annotation: {}\n"
             "*metadata*NewObs: {}\n"
             "*metadata*Operator: {}\n"
             "*metadata*Date: {}\n"
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
             )

    sfx_dic = {"hrz": "hmdc", "sctn": "smdc"}
    sfx = sfx_dic.get(revamp)

    cdf = pd.read_csv(colors, sep=r"\s{2,}", header=0, index_col=False)
    cdf.iloc[:, 1:4] /= 256.0

    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    for nm in nm_lst:
        seg = 1
        s2_file = Path(srt_dir) / f"{nm}.s2"
        lines = s2_file.read_text().split("\n")[:-1]  # skip the empty bottom line
        with open(Path(srt_dir) / f"{nm}.{sfx}", "w") as fou:
            while lines:
                try:
                    line = lines.pop(0)
                except IndexError:
                    logger.info(f"{nm}.s2 processed")
                    break
                if "GOCAD HomogeneousGroup 1" in line:
                    for _ in range(6):
                        line = lines.pop(0)
                if line.endswith("END"):
                    line = lines.pop(0)
                if "GOCAD PLine 1" in line:
                    for _ in range(8):
                        line = lines.pop(0)
                if "ILINE" in line:
                    line = lines.pop(0)
                    met = line.split("|")
                    met[-1] = met[-1].rstrip()
                    gname = met[1]
                    row = cdf[cdf["Feature classes"] == gname]
                    # row = cdf.query("`Feature classes` == @gname")
                    if seg > 1:
                        fou.write("END\n")
                    if revamp == "sctn":
                        gfeat = nm
                    else:  # hrz
                        gfeat = met[1]
                    fou.write(fsctn.format(nm, seg, met[1],
                              row['Red'].iloc[0], row['Green'].iloc[0], row['Blue'].iloc[0],
                              nm,
                              *met[1:],
                              gfeat
                              ))
                    seg += 1
                    if (revamp == "hrz") and ("fault" in met[1]):
                        fou.write("GEOLOGICAL_TYPE fault\n")
                    fou.write("ILINE\n")
                else:
                    if "END_MEMBERS" in line:
                        line = lines.pop(0)
                    else:
                        if line.endswith("END"):
                            line = lines.pop(0)
                        else:
                            fou.write(f"{line}\n")
            fou.write("END")


def sixth(wrk_dir: str, nm_lst: List[int]) -> None:
    """
    Simply writes the XML format header file for each flight path.
    Replaces the command:
    gawk -f xml.awk '$1'.gp  > '$1'_interp.xml

    Parameters:
    ----------
    wrk_dir: str
        The path to the existing work folder
    nm: List[int]
        The list of path identifiers from the the common extent file
    """

    srt_dir = Path(wrk_dir) / "SORT"
    get_make_srt_dir(srt_dir)

    for nm in nm_lst:
        with open(Path(srt_dir) / f"{nm}.xml", "w") as fou:
            fou.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            fou.write("<Layer version=\"1\" layerType=\"ModelLayer\">\n")
            fou.write(f"<DisplayName>{nm} Interp</DisplayName>\n")
            fou.write(f"<URL>{nm}.gp</URL>\n")
            fou.write("<DataFormat>GOCAD</DataFormat>\n")
            fou.write("<LineWidth>5</LineWidth>\n")
            fou.write(f"<DataCacheName>GA/EFTF/AEM/{nm}.gp</DataCacheName>\n")
            fou.write("<CoordinateSystem>EPSG:28353</CoordinateSystem>\n")
            fou.write("</Layer>\n")


def main(configuration: dict) -> None:
    shape_files_directory = configuration['dir']
    working_directory = configuration['workdir']
    extent_file_path = configuration['extent']
    path_files_directory = configuration['pathdir']
    colors_file_path = configuration['colors']
    features_file_path = configuration['features']

    output_folder = configuration['output_folder']
    working_directory = output_folder

    # logger.add(f"{output_folder}/aem_workflow.log", format="{time:YYYY-MM-DD at HH:mm:ss} {level} {message}")
    logger.info(f"Yes, we got here with title: {configuration['title']}")

    first(shape_files_directory, working_directory)
    nn_lst = zedfix_gmt(working_directory, path_files_directory, extent_file_path)
    sort_gmtp(working_directory, nn_lst)
    gmts_2_mdc(working_directory, colors_file_path, nn_lst)
    gmts_2_egs(working_directory, features_file_path, nn_lst)

    logger.warning('warning test completed...')
    logger.error('error test completed...')
    logger.warning('warning test completed...')
    logger.error('error test completed...')
    logger.warning('warning test completed...')
    logger.error('error test completed...')
    logger.error('error test completed...')
    logger.info('Processing completed...')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", "-d", required=True, help="Path to the dir with SHP files")
    ap.add_argument("--workdir", "-w", required=True, help="Path to the work dir")
    ap.add_argument("--extent", "-e", required=False, help="Path to the extent file")
    ap.add_argument("--pathdir", "-p", required=False, help="Path to the dir with path files")
    ap.add_argument("--colors", "-c", required=False, help="Path to the file with RGB colors")
    ap.add_argument("--features", "-f", required=False, help="Path to the split feature classes file")
    # ap.add_argument('--revamp', "-r",
    # default="all",
    # const="all",
    # nargs='?',
    # choices=["all", "", "2017", "hrz", "sctn"],
    # help='choose the revamp option')
    ARG = vars(ap.parse_args())
    first(ARG["dir"], ARG["workdir"])
    nn_lst = zedfix_gmt(ARG["workdir"], ARG["pathdir"], ARG['extent'])
    sort_gmtp(ARG["workdir"], nn_lst)
    gmts_2_mdc(ARG["workdir"], ARG["colors"], nn_lst)
    gmts_2_egs(ARG["workdir"], ARG["features"], nn_lst)

    # second(ARG["workdir"])
    # nn_lst = third(ARG["workdir"], ARG["extent"])
    # fourth(ARG["workdir"], ARG["pathdir"], nn_lst)
    # nn_lst = [1057001, 1058001, 1058002, 1059001, 1060001, 1061001]
    # if ARG["revamp"] in ("", "2017"):
    # fifth(ARG["workdir"], ARG["colors"], nn_lst, ARG["revamp"])
    # elif ARG["revamp"] in ("sctn", "hrz"):
    # fifth_b(ARG["workdir"], ARG["colors"], nn_lst, ARG["revamp"])
    # elif ARG["revamp"] == "all":
    # for ramp in ("", "2017"):
    # fifth(ARG["workdir"], ARG["colors"], nn_lst, ramp)
    # for ramp in ("sctn", "hrz"):
    # fifth_b(ARG["workdir"], ARG["colors"], nn_lst, ramp)
    # sixth(ARG["workdir"], nn_lst)
