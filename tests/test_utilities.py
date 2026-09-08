import subprocess
from unittest import mock

import pytest
from fiona.errors import DriverError

import aemworkflow.utilities as utilities

logger_session = mock.MagicMock()


def test_get_ogr_path_windows(monkeypatch):
    monkeypatch.setattr(utilities.os, "name", "nt")
    assert utilities.get_ogr_path() == "ogr2ogr.exe"


def test_get_ogr_path_posix(monkeypatch):
    monkeypatch.setattr(utilities.os, "name", "posix")
    assert utilities.get_ogr_path() == "ogr2ogr"


def test_validate_file_valid(tmp_path):
    valid = tmp_path / "a.shp"
    valid.write_text("")
    assert utilities.validate_file(valid, logger_session) is True


def test_validate_file_missing(tmp_path):
    (tmp_path / "missing.shp")
    assert utilities.validate_file(tmp_path, logger_session) is False


def test_validate_shapefile_no_shape_file(tmp_path):
    (tmp_path / "a.txt").write_text("no shapefile")
    assert utilities.validate_shapefile(tmp_path, logger_session) is True


def test_validate_shapefile_valid_shape_file(tmp_path):
    (tmp_path / "a.shp").write_text("valid")
    (tmp_path / "a.shx").write_text("valid")
    (tmp_path / "a.dbf").write_text("valid")
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_fiona_open:
        mock_fiona_open.return_value.__enter__.return_value.__len__.return_value = 1
        assert utilities.validate_shapefile(tmp_path, logger_session) is True


def test_validate_shapefile_driver_error(tmp_path):
    (tmp_path / "a.shp").write_text("invalid")
    (tmp_path / "a.shx").write_text("invalid")
    (tmp_path / "a.dbf").write_text("invalid")
    with mock.patch("aemworkflow.utilities.fiona.open", side_effect=DriverError("driver error")):
        assert utilities.validate_shapefile(str(tmp_path), logger_session=logger_session) is False


def test_validate_shapefile_exception(tmp_path):
    (tmp_path / "a.shp").write_text("invalid")
    (tmp_path / "a.shx").write_text("invalid")
    (tmp_path / "a.dbf").write_text("invalid")
    with mock.patch("aemworkflow.utilities.fiona.open", side_effect=Exception("exception")):
        assert utilities.validate_shapefile(str(tmp_path), logger_session=logger_session) is False


def test_validate_shapefile_missing_shx(tmp_path):
    (tmp_path / "a.shp").write_text("")
    (tmp_path / "a.dbf").write_text("")
    with mock.patch("aemworkflow.utilities.fiona.open"):
        assert utilities.validate_shapefile(tmp_path, logger_session=logger_session) is False


def test_validate_shapefile_missing_dbf(tmp_path):
    (tmp_path / "a.shp").write_text("")
    (tmp_path / "a.shx").write_text("")
    with mock.patch("aemworkflow.utilities.fiona.open"):
        assert utilities.validate_shapefile(tmp_path, logger_session=logger_session) is False


def test_run_command_invalid_type():
    with mock.patch("aemworkflow.utilities.logger.error") as mock_err:
        with pytest.raises(SystemExit) as e:
            utilities.run_command(None)
        assert e.value.code == 1
        mock_err.assert_called()

    with mock.patch("aemworkflow.utilities.logger.error") as mock_err:
        with pytest.raises(SystemExit) as e:
            utilities.run_command(["", 123])
        assert e.value.code == 1
        mock_err.assert_called()


def test_run_command_exe_not_found():
    logger_session.reset_mock()
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=None):
        with pytest.raises(SystemExit) as e:
            utilities.run_command(["ogr2ogr"], logger_session=logger_session)
        assert e.value.code == 1
        logger_session.error.assert_called()


def test_run_command_success(tmp_path):
    dummy_exe = (tmp_path / "ogr2ogr").write_text("")
    in_shp = tmp_path / "in.shp"
    out_gmt = tmp_path / "out.gmt"
    logger_session.reset_mock()
    cmd = [utilities.get_ogr_path(), "-f", "GMT", str(out_gmt), str(in_shp)]
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=str(dummy_exe)):
        with mock.patch("aemworkflow.utilities.os.access", return_value=True):
            with mock.patch("aemworkflow.utilities.subprocess.run") as mock_run:
                utilities.run_command(cmd, logger_session=logger_session)
                assert cmd[0] == str(dummy_exe)
                mock_run.assert_called_once_with(cmd, check=True, shell=False)


def test_run_command_invalid_exe(tmp_path):
    dummy_exe = (tmp_path / "ogr2ogr").write_text("")
    out_shp = tmp_path / "out.shp"
    in_gmt = tmp_path / "in.gmt"
    logger_session.reset_mock()
    cmd = [utilities.get_ogr_path(), "-f", "ESRI Shapefile", str(out_shp), str(in_gmt)]
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=str(dummy_exe)):
        with mock.patch("aemworkflow.utilities.os.access", return_value=False):
            with pytest.raises(SystemExit):
                utilities.run_command(cmd, logger_session=logger_session)
            logger_session.error.assert_called()


def test_run_command_invalid_chars(tmp_path):
    dummy_exe = (tmp_path / "ogr2ogr").write_text("")
    in_shp = tmp_path / "in.shp"
    logger_session.reset_mock()
    cmd = [utilities.get_ogr_path(), "-f", "GMT", "bad;arg", str(in_shp)]
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=str(dummy_exe)):
        with mock.patch("aemworkflow.utilities.os.access", return_value=True):
            with mock.patch("aemworkflow.utilities.subprocess.run") as mock_run:
                with pytest.raises(SystemExit):
                    utilities.run_command(cmd, logger_session=logger_session)
                mock_run.assert_not_called()
                logger_session.error.assert_called()


def test_run_command_subprocess_fails(tmp_path):
    dummy_exe = (tmp_path / "ogr2ogr").write_text("")
    in_shp = tmp_path / "in.shp"
    out_gmt = tmp_path / "out.gmt"
    logger_session.reset_mock()
    cmd = [utilities.get_ogr_path(), "-f", "GMT", str(out_gmt), str(in_shp)]
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=str(dummy_exe)):
        with mock.patch("aemworkflow.utilities.os.access", return_value=True):
            with mock.patch(
                "aemworkflow.utilities.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, cmd),
            ):
                with pytest.raises(SystemExit):
                    utilities.run_command(cmd, logger_session=logger_session)
                logger_session.error.assert_called()


def test_get_make_srt_dir_creates_dir(tmp_path):
    srt_dir = tmp_path / "SORT"
    with mock.patch("pathlib.Path.exists", return_value=False):
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            utilities.get_make_srt_dir(srt_dir)
            mock_mkdir.assert_called()


def test_get_make_srt_dir_does_not_creates_dir(tmp_path):
    srt_dir = tmp_path / "SORT"
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            utilities.get_make_srt_dir(srt_dir)
            mock_mkdir.assert_not_called()


def test_get_make_srt_dir_os_error(tmp_path):
    srt_dir = tmp_path / "SORT"
    with mock.patch("pathlib.Path.exists", side_effect=OSError("fail")):
        with pytest.raises(SystemExit):
            utilities.get_make_srt_dir(srt_dir)


def test_get_make_export_dir_creates_dir(tmp_path):
    export_dir = tmp_path / "export"
    with mock.patch("pathlib.Path.exists", return_value=False):
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            utilities.get_make_export_dir(export_dir)
            mock_mkdir.assert_called()


def test_get_make_export_dir_does_not_creates_dir(tmp_path):
    export_dir = tmp_path / "export"
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            utilities.get_make_export_dir(export_dir)
            mock_mkdir.assert_not_called()


def test_get_make_export_dir_os_error(tmp_path):
    export_dir = tmp_path / "export"
    with mock.patch("pathlib.Path.exists", side_effect=OSError("fail")):
        with pytest.raises(SystemExit):
            utilities.get_make_export_dir(export_dir)


def test_find_geometry_file_numeric(tmp_path):
    prefix = "1"
    f = tmp_path / f"{prefix}.path.txt"
    f.write_text("100 200 300 400")
    p, base_suffix = utilities.find_geometry_file(tmp_path, prefix, "path", logger_session)
    assert p == f
    assert base_suffix == ""


def test_find_geometry_file_alphanumeric(tmp_path):
    prefix = "1"
    f = tmp_path / f"{prefix}_low.extent.txt"
    f.write_text("100_low 200 300 400")
    p, base_suffix = utilities.find_geometry_file(tmp_path, prefix, "extent", logger_session)
    assert p == f
    assert base_suffix == "_low"


def test_find_geometry_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        utilities.find_geometry_file(tmp_path, "missing file", "path", logger_session)
    logger_session.error.assert_called()


def _make_fiona_feature(fid, geometry, properties):
    return {'id': str(fid), 'geometry': geometry, 'properties': properties}


def test_check_shapefile_blank_rows_no_blank_rows(tmp_path):
    shp_path = tmp_path / "LN1_interp_001.shp"
    shp_path.write_text("")
    features = [
        _make_fiona_feature(0, {'type': 'LineString', 'coordinates': [(0, 0), (1, 1)]},
                            {'FID': 0, 'Type': 'BASE', 'BoundConf': 'H'}),
        _make_fiona_feature(1, {'type': 'LineString', 'coordinates': [(2, 2), (3, 3)]},
                            {'FID': 1, 'Type': 'WITHIN', 'BoundConf': 'M'}),
    ]
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_open:
        mock_open.return_value.__enter__.return_value = iter(features)
        result = utilities.check_shapefile_blank_rows(str(shp_path), logger_session)
    assert result == []
    logger_session.warning.assert_not_called()


def test_check_shapefile_blank_rows_blank_attributes(tmp_path):
    shp_path = tmp_path / "LN1_interp_001.shp"
    shp_path.write_text("")
    features = [
        _make_fiona_feature(0, {'type': 'LineString', 'coordinates': [(0, 0), (1, 1)]},
                            {'FID': 0, 'Type': None, 'BoundConf': ''}),
    ]
    logger_session.reset_mock()
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_open:
        mock_open.return_value.__enter__.return_value = iter(features)
        result = utilities.check_shapefile_blank_rows(str(shp_path), logger_session)
    assert result == [0]
    logger_session.warning.assert_called_once()
    assert 'Blank row detected' in logger_session.warning.call_args[0][0]
    assert 'LN1' in logger_session.warning.call_args[0][0]


def test_check_shapefile_blank_rows_missing_geometry(tmp_path):
    shp_path = tmp_path / "LN1_interp_001.shp"
    shp_path.write_text("")
    features = [
        _make_fiona_feature(2, None, {'FID': 2, 'Type': 'BASE', 'BoundConf': 'H'}),
    ]
    logger_session.reset_mock()
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_open:
        mock_open.return_value.__enter__.return_value = iter(features)
        result = utilities.check_shapefile_blank_rows(str(shp_path), logger_session)
    assert result == [2]
    logger_session.warning.assert_called_once()
    assert 'Missing geometry' in logger_session.warning.call_args[0][0]


def test_check_shapefile_blank_rows_mixed(tmp_path):
    shp_path = tmp_path / "LN2_interp_001.shp"
    shp_path.write_text("")
    features = [
        _make_fiona_feature(0, {'type': 'LineString', 'coordinates': [(0, 0)]},
                            {'FID': 0, 'Type': 'BASE', 'BoundConf': 'H'}),
        _make_fiona_feature(1, None, {'FID': 1, 'Type': 'BASE', 'BoundConf': 'H'}),
        _make_fiona_feature(2, {'type': 'LineString', 'coordinates': [(1, 1)]},
                            {'FID': 2, 'Type': None, 'BoundConf': ''}),
    ]
    logger_session.reset_mock()
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_open:
        mock_open.return_value.__enter__.return_value = iter(features)
        result = utilities.check_shapefile_blank_rows(str(shp_path), logger_session)
    assert result == [1, 2]
    assert logger_session.warning.call_count == 2


def test_check_shapefile_blank_rows_uses_stem_prefix_for_line_name(tmp_path):
    shp_path = tmp_path / "LN5_interp_001.shp"
    shp_path.write_text("")
    features = [
        _make_fiona_feature(0, None, {'FID': 0, 'Type': 'BASE', 'BoundConf': 'H'}),
    ]
    logger_session.reset_mock()
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_open:
        mock_open.return_value.__enter__.return_value = iter(features)
        utilities.check_shapefile_blank_rows(str(shp_path), logger_session)
    assert 'LN5' in logger_session.warning.call_args[0][0]


def test_active_shp_to_gmt_skips_blank_fids(monkeypatch):
    from aemworkflow import interpretation
    commands = []

    monkeypatch.setattr(interpretation, "validate_file", lambda x: True)
    monkeypatch.setattr(interpretation, "check_shapefile_blank_rows", lambda *a, **k: [3, 7])
    monkeypatch.setattr(interpretation, "run_command", lambda cmd: commands.append(cmd))
    monkeypatch.setattr(interpretation, "get_ogr_path", lambda: "ogr2ogr")

    interpretation.active_shp_to_gmt("input.shp", "output.gmt")
    assert "-where" in commands[0]
    assert "FID NOT IN (3,7)" in commands[0]
