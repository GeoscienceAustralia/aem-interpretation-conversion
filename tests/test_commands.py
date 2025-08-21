import pytest
import pandas as pd
from pathlib import Path
from unittest import mock
import os

import scripts.commands as commands


def test_interpol():
    df = pd.DataFrame({
        'fid': [1, 2],
        'coordx': [10.0, 20.0],
        'coordy': [100.0, 200.0],
        'gl': [5.0, 15.0]
    })
    col_1 = 0.5
    frst = 0
    last = 1
    x, y, t = commands.interpol(col_1, frst, last, df)
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert isinstance(t, float)

def test_interpol_extrapolate_left():
    df = pd.DataFrame({
        'fid': [1, 2],
        'coordx': [10.0, 20.0],
        'coordy': [100.0, 200.0],
        'gl': [5.0, 15.0]
    })
    col_1 = 0.5
    frst = 1
    last = 2
    x, y, t = commands.interpol(col_1, frst, last, df)
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert isinstance(t, float)

def test_interpol_extrapolate_right():
    df = pd.DataFrame({
        'fid': [1, 2],
        'coordx': [10.0, 20.0],
        'coordy': [100.0, 200.0],
        'gl': [5.0, 15.0]
    })
    col_1 = 2
    frst = 0
    last = 1
    x, y, t = commands.interpol(col_1, frst, last, df)
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert isinstance(t, float)

def test_get_make_srt_dir_creates_dir(tmp_path):
    srt_dir = tmp_path / "SORT"
    with mock.patch("pathlib.Path.exists", return_value=False):
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            commands.get_make_srt_dir(srt_dir)
            mock_mkdir.assert_called()

def test_get_make_srt_dir_oserror(tmp_path):
    srt_dir = tmp_path / "SORT"
    with mock.patch("pathlib.Path.exists", side_effect=OSError("fail")):
        with pytest.raises(SystemExit):
            commands.get_make_srt_dir(srt_dir)

# def test_sort_gmtp_creates_dirs(tmp_path):
#     nm_lst = [123, 456]
#     with mock.patch("pathlib.Path.exists", return_value=False):
#         with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
#             with mock.patch("glob.glob", return_value=[]):
#                 with mock.patch("subprocess.run") as mock_run:
#                     commands.sort_gmtp(str(tmp_path), nm_lst)
#                     mock_mkdir.assert_called()
#                     mock_run.assert_called()

def test_first_runs_gdal_command(tmp_path):
    shp_dir = tmp_path
    wrk_dir = tmp_path / "work"
    shp_file = tmp_path / "test_interp_1.shp"
    shp_file.touch()
    with mock.patch("glob.glob", return_value=[str(shp_file)]):
        with mock.patch("subprocess.run") as mock_run:
            with mock.patch("scripts.commands.get_ogr_path", return_value="ogr2ogr"):
                commands.first(str(shp_dir), str(wrk_dir))
                mock_run.assert_called()

def test_second_writes_asc_file_to_sort_dir(tmp_path):
    wrk_dir = tmp_path / "work"
    filo = "test"
    name = "data"
    gmt_file = tmp_path / f"{filo}_interp_1.gmt"
    gmt_file.touch()
    gmt_file.write_text(f"@D0|{name}|{name}\n>@D0|{name}|{name}\n>")
    with mock.patch("glob.glob", return_value=[str(gmt_file)]):
        commands.second(str(wrk_dir))
        assert(os.path.exists(wrk_dir / "SORT" / f"{filo}_{name}.asc"))

def test_third_writes_s1_file_to_sort_dir(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / "SORT"
    srt_dir.mkdir()
    name = "name"
    asc_file = srt_dir / f"{name}.asc"
    asc_file.touch()
    df = pd.DataFrame({
        'nm': [name]
    })
    with mock.patch("scripts.commands.pd.read_csv", return_value=df):
        commands.third(str(wrk_dir), "ext_file")
        assert(os.path.exists(srt_dir / f"{name}.s1"))

def test_fourth_writes_s2_file_to_sort_dir(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / "SORT"
    srt_dir.mkdir()
    name = 0
    s1_file = srt_dir / f"{name}.s1"
    s1_file.touch()
    col_5_interpolate = 0.6
    col_5_extrapolate_left = 0
    col_5_extrapolate_right = 3
    s1_file.write_text(f"""
    PVRTX x x 1 1 {col_5_interpolate}\n
    PVRTX x x 1 1 {col_5_extrapolate_left}\n
    PVRTX x x 1 1 {col_5_extrapolate_right}\n>"
    """)
    df = pd.DataFrame({
        'fid': [1, 2],
        'coordx': [10.0, 20.0],
        'coordy': [100.0, 200.0],
        'gl': [5.0, 15.0]
    })
    with mock.patch("scripts.commands.pd.read_csv", return_value=df):
        commands.fourth(str(wrk_dir), str(srt_dir), [name])
        s2_file = (srt_dir / f"{name}.s2").read_text()
        assert 'PVRTX x 16.000000 160.000000 0.600000 1.000000 1.000000 11.000000 -10.400000' in s2_file
        assert 'PVRTX x 10.000000 100.000000 0.000000 1.000000 1.000000 5.000000 -5.000000' in s2_file
        assert 'PVRTX x 40.000000 400.000000 3.000000 1.000000 1.000000 35.000000 -32.000000' in s2_file

def test_main_runs_all(monkeypatch):
    config_dict = {
        'dir': 'dir',
        'workdir': 'workdir',
        'extent': 'extent',
        'pathdir': 'pathdir',
        'colors': 'colors',
        'features': 'features',
        'output_folder': 'output_folder',
        'title': 'title'
    }
    monkeypatch.setattr(commands, "first", lambda *a, **kw: None)
    monkeypatch.setattr(commands, "zedfix_gmt", lambda *a, **kw: [1, 2])
    monkeypatch.setattr(commands, "sort_gmtp", lambda *a, **kw: None)
    monkeypatch.setattr(commands, "gmts_2_mdc", lambda *a, **kw: None)
    monkeypatch.setattr(commands, "gmts_2_egs", lambda *a, **kw: None)
    commands.main(config_dict)