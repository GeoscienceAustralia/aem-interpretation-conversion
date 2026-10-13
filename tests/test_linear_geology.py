from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

import aemworkflow.linear_geology as linear_geology


@pytest.fixture
def mock_logger():
    """Return a logger mock accepted by the workflow functions."""
    return MagicMock()


class TestPathToPointGmt:
    def test_writes_gmt_points_from_valid_path_rows(
        self,
        tmp_path,
        mock_logger,
    ):
        path_file = tmp_path / "survey.path.txt"
        output_gmt = tmp_path / "survey.gmt"

        path_file.write_text(
            "100 1 a b c d 149.100 -35.100 extra\n"
            "101 2 a b c d 149.200 -35.200 extra\n",
            encoding="utf-8",
        )

        linear_geology.path_to_point_gmt(
            str(path_file),
            str(output_gmt),
            logger_session=mock_logger,
        )

        assert output_gmt.read_text(encoding="utf-8") == (
            "# @VGMT1.0 @GPOINT\n"
            "# @Je4283\n"
            "# @Nlinenum|flib|date|Survey|Company|Status\n"
            "# @Tinteger|integer|integer|string|string|string\n"
            "# FEATURE_DATA\n"
            ">\n"
            "# @D100|1\n"
            "149.100 -35.100\n"
            ">\n"
            "# @D101|2\n"
            "149.200 -35.200\n"
        )

        mock_logger.info.assert_any_call(
            "Converting path file to GMT: survey.path.txt"
        )
        mock_logger.info.assert_any_call(
            "GMT point file written: survey.gmt"
        )

    def test_skips_rows_with_fewer_than_eight_columns(
        self,
        tmp_path,
        mock_logger,
    ):
        path_file = tmp_path / "survey.path.txt"
        output_gmt = tmp_path / "survey.gmt"

        path_file.write_text(
            "too few columns\n"
            "200 3 a b c d 150.000 -34.000\n",
            encoding="utf-8",
        )

        linear_geology.path_to_point_gmt(
            str(path_file),
            str(output_gmt),
            logger_session=mock_logger,
        )

        contents = output_gmt.read_text(encoding="utf-8")

        assert "too few columns" not in contents
        assert "# @D200|3" in contents
        assert "150.000 -34.000" in contents


class TestPathGmtToShp:
    @patch("aemworkflow.linear_geology.run_command")
    @patch(
        "aemworkflow.linear_geology.get_ogr_path",
        return_value="/usr/bin/ogr2ogr",
    )
    def test_runs_expected_conversion_command(
        self,
        mock_get_ogr_path,
        mock_run_command,
        mock_logger,
    ):
        linear_geology.path_gmt_to_shp(
            "/input/flight.gmt",
            "/output/flight.shp",
            logger_session=mock_logger,
        )

        mock_get_ogr_path.assert_called_once_with()
        mock_run_command.assert_called_once_with(
            [
                "/usr/bin/ogr2ogr",
                "-f",
                "ESRI Shapefile",
                "/output/flight.shp",
                "/input/flight.gmt",
            ]
        )
        mock_logger.info.assert_called_once_with(
            "Point shapefile written: flight.shp"
        )


class TestSpatialJoin:
    @patch("aemworkflow.linear_geology.gpd.sjoin")
    @patch("aemworkflow.linear_geology.gpd.read_file")
    def test_joins_each_point_shapefile_to_polygons(
        self,
        mock_read_file,
        mock_sjoin,
        tmp_path,
        mock_logger,
    ):
        point_dir = tmp_path / "points"
        output_dir = tmp_path / "joined"
        polygon_shp = tmp_path / "map_data" / "geology.shp"

        point_dir.mkdir()
        polygon_shp.parent.mkdir()

        (point_dir / "flight_1.shp").touch()
        (point_dir / "flight_2.shp").touch()
        (point_dir / "ignore.txt").touch()
        polygon_shp.touch()

        polygons = MagicMock()
        polygons.crs = "EPSG:4283"
        polygons.__len__.return_value = 3

        points_1 = MagicMock()
        points_2 = MagicMock()
        projected_points_1 = MagicMock()
        projected_points_2 = MagicMock()
        joined_1 = MagicMock()
        joined_2 = MagicMock()

        points_1.to_crs.return_value = projected_points_1
        points_2.to_crs.return_value = projected_points_2

        mock_read_file.side_effect = [
            polygons,
            points_1,
            points_2,
        ]
        mock_sjoin.side_effect = [
            joined_1,
            joined_2,
        ]

        linear_geology.spatial_join(
            str(point_dir),
            str(polygon_shp),
            str(output_dir),
            logger_session=mock_logger,
        )

        assert output_dir.is_dir()

        assert mock_read_file.call_args_list == [
            call(str(polygon_shp)),
            call(str(point_dir / "flight_1.shp")),
            call(str(point_dir / "flight_2.shp")),
        ]

        points_1.to_crs.assert_called_once_with("EPSG:4283")
        points_2.to_crs.assert_called_once_with("EPSG:4283")

        assert mock_sjoin.call_args_list == [
            call(
                projected_points_1,
                polygons,
                how="left",
                predicate="within",
            ),
            call(
                projected_points_2,
                polygons,
                how="left",
                predicate="within",
            ),
        ]

        joined_1.to_file.assert_called_once_with(
            str(output_dir / "flight_1_new.shp")
        )
        joined_2.to_file.assert_called_once_with(
            str(output_dir / "flight_2_new.shp")
        )

    @patch("aemworkflow.linear_geology.gpd.sjoin")
    @patch("aemworkflow.linear_geology.gpd.read_file")
    def test_ignores_non_shapefile_point_files(
        self,
        mock_read_file,
        mock_sjoin,
        tmp_path,
        mock_logger,
    ):
        point_dir = tmp_path / "points"
        output_dir = tmp_path / "joined"
        polygon_shp = tmp_path / "geology.shp"

        point_dir.mkdir()
        (point_dir / "notes.txt").touch()
        polygon_shp.touch()

        polygons = MagicMock()
        polygons.crs = "EPSG:4283"
        polygons.__len__.return_value = 1
        mock_read_file.return_value = polygons

        linear_geology.spatial_join(
            str(point_dir),
            str(polygon_shp),
            str(output_dir),
            logger_session=mock_logger,
        )

        mock_read_file.assert_called_once_with(str(polygon_shp))
        mock_sjoin.assert_not_called()


class TestBuildPolygonGmt:
    @patch(
        "aemworkflow.linear_geology.get_ogr_path",
        return_value="/usr/bin/ogr2ogr",
    )
    @patch("aemworkflow.linear_geology.run_command")
    def test_groups_consecutive_points_by_selected_column(
        self,
        mock_run_command,
        mock_get_ogr_path,
        tmp_path,
        mock_logger,
    ):
        joined_shp = tmp_path / "flight_new.shp"
        output_gmt = tmp_path / "flight_polygon.gmt"
        intermediate_gmt = tmp_path / "flight_new_path_SurfGeo.gmt"

        joined_shp.touch()

        intermediate_gmt.write_text(
            "# @VGMT1.0 @GPOINT\n"
            "# @Nlinenum|flib|unit\n"
            "# @Tinteger|integer|string\n"
            "# FEATURE_DATA\n"
            ">\n"
            "# @D100|1|A\n"
            "149.0 -35.0\n"
            ">\n"
            "# @D100|2|A\n"
            "149.1 -35.1\n"
            ">\n"
            "# @D100|3|B\n"
            "149.2 -35.2\n",
            encoding="utf-8",
        )

        linear_geology.build_polygon_gmt(
            str(joined_shp),
            str(output_gmt),
            column_index=3,
            logger_session=mock_logger,
        )

        mock_run_command.assert_called_once_with(
            [
                "/usr/bin/ogr2ogr",
                "-f",
                "GMT",
                str(intermediate_gmt),
                str(joined_shp),
            ]
        )

        assert output_gmt.read_text(encoding="utf-8") == (
            "# @VGMT1.0 @GPOLYGON\n"
            "# @NId\n"
            "# @Nlinenum|flib|unit\n"
            "# @Tinteger|integer|string\n"
            "# FEATURE_DATA\n"
            ">\n"
            "# @D100|1|A\n"
            "# @P\n"
            "2 0\n"
            "2 20\n"
            "1 20\n"
            "1 0\n"
            ">\n"
            "# @D100|3|B\n"
            "# @P\n"
            "3 0\n"
            "3 20\n"
            "3 20\n"
            "3 0\n"
        )

    @patch(
        "aemworkflow.linear_geology.get_ogr_path",
        return_value="/usr/bin/ogr2ogr",
    )
    @patch("aemworkflow.linear_geology.run_command")
    def test_produces_empty_output_when_intermediate_has_no_features(
        self,
        mock_run_command,
        mock_get_ogr_path,
        tmp_path,
        mock_logger,
    ):
        joined_shp = tmp_path / "empty_new.shp"
        output_gmt = tmp_path / "empty_polygon.gmt"
        intermediate_gmt = tmp_path / "empty_new_path_SurfGeo.gmt"

        joined_shp.touch()
        intermediate_gmt.write_text(
            "# @VGMT1.0 @GPOINT\n"
            "# @Nlinenum|flib|unit\n"
            "# @Tinteger|integer|string\n"
            "# FEATURE_DATA\n",
            encoding="utf-8",
        )

        linear_geology.build_polygon_gmt(
            str(joined_shp),
            str(output_gmt),
            column_index=3,
            logger_session=mock_logger,
        )

        assert output_gmt.read_text(encoding="utf-8") == ""


class TestFindMapDataDir:
    def test_finds_lowercase_map_data_directory(self, tmp_path):
        map_data = tmp_path / "map_data"
        map_data.mkdir()

        result = linear_geology.find_map_data_dir(str(tmp_path))

        assert result == str(map_data)

    def test_finds_map_data_directory_case_insensitively(self, tmp_path):
        map_data = tmp_path / "Map_Data"
        map_data.mkdir()

        result = linear_geology.find_map_data_dir(str(tmp_path))

        assert result == str(map_data)

    def test_ignores_file_named_map_data(self, tmp_path):
        (tmp_path / "map_data").touch()

        result = linear_geology.find_map_data_dir(str(tmp_path))

        assert result == ""

    def test_returns_empty_string_when_directory_is_missing(self, tmp_path):
        result = linear_geology.find_map_data_dir(str(tmp_path))

        assert result == ""


class TestRunLinearGeology:
    def test_returns_false_when_map_data_directory_is_missing(
        self,
        tmp_path,
        mock_logger,
    ):
        result = linear_geology.run_linear_geology(
            str(tmp_path),
            str(tmp_path / "output"),
            entries=[("geology", 3)],
            logger_session=mock_logger,
        )

        assert result is False
        mock_logger.error.assert_called_once_with(
            "No map_data folder found in input directory."
        )

    def test_returns_false_when_no_path_files_exist(
        self,
        tmp_path,
        mock_logger,
    ):
        (tmp_path / "map_data").mkdir()

        result = linear_geology.run_linear_geology(
            str(tmp_path),
            str(tmp_path / "output"),
            entries=[("geology", 3)],
            logger_session=mock_logger,
        )

        assert result is False
        mock_logger.error.assert_called_once_with(
            "No .path.txt files found in input directory."
        )

    @patch("aemworkflow.linear_geology.run_command")
    @patch("aemworkflow.linear_geology.build_polygon_gmt")
    @patch("aemworkflow.linear_geology.spatial_join")
    @patch("aemworkflow.linear_geology.path_gmt_to_shp")
    @patch("aemworkflow.linear_geology.path_to_point_gmt")
    @patch(
        "aemworkflow.linear_geology.get_ogr_path",
        return_value="/usr/bin/ogr2ogr",
    )
    def test_runs_complete_pipeline_for_selected_dataset(
        self,
        mock_get_ogr_path,
        mock_path_to_point_gmt,
        mock_path_gmt_to_shp,
        mock_spatial_join,
        mock_build_polygon_gmt,
        mock_run_command,
        tmp_path,
        mock_logger,
    ):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        map_data_dir = input_dir / "map_data"

        input_dir.mkdir()
        map_data_dir.mkdir()
        output_dir.mkdir()

        path_file = input_dir / "flight_101.path.txt"
        polygon_shp = map_data_dir / "geology.shp"

        path_file.write_text("path data", encoding="utf-8")
        polygon_shp.touch()

        def create_joined_output(
            point_shp_dir,
            polygon_shp_path,
            joined_dir,
            logger_session,
        ):
            Path(joined_dir).mkdir(parents=True, exist_ok=True)
            (Path(joined_dir) / "flight_101_new.shp").touch()

        mock_spatial_join.side_effect = create_joined_output

        result = linear_geology.run_linear_geology(
            str(input_dir),
            str(output_dir),
            entries=[("geology", 3)],
            logger_session=mock_logger,
        )

        assert result is True

        point_dir = output_dir / "lin_geo" / "_point_shp"
        joined_dir = output_dir / "lin_geo" / "geology" / "joined"
        polygon_dir = output_dir / "lin_geo" / "geology" / "polygons"

        mock_path_to_point_gmt.assert_called_once_with(
            str(path_file),
            str(point_dir / "flight_101.gmt"),
            logger_session=mock_logger,
        )

        mock_path_gmt_to_shp.assert_called_once_with(
            str(point_dir / "flight_101.gmt"),
            str(point_dir / "flight_101.shp"),
            logger_session=mock_logger,
        )

        mock_spatial_join.assert_called_once_with(
            str(point_dir),
            str(polygon_shp),
            str(joined_dir),
            logger_session=mock_logger,
        )

        mock_build_polygon_gmt.assert_called_once_with(
            str(joined_dir / "flight_101_new.shp"),
            str(polygon_dir / "flight_101_geology_pl.gmt"),
            3,
            logger_session=mock_logger,
        )

        mock_run_command.assert_called_once_with(
            [
                "/usr/bin/ogr2ogr",
                "-f",
                "ESRI Shapefile",
                str(polygon_dir / "flight_101_geology.shp"),
                str(polygon_dir / "flight_101_geology_pl.gmt"),
            ]
        )

        mock_logger.info.assert_any_call(
            "Linear geology pipeline completed."
        )

    @patch("aemworkflow.linear_geology.spatial_join")
    @patch("aemworkflow.linear_geology.path_gmt_to_shp")
    @patch("aemworkflow.linear_geology.path_to_point_gmt")
    def test_skips_missing_map_shapefile(
        self,
        mock_path_to_point_gmt,
        mock_path_gmt_to_shp,
        mock_spatial_join,
        tmp_path,
        mock_logger,
    ):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"

        input_dir.mkdir()
        (input_dir / "map_data").mkdir()
        (input_dir / "flight.path.txt").touch()

        result = linear_geology.run_linear_geology(
            str(input_dir),
            str(output_dir),
            entries=[("missing_geology", 4)],
            logger_session=mock_logger,
        )

        assert result is True
        mock_spatial_join.assert_not_called()
        mock_logger.warning.assert_called_once_with(
            "Map shapefile not found, skipping: missing_geology.shp"
        )

    @patch(
        "aemworkflow.linear_geology.path_to_point_gmt",
        side_effect=RuntimeError("test conversion failure"),
    )
    def test_returns_false_when_pipeline_raises_exception(
        self,
        mock_path_to_point_gmt,
        tmp_path,
        mock_logger,
    ):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"

        input_dir.mkdir()
        (input_dir / "map_data").mkdir()
        (input_dir / "flight.path.txt").touch()

        result = linear_geology.run_linear_geology(
            str(input_dir),
            str(output_dir),
            entries=[],
            logger_session=mock_logger,
        )

        assert result is False
        mock_logger.error.assert_called_once_with(
            "Linear geology pipeline failed: test conversion failure"
        )

    @patch("aemworkflow.linear_geology.spatial_join")
    @patch("aemworkflow.linear_geology.path_gmt_to_shp")
    @patch("aemworkflow.linear_geology.path_to_point_gmt")
    def test_supports_no_selected_map_datasets(
        self,
        mock_path_to_point_gmt,
        mock_path_gmt_to_shp,
        mock_spatial_join,
        tmp_path,
        mock_logger,
    ):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"

        input_dir.mkdir()
        (input_dir / "map_data").mkdir()
        (input_dir / "flight.path.txt").touch()

        result = linear_geology.run_linear_geology(
            str(input_dir),
            str(output_dir),
            entries=[],
            logger_session=mock_logger,
        )

        assert result is True
        mock_path_to_point_gmt.assert_called_once()
        mock_path_gmt_to_shp.assert_called_once()
        mock_spatial_join.assert_not_called()