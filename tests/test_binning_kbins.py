import pytest

from machineLearning import binning_kbins


def test_clean_list_converts_nested_string_values_to_floats():
    assert binning_kbins.cleanList([["72.0"], ["73.5"], ["80"]]) == [72.0, 73.5, 80.0]


def test_get_data_from_file_reads_newline_delimited_values(tmp_path):
    data_file = tmp_path / "temperatures.txt"
    data_file.write_text("72.0\n73.5\n\n74\n", encoding="utf-8")

    assert binning_kbins.getDataFromFile(data_file) == [["72.0"], ["73.5"], ["74"]]


def test_get_data_from_file_returns_empty_list_for_missing_file(tmp_path):
    assert binning_kbins.getDataFromFile(tmp_path / "missing.txt") == []


def test_determine_user_time_returns_zero_when_bins_are_too_small():
    bins = [bin_with_items(1, [7.00, 7.10, 7.20])]

    result = binning_kbins.determineUserTime(
        bins,
        BIN_SIZE_LIMIT=30,
        TIME_STD=0.50,
        USER_SHOWER_PUSH_FORWARD=0.17,
    )

    assert result == 0


def test_determine_user_time_picks_lowest_standard_deviation_bin():
    stable_early = bin_with_items(1, [7.95, 8.00, 8.05] * 10)
    noisy_later = bin_with_items(2, [9.00, 9.45, 9.90] * 10)

    result = binning_kbins.determineUserTime(
        [noisy_later, stable_early],
        BIN_SIZE_LIMIT=30,
        TIME_STD=0.50,
        USER_SHOWER_PUSH_FORWARD=0.17,
    )

    assert result == pytest.approx(7.83)


def test_determine_user_time_returns_zero_when_no_bin_is_stable():
    noisy_bin = bin_with_items(2, [6.00, 8.00, 10.00] * 10)

    result = binning_kbins.determineUserTime(
        [noisy_bin],
        BIN_SIZE_LIMIT=30,
        TIME_STD=0.50,
        USER_SHOWER_PUSH_FORWARD=0.17,
    )

    assert result == 0


def test_get_temp_mode_value_uses_default_temperature_file(monkeypatch, tmp_path):
    temperatures_file = tmp_path / "temperatures.txt"
    temperatures_file.write_text("71\n72\n72\n73\n", encoding="utf-8")
    monkeypatch.setattr(binning_kbins, "TEMPERATURES_FILE", temperatures_file)

    assert binning_kbins.getTempModeValue() == 72.0


def test_get_time_data_bins_groups_each_input_value(tmp_path):
    time_file = tmp_path / "time_data.txt"
    time_file.write_text(
        "\n".join(str(value) for value in [7.9, 8.0, 8.1, 18.0, 18.1, 18.2]) + "\n",
        encoding="utf-8",
    )

    bins = binning_kbins.getTimeDataBins(time_file, number_of_bins=2)

    assert len(bins) == 2
    assert sorted(len(time_bin.binItems) for time_bin in bins) == [3, 3]


def test_bin_data_string_representation_includes_value_and_items():
    time_bin = bin_with_items(3, [7.5])

    assert str(time_bin) == "binValue 3 | binItems: [7.5] \n"
    assert repr(time_bin) == "binValue 3 | binItems: [7.5] \n"


def test_do_binning_print_bins_sorts_bins(monkeypatch, capsys):
    monkeypatch.setattr(
        binning_kbins,
        "getTimeDataBins",
        lambda: [bin_with_items(2, [9.0]), bin_with_items(1, [8.0])],
    )

    bins = binning_kbins.doBinning_printBins()

    assert [time_bin.binValue for time_bin in bins] == [1, 2]
    assert "binValue 1" in capsys.readouterr().out


def test_do_binning_returns_time_and_temperature(monkeypatch, tmp_path):
    temperatures_file = tmp_path / "temperatures.txt"
    temperatures_file.write_text("70\n71\n71\n", encoding="utf-8")
    monkeypatch.setattr(binning_kbins, "TEMPERATURES_FILE", temperatures_file)
    monkeypatch.setattr(
        binning_kbins,
        "getTimeDataBins",
        lambda: [bin_with_items(1, [6.95, 7.00, 7.05] * 10)],
    )

    assert binning_kbins.doBinning() == (pytest.approx(6.83), 71.0)


def bin_with_items(bin_value, items):
    time_bin = binning_kbins.BinData(bin_value)
    time_bin.binItems = items
    return time_bin
