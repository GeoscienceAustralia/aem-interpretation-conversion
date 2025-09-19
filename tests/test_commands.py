import pytest
import pandas as pd
from unittest import mock
import os

import aemworkflow.commands as commands


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
    srt_dir = tmp_path / 'SORT'
    with mock.patch('pathlib.Path.exists', return_value=False):
        with mock.patch('pathlib.Path.mkdir') as mock_mkdir:
            commands.get_make_srt_dir(srt_dir)
            mock_mkdir.assert_called()

def test_get_make_srt_dir_oserror(tmp_path):
    srt_dir = tmp_path / 'SORT'
    with mock.patch('pathlib.Path.exists', side_effect=OSError('fail')):
        with pytest.raises(SystemExit):
            commands.get_make_srt_dir(srt_dir)

def test_sort_gmtp_creates_dirs(tmp_path):
    name = "name"
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    hdr_file = srt_dir / f'{name}_hdr.hdr'
    hdr_file.touch()
    with mock.patch('pathlib.Path.exists', return_value=False):
        with mock.patch('pathlib.Path.mkdir') as mock_mkdir:
            with mock.patch('glob.glob', return_value=[]):
                with mock.patch('aemworkflow.commands.run_command') as mock_run:
                    with mock.patch('aemworkflow.commands.validate_file', return_value=True):
                        commands.sort_gmtp(str(tmp_path), [name])
                        mock_mkdir.assert_called()
                        mock_run.assert_called()

def test_gmts_2_mdc_writes_mdc_file(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    name = "name"
    df = pd.DataFrame({
        'Feature classes': ['gname'],
        'Red': [10.0],
        'Green': [100.0],
        'Blue': [5.0]
    })
    gmts_file = srt_dir / f'{name}.gmts'
    gmts_file.touch()
    gmts_file.write_text("@D|gname|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19\n 1 2 3 4 5 6 7 8 9 10")
    with mock.patch("aemworkflow.commands.pd.read_csv", return_value=df):
        commands.gmts_2_mdc(str(wrk_dir), 'colors_file', [name])
        mdc_file = srt_dir / f'{name}.mdc'
        assert(os.path.exists(mdc_file))
        mdc_content = mdc_file.read_text()
        assert 'gname' in mdc_content
        assert '*line*color:0.039062 0.390625 0.019531 1' in mdc_content

def test_gmts_2_egs_writes_egs_file(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    name = 'gname'
    df = pd.DataFrame({
        'TYPE': ['gname'],
        'OVERAGE': [10.0],
        'UNDERAGE': [100.0],
        'Blue': [5.0]
    })
    gmts_file = srt_dir / f'{name}.gmts'
    gmts_file.touch()
    gmts_file.write_text("@D|gname|1|2|3|4|5|6|7|8\n 1 2 3 4 5 6 7 8 9 10")
    with mock.patch("aemworkflow.commands.pd.read_csv", return_value=df):
        commands.gmts_2_egs(str(wrk_dir), 'alt-colors', [name])
        egs_file = srt_dir / f'{name}.egs'
        assert(os.path.exists(egs_file))
        egs_content = egs_file.read_text()
        assert f"10,9,3,4,5,1,2,6,7,('{name}',),{name}" in egs_content

def test_zedfix_gmt_returns_path_identifiers(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    filo_1 = 'test1'
    filo_2 = 'test2'
    gmt_file_1 = tmp_path / f'{filo_1}_interp.gmt'
    gmt_file_2 = tmp_path / f'{filo_2}_interp.gmt'
    gmt_file_1.touch()
    gmt_file_2.touch()
    gmt_file_1.write_text(f'@D0|{filo_1}|{filo_1}\n>@D0|{filo_1}|{filo_1}\n>')
    gmt_file_2.write_text(f'@D0|{filo_2}|{filo_2}\n>@D0|{filo_2}|{filo_2}\n>')
    df = pd.DataFrame({
        'nm': [filo_1, filo_2],
        't_bot': [1, 2],
        't_top': [2, 3],
        'frame_bot': [3, 4],
        'frame_top': [4, 5]
    })
    df2 = pd.DataFrame({
        'fid': [1, 2],
        'gl': [5.0, 15.0]
    })
    with mock.patch("aemworkflow.commands.pd.read_csv", side_effect=[df, df2, df2]):
        names = commands.zedfix_gmt(str(wrk_dir), 'path_dir', 'ext_file')
        assert names == [filo_1, filo_2]

def test_first_runs_gdal_command(tmp_path):
    shp_dir = tmp_path
    wrk_dir = tmp_path / 'work'
    shp_file = tmp_path / 'test_interp_1.shp'
    shp_file.touch()
    with mock.patch("glob.glob", return_value=[str(shp_file)]):
        with mock.patch("aemworkflow.commands.run_command") as mock_run:
            with mock.patch("aemworkflow.commands.get_ogr_path", return_value="ogr2ogr"):
                commands.first(str(shp_dir), str(wrk_dir))
                mock_run.assert_called()

def test_second_writes_asc_file_to_sort_dir(tmp_path):
    wrk_dir = tmp_path / "work"
    filo = "test"
    name = "name"
    gmt_file = tmp_path / f"{filo}_interp_1.gmt"
    gmt_file.touch()
    gmt_file.write_text(f'@D0|{name}|{name}\n>@D0|{name}|{name}\n>')
    with mock.patch('glob.glob', return_value=[str(gmt_file)]):
        commands.second(str(wrk_dir))
        assert(os.path.exists(wrk_dir / 'SORT' / f'{filo}_{name}.asc'))

def test_third_writes_s1_file_to_sort_dir(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    name = 'name'
    asc_file = srt_dir / f'{name}.asc'
    asc_file.touch()
    asc_file.write_text(f'1\n2\n3 4 5\n1\n5 6 7\n8 9 10\n11 12 13\n14 15 16\n1\n17 18 19')
    df = pd.DataFrame({
        'nm': [name],
        't_bot': [1],
        't_top': [2],
        'frame_bot': [3],
        'frame_top': [4]
    })
    with mock.patch("aemworkflow.commands.pd.read_csv", return_value=df):
        commands.third(str(wrk_dir), "ext_file")
        assert(os.path.exists(srt_dir / f"{name}.s1"))

def test_fourth_writes_s2_file_to_sort_dir(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    name = "name"
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
    with mock.patch("aemworkflow.commands.pd.read_csv", return_value=df):
        commands.fourth(str(wrk_dir), str(srt_dir), [name])
        s2_file = (srt_dir / f'{name}.s2').read_text()
        assert 'PVRTX x 16.000000 160.000000 0.600000 1.000000 1.000000 11.000000 -10.400000' in s2_file
        assert 'PVRTX x 10.000000 100.000000 0.000000 1.000000 1.000000 5.000000 -5.000000' in s2_file
        assert 'PVRTX x 40.000000 400.000000 3.000000 1.000000 1.000000 35.000000 -32.000000' in s2_file

def test_fifth_writes_gp_file_to_sort_dir(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    name = "name"
    s2_file = srt_dir / f"{name}.s2"
    s2_file.touch()
    s2_file.write_text('GOCAD PLine 1\nline:1\nline:gname\nline:next\nline:last\n')
    df = pd.DataFrame({
        'Feature classes': ['gname'],
        'Red': [10.0],
        'Green': [100.0],
        'Blue': [5.0]
    })
    with mock.patch("aemworkflow.commands.pd.read_csv", return_value=df):
        commands.fifth(str(wrk_dir), 'colors_file', [name])
        assert(os.path.exists(srt_dir / f"{name}.gp"))

def test_fifth_b_writes_hmdc_file_to_sort_dir(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    name = "name"
    s2_file = srt_dir / f"{name}.s2"
    s2_file.touch()
    s2_file.write_text('ILINE\nline|gname|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22\n')
    df = pd.DataFrame({
        'Feature classes': ['gname'],
        'Red': [0],
        'Green': [0],
        'Blue': [0]
    })
    with mock.patch("aemworkflow.commands.pd.read_csv", return_value=df):
        commands.fifth_b(str(wrk_dir), 'colors_file', [name], 'hrz')
        assert(os.path.exists(srt_dir / f"{name}.hmdc"))

def test_sixth_writes_xml_format_header_files(tmp_path):
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    name = "name"
    commands.sixth(str(wrk_dir), [name])
    xml_file = (srt_dir / f'{name}.xml').read_text()
    assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" in xml_file
    assert "<Layer version=\"1\" layerType=\"ModelLayer\">\n" in xml_file
    assert f"<DisplayName>{name} Interp</DisplayName>\n" in xml_file
    assert f"<URL>{name}.gp</URL>\n" in xml_file
    assert "<DataFormat>GOCAD</DataFormat>\n" in xml_file
    assert "<LineWidth>5</LineWidth>\n" in xml_file
    assert f"<DataCacheName>GA/EFTF/AEM/{name}.gp</DataCacheName>\n" in xml_file
    assert "<CoordinateSystem>EPSG:28353</CoordinateSystem>\n" in xml_file
    assert "</Layer>\n" in xml_file

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
    
