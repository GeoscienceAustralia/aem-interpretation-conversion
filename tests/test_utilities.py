import os
import subprocess
import pytest
import aemworkflow.utilities as utilities
from pathlib import Path
from unittest import mock
from fiona.errors import DriverError

logger_session = mock.MagicMock()


def test_get_ogr_path(monkeypatch):
    monkeypatch.setattr(utilities.os, "name", "nt")
    assert utilities.get_ogr_path() == "ogr2ogr.exe"

    monkeypatch.setattr(utilities.os, "name", "posix")
    assert utilities.get_ogr_path() == "ogr2ogr"


def test_validate_file(tmp_path):
    # valid
    valid = tmp_path / "a.shp"
    valid.write_text("")
    assert utilities.validate_file(valid, logger_session) is True

    # missing shape file
    missing = tmp_path / "missing.shp"
    assert utilities.validate_file(missing, logger_session) is False


def test_validate_shapefile(tmp_path):
    # no shape file
    (tmp_path / "a.txt").write_text("no shapefile")
    assert utilities.validate_shapefile(tmp_path, logger_session) is True

    # valid shape file
    (tmp_path / "a.shp").write_text("")
    (tmp_path / "a.shx").write_text("")
    (tmp_path / "a.dbf").write_text("")
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_fiona_open:
        mock_fiona_open.return_value.__enter__.return_value.__len__.return_value = 1
        assert utilities.validate_shapefile(tmp_path, logger_session) is True

    # empty shape file
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_fiona_open:
        mock_fiona_open.return_value.__enter__.return_value.__len__.return_value = 0
        assert utilities.validate_shapefile(str(tmp_path), logger_session=logger_session) is False

    # driver error
    with mock.patch("aemworkflow.utilities.fiona.open", side_effect=DriverError("driver error")):
        assert utilities.validate_shapefile(str(tmp_path), logger_session=logger_session) is False

    # exception
    with mock.patch("aemworkflow.utilities.fiona.open", side_effect=Exception("exception")):
        assert utilities.validate_shapefile(str(tmp_path), logger_session=logger_session) is False

    # missing .shx
    (tmp_path / "a.shp").write_text("")
    (tmp_path / "a.dbf").write_text("")
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_fiona_open:
        assert utilities.validate_shapefile(tmp_path, logger_session=logger_session) is False

    # missing .dbf
    (tmp_path / "a.shp").write_text("")
    (tmp_path / "a.shx").write_text("")
    with mock.patch("aemworkflow.utilities.fiona.open") as mock_fiona_open:
        assert utilities.validate_shapefile(tmp_path, logger_session=logger_session) is False


def test_run_command(tmp_path):
    dummy_exe = (tmp_path / "ogr2ogr").write_text("")

    in_shp = tmp_path / "in.shp"
    out_shp = tmp_path / "out.shp"
    in_gmt = tmp_path / "in.gmt"
    out_gmt = tmp_path / "out.gmt"

    # invalid type
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

    # exe not found
    logger_session.reset_mock()
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=None):
        with pytest.raises(SystemExit) as e:
            utilities.run_command(["ogr2ogr"], logger_session=logger_session)
        assert e.value.code == 1
        logger_session.error.assert_called()

    # success
    logger_session.reset_mock()
    cmd = [utilities.get_ogr_path(), "-f", "GMT", str(out_gmt), str(in_shp)]
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=str(dummy_exe)):
        with mock.patch("aemworkflow.utilities.os.access", return_value=True):
            with mock.patch("aemworkflow.utilities.subprocess.run") as mock_run:
                utilities.run_command(cmd, logger_session=logger_session)
                assert cmd[0] == str(dummy_exe)
                mock_run.assert_called_once_with(cmd, check=True, shell=False)

    # invalid exe
    logger_session.reset_mock()
    cmd = [utilities.get_ogr_path(), "-f", "ESRI Shapefile", str(out_shp), str(in_gmt)]
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=str(dummy_exe)):
        with mock.patch("aemworkflow.utilities.os.access", return_value=False):
            with pytest.raises(SystemExit):
                utilities.run_command(cmd, logger_session=logger_session)
            logger_session.error.assert_called()

    # invalid chars in cmd
    logger_session.reset_mock()
    cmd = [utilities.get_ogr_path(), "-f", "GMT", "bad;arg", str(in_shp)]
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=str(dummy_exe)):
        with mock.patch("aemworkflow.utilities.os.access", return_value=True):
            with mock.patch("aemworkflow.utilities.subprocess.run") as mock_run:
                with pytest.raises(SystemExit):
                    utilities.run_command(cmd, logger_session=logger_session)
                mock_run.assert_not_called()
                logger_session.error.assert_called()

    #  subprocess fails
    logger_session.reset_mock()
    cmd = [utilities.get_ogr_path(), "-f", "GMT", str(out_gmt), str(in_shp)]
    with mock.patch("aemworkflow.utilities.shutil.which", return_value=str(dummy_exe)):
        with mock.patch("aemworkflow.utilities.os.access", return_value=True):
            with mock.patch("aemworkflow.utilities.subprocess.run", side_effect=subprocess.CalledProcessError(1, cmd),):
                with pytest.raises(SystemExit):
                    utilities.run_command(cmd, logger_session=logger_session)
                logger_session.error.assert_called()


def test_get_make_srt_dir(tmp_path):
    srt_dir = tmp_path / "SORT"

    # creates dir
    with mock.patch("pathlib.Path.exists", return_value=False):
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            utilities.get_make_srt_dir(srt_dir)
            mock_mkdir.assert_called()

    # does not create if exists
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            utilities.get_make_srt_dir(srt_dir)
            mock_mkdir.assert_not_called()

    # os error
    with mock.patch("pathlib.Path.exists", side_effect=OSError("fail")):
        with pytest.raises(SystemExit):
            utilities.get_make_srt_dir(srt_dir)


def test_find_geometry_file(tmp_path):
    prefix = "1"

    # numeric geometry file
    f = tmp_path / f"{prefix}.path.txt"
    f.write_text("100 200 300 400")
    p, base_suffix = utilities.find_geometry_file(tmp_path, prefix, "path", logger_session)
    assert p == f
    assert base_suffix == ""

    # alphanumeric geometry file
    f = tmp_path / f"{prefix}_low.extent.txt"
    f.write_text("100_low 200 300 400")
    p, base_suffix = utilities.find_geometry_file(tmp_path, prefix, "extent", logger_session)
    assert p == f
    assert base_suffix == "_low"

    # no geometry file
    with pytest.raises(FileNotFoundError):
        utilities.find_geometry_file(tmp_path, "missing file", "path", logger_session)
    logger_session.error.assert_called()
