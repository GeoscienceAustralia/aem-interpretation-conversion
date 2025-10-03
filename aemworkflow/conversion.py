import os
import glob
import re
import warnings

from pathlib import Path
import pandas as pd
from typing import List, Tuple
from osgeo import osr
from loguru import logger
from aemworkflow.utilities import get_ogr_path, get_make_srt_dir, validate_file, run_command


def conversion_zedfix_gmt_to_srt(wrk_dir: str, path_dir: str, ext_file: str, logger_session=logger) -> List[int]:
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
    logger_session.info("Running zedfix_gmt_to_srt conversion.")

    try:
        fm1 = "  {:{_f}}" * 7 + " {} {}\n"
        fm2 = " {:{_f}}" * 7 + " {} {}\n"
        # regex1 = re.compile('\d')   # this fails for negative numbers
        regex2 = re.compile('[+-]?([0-9]*[.])?[0-9]+')

        srt_dir = Path(wrk_dir) / "SORT"
        get_make_srt_dir(srt_dir, logger_session=logger)

        dcols = ("nm", "frame_l", "frame_top", "frame_r", "frame_bot", "t_l", "t_top", "t_r", "t_bot")
        exdf = pd.read_csv(ext_file, sep=r'\s+', names=dcols, header=None, index_col=False)

        logger_session.info("Testing GMT for +Z ")

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

            gmt = Path(wrk_dir) / 'interp' / f"{nm}_interp.gmt"

            with open(gmt, "r") as fin:
                lin_lst = fin.readlines()
            logger_session.info(f"{nm}_interp.gmt successfully read.")
            lines = lin_lst.copy()

            with open(Path(srt_dir) / f"{nm}zf.gmtf", "w") as fou:
                while lines:
                    try:
                        line = lines.pop(0).strip()
                    except IndexError:
                        logger_session.info(f"{nm}.gmt processed")
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
                            # first_col = t - dpth
                            nyp = col_2 + (t - dpth) / y_scale
                            fou.write(fm1.format(col_1, nyp, x, y, t, t, 0, idd, fidd - 1, _f=".6f"))
                            with open(srt_file, mode="a") as fou3:
                                fou3.write(fm1.format(col_1, nyp, x, y, t, t, 0, idd, fidd - 1, _f=".6f"))
                                # fou3.write(fm1.format(col_1, nyp, x, y, t, t, 0, idd, _f=".6f"))

                            ner += 1
                        else:
                            fou.write(fm2.format(col_1, col_2, x, y, dpth, t, t - dpth, idd, fidd - 1, _f=".6f"))
                            with open(srt_file, mode="a") as fou3:
                                fou3.write(fm2.format(col_1, col_2, x, y, dpth, t, t - dpth, idd, fidd - 1, _f=".6f"))
                                # fou3.write(fm2.format(col_1, col_2, x, y, dpth, t, t - dpth, idd, _f=".6f"))
                        idd += 1

                fou.write(">\n")
                logger_session.info(f"** Error count {ner} **\n")
                # logger_session.info("** See z_err.log **\n")
                fou.write("# @D0|DNDUTL|||||||||||||||||||||MAL|\n")
                for i in range(frst, last + 1):
                    tmp = f"{-(row['t_top'].iloc[0] - tdf['gl'].iloc[i]) / y_scale: .6f}"\
                        .rstrip('0').rstrip('.')
                    fou.write(f"{i} {tmp}\n")
                fou.write(">\n")

        logger_session.info("Completed zedfix_gmt_to_srt conversion.")

        return exdf['nm'].tolist()
    except Exception as e:
        logger_session.error(f"Error during zedfix_gmt_to_srt conversion: {e}")
        return []


def conversion_sort_gmtp_3d(wrk_dir: str, nm_lst: List[int], crs: str, logger_session=logger) -> None:
    logger_session.info("Running sort_gmtp_3d conversion.")
    try:
        proj = osr.SpatialReference()
        proj.ImportFromEPSG(int(crs))
        result_wkt = proj.ExportToWkt()
        result_wkt = result_wkt.replace('"', '\\"')
        result_proj = proj.ExportToProj4()
        # print(f'epsg resutl is: {result_wkt}')
        # print(f'proj string is: {result_proj}')
        del proj

        srt_dir = Path(wrk_dir) / "SORT"
        get_make_srt_dir(srt_dir, logger_session=logger)

        zfshp_dir = Path(wrk_dir) / "ZF_SHP"
        if not Path(zfshp_dir).exists():
            Path(zfshp_dir).mkdir(parents=True, exist_ok=False)
        else:
            logger_session.warning(f"{zfshp_dir} folder already exists!")

        for nm in nm_lst:
            ano_list = sorted(glob.glob(os.path.join(srt_dir, "*Annotations.srt")))
            if ano_list:
                _ = [Path(_f).unlink() for _f in ano_list]

            srt_list = sorted(glob.glob(os.path.join(srt_dir, f"{nm}*.srt")))
            hdr = Path(srt_dir / f"{nm}_hdr.hdr")
            with open(Path(srt_dir) / f"{nm}.gmtsddd", "w") as fou:
                with open(hdr, 'r') as hdr_file:
                    for line in hdr_file:
                        fields = line.strip().split()
                        if len(fields) > 0:
                            if "@VGMT1" in fields[1]:
                                fou.write(f"{line}")
                            elif "@R" in fields[1]:
                                fou.write(f"{line}")
                                fou.write(f"# @Je{crs}\n")
                                fou.write(f'# @Jp"{result_proj}"\n')
                                fou.write(f'# @Jw"{result_wkt}"\n')
                            elif "@NId" in fields[1]:
                                hd3 = line.split("# @NId")
                                fou.write(f"# @NFID_|Entity{hd3[1]}")
                            elif "@Tinteger" in fields[1]:
                                hd4 = line.split("# @Tinteger")
                                fou.write(f"# @Tdouble|string{hd4[1]}")
                            elif "FEATURE_DATA" in fields[1]:
                                fou.write(f"{line}")

                for i, srt in enumerate(srt_list, 1):
                    vtx = 1
                    seg = 0
                    with open(srt, 'r') as srt_file:
                        for line in srt_file:
                            fields = line.strip().split()
                            if len(fields) > 0:
                                if fields[0] == ">":
                                    seg += 1
                                    fou.write(f"{line.strip()}\n")
                                    next_line = next(srt_file).strip()
                                    met = next_line.split("# @D0")
                                    fou.write(f"# @D0|3DPolyline{met[1]}\n")
                                else:
                                    # fou.write(fields[2], fields[3], fields[4], fields[0], fields[1], fields[5],
                                    # fields[6], fields[7], fields[8], vtx, seg)
                                    fou.write(" ".join([fields[2], fields[3], fields[4], fields[0],
                                                        fields[1], fields[5], fields[6], fields[7],
                                                        fields[8], str(vtx), str(seg)]) + "\n")
                                    vtx += 1

            in_gmtf = Path(srt_dir) / f"{nm}zf.gmtf"
            out_shp = Path(zfshp_dir) / f"{nm}_zf.shp"

            # ogr2ogr.main(["", "-f", "ESRI Shapefile", str(out_shp), str(in_gmtf)])
            cmd = [get_ogr_path(), "-f", "ESRI Shapefile", str(out_shp), str(in_gmtf)]
            if not validate_file(in_gmtf):
                return
            run_command(cmd)

            if out_shp.exists():
                logger_session.info(f"{nm}zf.gmtf successfully converted to {nm}_zf.shp")

        logger_session.info("Completed sort_gmtp conversion.")
    except Exception as e:
        logger_session.error(f"Error during sort_gmtp_3d conversion: {e}")
        return


def conversion_sort_gmtp(wrk_dir: str, nm_lst: List[int], logger_session=logger) -> None:
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
    logger_session.info("Running sort_gmtp conversion.")

    try:
        srt_dir = Path(wrk_dir) / "SORT"
        get_make_srt_dir(srt_dir, logger_session=logger)

        zfshp_dir = Path(wrk_dir) / "ZF_SHP"
        if not Path(zfshp_dir).exists():
            Path(zfshp_dir).mkdir(parents=True, exist_ok=False)
        else:
            logger_session.warning(f"{zfshp_dir} folder already exists!")

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
                            logger_session.info(f"{srt} completed")
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

            # ogr2ogr.main(["", "-f", "ESRI Shapefile", str(out_shp), str(in_gmtf)])
            cmd = [get_ogr_path(), "-f", "ESRI Shapefile", str(out_shp), str(in_gmtf)]
            if not validate_file(in_gmtf):
                return
            run_command(cmd)

            if out_shp.exists():
                logger_session.info(f"{nm}zf.gmtf successfully converted to {nm}_zf.shp")

        logger_session.info("Completed sort_gmtp conversion.")
    except Exception as e:
        logger_session.error(f"Error during sort_gmtp conversion: {e}")
        return


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

    try:
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
    except Exception as e:
        logger.error(f"Error during interpolation: {e}")


def main(input_directory: str, output_directory: str, crs=28349) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        work_dir = output_directory
        path_dir = input_directory

        active_extent_out_file_path = os.path.join(output_directory, 'interp', 'active_extent.txt')
        return_list = conversion_zedfix_gmt_to_srt(work_dir, path_dir, active_extent_out_file_path)

        nm_list = return_list
        conversion_sort_gmtp_3d(work_dir, nm_list, crs)


if __name__ == "__main__":
    main()
