import os
from unittest import mock
import pandas as pd

import aemworkflow.conversion as conversion

logger_session = mock.MagicMock()

def test_make_srt_dir_creates_dir(tmp_path):
    wrk_dir = tmp_path
    with mock.patch("pathlib.Path.exists", return_value=False):
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            conversion.make_srt_dir(wrk_dir, logger_session)
            mock_mkdir.assert_called()

def test_conversion_zedfix_gmt_returns_path_identifiers(tmp_path):
    wrk_dir = tmp_path
    int_dir = wrk_dir / "interp"
    int_dir.mkdir()
    filo_1 = "test1"
    filo_2 = "test2"
    gmt_file_1 = int_dir / f"{filo_1}_interp.gmt"
    gmt_file_2 = int_dir / f"{filo_2}_interp.gmt"
    gmt_file_1.touch()
    gmt_file_2.touch()
    gmt_file_1.write_text(f"@D0|{filo_1}|{filo_1}\n>@D0|{filo_1}|{filo_1}\n>")
    gmt_file_2.write_text(f"@D0|{filo_2}|{filo_2}\n>@D0|{filo_2}|{filo_2}\n>")
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
    with mock.patch("aemworkflow.conversion.pd.read_csv", side_effect=[df, df2, df2]):
        names = conversion.conversion_zedfix_gmt_to_srt(str(wrk_dir), 'path_dir', 'ext_file', logger_session)
        assert names == [filo_1, filo_2]


def test_sort_gmtp_3d_creates_dirs_and_writes_gmtsddd_file(tmp_path):
    name = "name"
    wrk_dir = tmp_path
    srt_dir = wrk_dir / 'SORT'
    srt_dir.mkdir()
    hdr_file = srt_dir / f'{name}_hdr.hdr'
    hdr_file.touch()
    hdr_file.write_text(f"0 @VGMT1\n1 @R\n2 @NId # @NId\n3 @Tinteger # @Tinteger\n4 FEATURE_DATA\n")
    srt_file = srt_dir / f'{name}.srt'
    srt_file.touch()
    srt_file.write_text(f"> @VGMT1\n# @D0\n1 2 3 4 5 6 7 8 9 10")
    with mock.patch('pathlib.Path.exists', return_value=False):
        with mock.patch('pathlib.Path.mkdir') as mock_mkdir:
            with mock.patch('subprocess.run') as mock_run:
                conversion.conversion_sort_gmtp_3d(str(tmp_path), [name], '1', logger_session)
                assert(os.path.exists(srt_dir / f"{name}.gmtsddd"))
                mock_mkdir.assert_called()
                mock_run.assert_called()

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
                with mock.patch('subprocess.run') as mock_run:
                    conversion.conversion_sort_gmtp(str(tmp_path), [name], logger_session)
                    mock_mkdir.assert_called()
                    mock_run.assert_called()

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
    x, y, t = conversion.interpol(col_1, frst, last, df)
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
    x, y, t = conversion.interpol(col_1, frst, last, df)
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
    x, y, t = conversion.interpol(col_1, frst, last, df)
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert isinstance(t, float)

def test_main():
    ap = mock.MagicMock()
    ap.add_argument = mock.MagicMock()
    ap.parse_args = mock.MagicMock(return_value=mock.MagicMock(
        input_directory='input_dir',
        output_directory='output_dir',
        crs='4326',
    ))
    with mock.patch('argparse.ArgumentParser', return_value=ap):
        with mock.patch('aemworkflow.conversion.conversion_zedfix_gmt_to_srt', return_value=['name1', 'name2']) as mock_conversion_zedfix:
            with mock.patch('aemworkflow.conversion.conversion_sort_gmtp_3d') as mock_conversion_sort_gmtp_3d:
                conversion.main()
                mock_conversion_zedfix.assert_called()
                mock_conversion_sort_gmtp_3d.assert_called()
