from __future__ import annotations

import gspread as gs
from typing import Optional

from servers.tepcott.tepcott import (
    MY_SHEET_BOTTOM_DIVISION_NAMED_RANGE,
    MY_SHEET_D1_CAR_RANGE_NAMED_RANGE,
    MY_SHEET_D1_PIT_MARSHAL_D1_NAMED_RANGE,
    MY_SHEET_D1_PIT_MARSHAL_D2_NAMED_RANGE,
    MY_SHEET_D1_LAP_COUNT_PIT_WINDOW_NAMED_RANGE,
    MY_SHEET_NAME,
    MY_SHEET_RESERVE_REQUESTS_DISCORD_IDS_NAMED_RANGE,
    MY_SHEET_RESERVE_REQUESTS_DIVISIONS_NAMED_RANGE,
    MY_SHEET_RESERVE_REQUESTS_RESERVES_NAMED_RANGE,
    MY_SHEET_RESERVE_REQUESTS_ROUND_NUMBERS_NAMED_RANGE,
    MY_SHEET_ROUND_NUMBER_NAMED_RANGE,
    MY_SHEET_ROUND_TAB_DIVISION_OFFSET,
    MY_SHEET_STARTING_ORDER_DRIVERS_RANGE_NAMED_RANGE,
    MY_SHEET_STARTING_ORDER_RESERVES_RANGE_NAMED_RANGE,
    MY_SHEET_TRACK_RANGE_NAMED_RANGE,
    RESERVE_NEEDED_STRING,
    ROUND_TAB_PREFIX,
    ROSTER_DIVS_NAMED_RANGE,
    ROSTER_DISCORD_IDS_NAMED_RANGE,
    ROSTER_DRIVERS_NAMED_RANGE,
    ROSTER_QUALIFYING_DIVISIONS_NAMED_RANGE,
    ROSTER_SHEET_NAME,
    ROSTER_STATUS_NAMED_RANGE,
    ROSTER_SOCIAL_CLUB_LINKS_NAMED_RANGE,
    SERVICE_ACCOUNT_KEY,
    SPREADSHEET_KEY,
)


class Spreadsheet:
    def __init__(self) -> None:
        """ """

        self._gs = gs.service_account(filename=SERVICE_ACCOUNT_KEY)
        self._spreadsheet = self._gs.open_by_key(SPREADSHEET_KEY)

        self._roster_column_indexes = [
            ROSTER_DRIVERS_NAMED_RANGE,
            ROSTER_SOCIAL_CLUB_LINKS_NAMED_RANGE,
            ROSTER_DISCORD_IDS_NAMED_RANGE,
            ROSTER_DIVS_NAMED_RANGE,
            ROSTER_QUALIFYING_DIVISIONS_NAMED_RANGE,
            ROSTER_STATUS_NAMED_RANGE,
        ]

        self._starting_order_range_column_indexes = [
            MY_SHEET_ROUND_TAB_DIVISION_OFFSET,
            MY_SHEET_BOTTOM_DIVISION_NAMED_RANGE,
            MY_SHEET_STARTING_ORDER_DRIVERS_RANGE_NAMED_RANGE,
            MY_SHEET_STARTING_ORDER_RESERVES_RANGE_NAMED_RANGE,
        ]

        self._reserve_requests_range_column_indexes = [
            MY_SHEET_RESERVE_REQUESTS_ROUND_NUMBERS_NAMED_RANGE,
            MY_SHEET_RESERVE_REQUESTS_DISCORD_IDS_NAMED_RANGE,
            MY_SHEET_RESERVE_REQUESTS_DIVISIONS_NAMED_RANGE,
            MY_SHEET_RESERVE_REQUESTS_RESERVES_NAMED_RANGE,
        ]

        # these are just the A1:A notiation, not the full range used in requests
        self._d1_car_range: Optional[str] = None
        self._track_range: Optional[str] = None
        self._starting_order_drivers_range: Optional[str] = None
        self._starting_order_reserves_range: Optional[str] = None
        self._round_tab_division_offset: Optional[int] = None
        self._bottom_division_number: Optional[int] = None

        self._round_number: Optional[int] = None

    @property
    def round_number(self) -> int:
        """ """
        if not self._round_number:
            self.set_round_number()

        return self._round_number

    def set_round_number(self) -> None:
        """ """

        value_ranges = self.get_single_column_value_ranges(
            ranges=[MY_SHEET_ROUND_NUMBER_NAMED_RANGE], sheet_name=MY_SHEET_NAME
        )

        self._round_number = int(value_ranges[0][0][0])

    @property
    def bottom_division_number(self) -> int:
        """ """
        if not self._bottom_division_number:
            self.set_bottom_division_number()

        return self._bottom_division_number

    def set_bottom_division_number(self) -> None:
        """ """

        value_ranges = self.get_single_column_value_ranges(
            ranges=[MY_SHEET_BOTTOM_DIVISION_NAMED_RANGE], sheet_name=MY_SHEET_NAME
        )

        self._bottom_division_number = int(value_ranges[0][0][0])

    def add_reserve_request(self, discord_id: int) -> None:
        """ """

        reserve_requests_column_indexes = [
            MY_SHEET_RESERVE_REQUESTS_ROUND_NUMBERS_NAMED_RANGE,
            MY_SHEET_RESERVE_REQUESTS_DISCORD_IDS_NAMED_RANGE,
        ]

        value_ranges = self.get_single_column_value_ranges(
            ranges=reserve_requests_column_indexes, sheet_name=MY_SHEET_NAME
        )

        value_ranges[0].append([self.round_number])
        value_ranges[1].append([str(discord_id)])

        my_sheet = self._spreadsheet.worksheet(f"{MY_SHEET_NAME}")

        round_number_index = reserve_requests_column_indexes.index(
            MY_SHEET_RESERVE_REQUESTS_ROUND_NUMBERS_NAMED_RANGE
        )
        discord_id_index = reserve_requests_column_indexes.index(
            MY_SHEET_RESERVE_REQUESTS_DISCORD_IDS_NAMED_RANGE
        )
        my_sheet.batch_update(
            [
                {
                    "range": reserve_requests_column_indexes[round_number_index],
                    "values": value_ranges[round_number_index],
                },
                {
                    "range": reserve_requests_column_indexes[discord_id_index],
                    "values": value_ranges[discord_id_index],
                },
            ],
            value_input_option="raw",
        )

    def remove_reserve_request(self, discord_id: int) -> None:
        """ """

        reserve_requests_column_indexes = [
            MY_SHEET_RESERVE_REQUESTS_ROUND_NUMBERS_NAMED_RANGE,
            MY_SHEET_RESERVE_REQUESTS_DISCORD_IDS_NAMED_RANGE,
        ]

        value_ranges = self.get_single_column_value_ranges(
            ranges=reserve_requests_column_indexes, sheet_name=MY_SHEET_NAME
        )

        round_number_index = reserve_requests_column_indexes.index(
            MY_SHEET_RESERVE_REQUESTS_ROUND_NUMBERS_NAMED_RANGE
        )
        discord_id_index = reserve_requests_column_indexes.index(
            MY_SHEET_RESERVE_REQUESTS_DISCORD_IDS_NAMED_RANGE
        )

        for i, row in enumerate(value_ranges[discord_id_index]):
            if row[0] == str(discord_id):
                value_ranges[round_number_index].pop(i)
                value_ranges[discord_id_index].pop(i)
                value_ranges[round_number_index].append([""])
                value_ranges[discord_id_index].append([""])
                break

        my_sheet = self._spreadsheet.worksheet(f"{MY_SHEET_NAME}")

        my_sheet.batch_update(
            [
                {
                    "range": reserve_requests_column_indexes[round_number_index],
                    "values": value_ranges[round_number_index],
                },
                {
                    "range": reserve_requests_column_indexes[discord_id_index],
                    "values": value_ranges[discord_id_index],
                },
            ],
            value_input_option="raw",
        )

    def get_reserves_needed(
        self,
        divisions: set[str],
        include_filled_reserves=True,
    ) -> list[SpreadsheetDriver]:
        """returns a list of SpreadsheetDriver objects for the reserves needed for the given divisions"""

        reserve_requests_ranges = self.get_single_column_value_ranges(
            ranges=self._reserve_requests_range_column_indexes,
            sheet_name=MY_SHEET_NAME,
        )

        round_numbers_index = self._reserve_requests_range_column_indexes.index(
            MY_SHEET_RESERVE_REQUESTS_ROUND_NUMBERS_NAMED_RANGE
        )
        divisions_index = self._reserve_requests_range_column_indexes.index(
            MY_SHEET_RESERVE_REQUESTS_DIVISIONS_NAMED_RANGE
        )
        discord_ids_index = self._reserve_requests_range_column_indexes.index(
            MY_SHEET_RESERVE_REQUESTS_DISCORD_IDS_NAMED_RANGE
        )
        reserves_index = self._reserve_requests_range_column_indexes.index(
            MY_SHEET_RESERVE_REQUESTS_RESERVES_NAMED_RANGE
        )

        reserve_requests_round_numbers: list[str] = list(
            map(lambda x: x[0], reserve_requests_ranges[round_numbers_index])
        )
        reserve_requests_divisions: list[str] = list(
            map(lambda x: x[0], reserve_requests_ranges[divisions_index])
        )
        reserve_requests_discord_ids: list[str] = list(
            map(lambda x: x[0], reserve_requests_ranges[discord_ids_index])
        )
        reserve_requests_reserves: list[str] = list(
            map(lambda x: x[0], reserve_requests_ranges[reserves_index])
        )

        drivers_by_social_club_name, drivers_by_discord_id = self.get_roster_drivers()

        reserves_needed: list[SpreadsheetDriver] = []

        for i, round_number in enumerate(reserve_requests_round_numbers):
            if round_number != str(self.round_number):
                continue

            division = reserve_requests_divisions[i]
            if not division.isnumeric():
                continue

            division = int(division)
            if division not in divisions:
                continue

            reserve = reserve_requests_reserves[i]
            driver = drivers_by_discord_id[int(reserve_requests_discord_ids[i])]

            driver_needs_reserve = reserve != ""
            # technically this shouldn't ever be blank, but it's still possible
            if not driver_needs_reserve:
                continue

            driver_has_reserve = (
                driver_needs_reserve and reserve != RESERVE_NEEDED_STRING
            )
            if driver_has_reserve and not include_filled_reserves:
                continue

            if reserve in drivers_by_social_club_name:
                driver.reserve = drivers_by_social_club_name[reserve]
            reserves_needed.append(driver)

        return reserves_needed

    def get_neighboring_division_numbers(self, division_number: int) -> tuple[int]:
        """ """
        if division_number == 1:
            return ((division_number + 1),)

        if division_number == self.bottom_division_number:
            return ((division_number - 1),)

        return (division_number - 1, division_number + 1)

    def get_single_column_value_ranges(
        self,
        ranges: list[str],
        sheet_name: Optional[str] = None,
        sheet: Optional[gs.worksheet.Worksheet] = None,
        value_render_option="FORMATTED_VALUE",
    ) -> list[gs.worksheet.ValueRange]:
        """A sheet or sheet name must be provided"""

        sheet_provided: bool = sheet is not None
        sheet_name_provided: bool = sheet_name is not None

        if not sheet_provided and not sheet_name_provided:
            raise ValueError("Either a sheet or a sheet name must be provided")

        if not sheet_provided:
            spreadsheet: gs.Spreadsheet = self._gs.open_by_key(SPREADSHEET_KEY)
            sheet = spreadsheet.worksheet(sheet_name)

        value_ranges: list[gs.worksheet.ValueRange] = sheet.batch_get(
            ranges, major_dimension="ROWS", value_render_option=value_render_option
        )

        max_row_count: int = max([len(vr) for vr in value_ranges])
        for value_range in value_ranges:
            if value_range == []:
                value_range.append([""])

            for row in value_range:
                if row == []:
                    row.append("")

            while len(value_range) < max_row_count:
                value_range.append([""])

        return value_ranges

    def set_round_tab_ranges(self) -> None:
        """ """

        my_sheet_sheet = self._spreadsheet.worksheet(MY_SHEET_NAME)

        starting_order_ranges_value_ranges = self.get_single_column_value_ranges(
            sheet=my_sheet_sheet, ranges=self._starting_order_range_column_indexes
        )

        self._starting_order_drivers_range: str = starting_order_ranges_value_ranges[
            self._starting_order_range_column_indexes.index(
                MY_SHEET_STARTING_ORDER_DRIVERS_RANGE_NAMED_RANGE
            )
        ][0][0]
        self._starting_order_reserves_range: str = starting_order_ranges_value_ranges[
            self._starting_order_range_column_indexes.index(
                MY_SHEET_STARTING_ORDER_RESERVES_RANGE_NAMED_RANGE
            )
        ][0][0]
        self._round_tab_division_offset: int = int(
            starting_order_ranges_value_ranges[
                self._starting_order_range_column_indexes.index(
                    MY_SHEET_ROUND_TAB_DIVISION_OFFSET
                )
            ][0][0]
        )
        self._bottom_division_number: int = int(
            starting_order_ranges_value_ranges[
                self._starting_order_range_column_indexes.index(
                    MY_SHEET_BOTTOM_DIVISION_NAMED_RANGE
                )
            ][0][0]
        )

    def get_starting_order(self, division_number: int) -> list[SpreadsheetDriver]:
        """ """

        division_starting_order = self.get_starting_orders(
            round_number=self.round_number
        )[division_number]
        return division_starting_order

    def set_reserves(self, drivers: list[SpreadsheetDriver]) -> None:
        """`drivers` is a list of drivers that we are updating the reserves for."""

        round_sheet = self._spreadsheet.worksheet(
            f"{ROUND_TAB_PREFIX}{self.round_number}"
        )

        if (
            self._starting_order_drivers_range is None
            or self._starting_order_reserves_range is None
        ):
            self.set_round_tab_ranges()

        STARTING_ORDER_DRIVERS_RANGE = (
            f"{self._starting_order_drivers_range}{round_sheet.row_count}"
        )
        STARTING_ORDER_RESERVES_RANGE = (
            f"{self._starting_order_reserves_range}{round_sheet.row_count}"
        )

        starting_order_column_indexes = [
            STARTING_ORDER_DRIVERS_RANGE,
            STARTING_ORDER_RESERVES_RANGE,
        ]

        starting_order_value_ranges = self.get_single_column_value_ranges(
            sheet=round_sheet, ranges=starting_order_column_indexes
        )

        driver_column_index = starting_order_column_indexes.index(
            STARTING_ORDER_DRIVERS_RANGE
        )
        reserve_column_index = starting_order_column_indexes.index(
            STARTING_ORDER_RESERVES_RANGE
        )

        for i, driver_value in enumerate(
            starting_order_value_ranges[driver_column_index]
        ):
            for driver in drivers:
                if driver_value[0] != driver.social_club_name:
                    continue
                starting_order_value_ranges[reserve_column_index][i][
                    0
                ] = driver.reserve.social_club_name

        round_sheet.batch_update(
            [
                {
                    "range": starting_order_column_indexes[reserve_column_index],
                    "values": starting_order_value_ranges[reserve_column_index],
                }
            ],
            value_input_option="USER_ENTERED",
        )

    def get_roster_drivers(
        self,
    ) -> tuple[dict[str, SpreadsheetDriver], dict[int, SpreadsheetDriver]]:
        """returns tuple(dict[social_club_name, SpreadsheetDriver], dict[discord_id, SpreadsheetDriver])"""

        roster_value_ranges: list[
            gs.worksheet.ValueRange
        ] = self.get_single_column_value_ranges(
            ranges=self._roster_column_indexes, sheet_name=ROSTER_SHEET_NAME
        )

        roster_drivers: list[str] = list(
            map(
                lambda x: x[0],
                roster_value_ranges[
                    self._roster_column_indexes.index(ROSTER_DRIVERS_NAMED_RANGE)
                ],
            )
        )
        roster_social_club_links: list[str] = list(
            map(
                lambda x: x[0],
                roster_value_ranges[
                    self._roster_column_indexes.index(
                        ROSTER_SOCIAL_CLUB_LINKS_NAMED_RANGE
                    )
                ],
            )
        )
        roster_discord_ids: list[str] = list(
            map(
                lambda x: x[0],
                roster_value_ranges[
                    self._roster_column_indexes.index(ROSTER_DISCORD_IDS_NAMED_RANGE)
                ],
            )
        )
        roster_divs: list[str] = list(
            map(
                lambda x: x[0],
                roster_value_ranges[
                    self._roster_column_indexes.index(ROSTER_DIVS_NAMED_RANGE)
                ],
            )
        )
        roster_quailfying_divs: list[str] = list(
            map(
                lambda x: x[0],
                roster_value_ranges[
                    self._roster_column_indexes.index(
                        ROSTER_QUALIFYING_DIVISIONS_NAMED_RANGE
                    )
                ],
            )
        )
        roster_status: list[str] = list(
            map(
                lambda x: x[0],
                roster_value_ranges[
                    self._roster_column_indexes.index(ROSTER_STATUS_NAMED_RANGE)
                ],
            )
        )

        drivers_by_social_club_name: dict[str, SpreadsheetDriver] = {}
        drivers_by_discord_id: dict[int, SpreadsheetDriver] = {}
        for (
            driver,
            social_club_link,
            discord_id,
            division_number,
            qualifying_division,
            status,
        ) in zip(
            roster_drivers,
            roster_social_club_links,
            roster_discord_ids,
            roster_divs,
            roster_quailfying_divs,
            roster_status,
        ):
            driver = SpreadsheetDriver(
                social_club_name=driver,
                discord_id=int(discord_id),
                division=division_number,
                qualifying_division=qualifying_division,
                status=status,
            )
            drivers_by_social_club_name[driver.social_club_name] = driver
            drivers_by_discord_id[driver.discord_id] = driver

        return drivers_by_social_club_name, drivers_by_discord_id

    def get_starting_orders(self, round_number: int) -> list[list[SpreadsheetDriver]]:
        """returns a list of lists of drivers. every driver has a reserve and
        every reserve is not None, but the name could be blank and discord_id
        could be None."""

        round_sheet = self._spreadsheet.worksheet(f"{ROUND_TAB_PREFIX}{round_number}")

        if (
            self._starting_order_drivers_range is None
            or self._starting_order_reserves_range is None
        ):
            self.set_round_tab_ranges()

        STARTING_ORDER_DRIVERS_RANGE = (
            f"{self._starting_order_drivers_range}{round_sheet.row_count}"
        )
        STARTING_ORDER_RESERVES_RANGE = (
            f"{self._starting_order_reserves_range}{round_sheet.row_count}"
        )

        starting_order_column_indexes = [
            STARTING_ORDER_DRIVERS_RANGE,
            STARTING_ORDER_RESERVES_RANGE,
        ]

        starting_order_value_ranges = self.get_single_column_value_ranges(
            sheet=round_sheet, ranges=starting_order_column_indexes
        )

        starting_order_drivers: list[str] = starting_order_value_ranges[
            starting_order_column_indexes.index(STARTING_ORDER_DRIVERS_RANGE)
        ]
        starting_order_reserves: list[str] = starting_order_value_ranges[
            starting_order_column_indexes.index(STARTING_ORDER_RESERVES_RANGE)
        ]

        drivers_by_social_club_name: dict[str, SpreadsheetDriver]
        drivers_by_social_club_name, _ = self.get_roster_drivers()

        starting_orders: list[list[SpreadsheetDriver]] = [
            [],
        ]
        # [0] intentionally left blank for indexing to match division number

        for i, driver_value in enumerate(starting_order_drivers):
            if driver_value == [""]:
                continue
            driver_value = driver_value[0]

            division_number: int = (i // self._round_tab_division_offset) + 1
            if division_number > self._bottom_division_number:
                break

            driver = drivers_by_social_club_name[driver_value]

            reserve_is_driver = (
                starting_order_reserves[i][0] in drivers_by_social_club_name
            )
            if reserve_is_driver:
                reserve = drivers_by_social_club_name[starting_order_reserves[i][0]]
            else:
                reserve = SpreadsheetDriver(
                    social_club_name=starting_order_reserves[i][0],
                )
            driver.reserve = reserve

            if division_number >= len(starting_orders):
                starting_orders.append([])

            starting_orders[division_number].append(driver)

        return starting_orders

    def get_track(self) -> SpreadsheetTrack:
        track_range = self.get_single_column_value_ranges(
            sheet=self._spreadsheet.worksheet(MY_SHEET_NAME),
            ranges=[MY_SHEET_TRACK_RANGE_NAMED_RANGE],
        )

        round_tab = self._spreadsheet.worksheet(
            f"{ROUND_TAB_PREFIX}{self.round_number}"
        )

        round_track = self.get_single_column_value_ranges(
            sheet=round_tab, ranges=[track_range[0][0][0]]
        )[0][0]

        track = SpreadsheetTrack(name=round_track[0])

        return track

    def get_vehicles(self) -> list[SpreadsheetCar]:

        self.set_round_tab_ranges()

        round_tab = self._spreadsheet.worksheet(
            f"{ROUND_TAB_PREFIX}{self.round_number}"
        )

        d1_car_range = self.get_single_column_value_ranges(
            sheet=self._spreadsheet.worksheet(MY_SHEET_NAME),
            ranges=[MY_SHEET_D1_CAR_RANGE_NAMED_RANGE],
        )

        d1_car_range_row = int(d1_car_range[0][0][0][1:])
        d1_car_range_column = d1_car_range[0][0][0][0]
        # this assumes column is one letter

        car_ranges = []

        for i in range(self._bottom_division_number):
            car_ranges.append(
                f"{d1_car_range_column}{d1_car_range_row + (i * self._round_tab_division_offset)}"
            )

        car_ranges = self.get_single_column_value_ranges(
            sheet=round_tab, ranges=car_ranges
        )

        vehicles: list[SpreadsheetCar] = []
        for car_range in car_ranges:
            for car in car_range:
                vehicles.append(SpreadsheetCar(name=car[0]))

        return vehicles

    def get_pit_marshals(self) -> list[tuple[SpreadsheetDriver]]:
        """ """

        self.set_round_tab_ranges()

        round_tab = self._spreadsheet.worksheet(
            f"{ROUND_TAB_PREFIX}{self.round_number}"
        )

        d1_pit_marshals_range = self.get_single_column_value_ranges(
            sheet=self._spreadsheet.worksheet(MY_SHEET_NAME),
            ranges=[
                MY_SHEET_D1_PIT_MARSHAL_D1_NAMED_RANGE,
                MY_SHEET_D1_PIT_MARSHAL_D2_NAMED_RANGE,
            ],
        )

        d1_pit_marshal_1_range_row = int(d1_pit_marshals_range[0][0][0][1:])
        d1_pit_marshal_1_range_column = d1_pit_marshals_range[0][0][0][0]
        # this assumes column is one letter

        d1_pit_marshal_2_range_row = int(d1_pit_marshals_range[1][0][0][1:])
        d1_pit_marshal_2_range_column = d1_pit_marshals_range[1][0][0][0]
        # this assumes column is one letter

        pit_marshal_1_ranges = []
        pit_marshal_2_ranges = []

        for i in range(self._bottom_division_number):
            pit_marshal_1_ranges.append(
                f"{d1_pit_marshal_1_range_column}{d1_pit_marshal_1_range_row + (i * self._round_tab_division_offset)}"
            )
            pit_marshal_2_ranges.append(
                f"{d1_pit_marshal_2_range_column}{d1_pit_marshal_2_range_row + (i * self._round_tab_division_offset)}"
            )

        pit_marshal_ranges = pit_marshal_1_ranges + pit_marshal_2_ranges
        pit_marshal_ranges = self.get_single_column_value_ranges(
            sheet=round_tab, ranges=pit_marshal_ranges
        )
        pit_marshal_ranges = zip(
            pit_marshal_ranges[: len(pit_marshal_ranges) // 2],
            pit_marshal_ranges[len(pit_marshal_ranges) // 2 :],
        )

        drivers_by_social_club_name, _ = self.get_roster_drivers()

        pit_marshals: list[tuple[SpreadsheetDriver]] = []
        for pit_marshal_range in pit_marshal_ranges:
            div_pit_marshals = ()

            for pit_marshal in pit_marshal_range:
                pit_marshal_name = pit_marshal[0][0]
                pit_marshal_present = pit_marshal_name != ""
                if not pit_marshal_present:
                    continue

                div_pit_marshals += (drivers_by_social_club_name[pit_marshal_name],)

            pit_marshals.append(div_pit_marshals)

        return pit_marshals

    def get_lap_counts_pit_widows(self) -> list[tuple[str, str]]:
        """ """

        self.set_round_tab_ranges()

        round_tab = self._spreadsheet.worksheet(
            f"{ROUND_TAB_PREFIX}{self.round_number}"
        )

        d1_lap_count_pit_window_range = self.get_single_column_value_ranges(
            sheet=self._spreadsheet.worksheet(MY_SHEET_NAME),
            ranges=[MY_SHEET_D1_LAP_COUNT_PIT_WINDOW_NAMED_RANGE],
        )

        d1_lap_count_pit_window_range_row = int(
            d1_lap_count_pit_window_range[0][0][0][1:]
        )
        d1_lap_count_pit_window_range_column = d1_lap_count_pit_window_range[0][0][0][0]

        lap_count_pit_window_ranges = []

        for i in range(self._bottom_division_number):
            lap_count_pit_window_ranges.append(
                f"{d1_lap_count_pit_window_range_column}{d1_lap_count_pit_window_range_row + (i * self._round_tab_division_offset)}"
            )

        lap_count_pit_window_ranges = self.get_single_column_value_ranges(
            sheet=round_tab, ranges=lap_count_pit_window_ranges
        )

        lap_counts_pit_windows: list[tuple[str, str]] = []
        for lap_count_pit_widnow_range in lap_count_pit_window_ranges:
            lap_count: str
            pit_window: str
            lap_count, pit_window = tuple(lap_count_pit_widnow_range[0][0].split("/"))
            lap_counts_pit_windows.append((lap_count.strip(), pit_window.strip()))

        return lap_counts_pit_windows


class SpreadsheetTrack:
    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def social_club_search_link(self) -> str:
        return f"https://socialclub.rockstargames.com/jobs/{self.name.replace(' ', '%20')}?dateRange=any&missiontype=race&platform=pc&sort=likes&title=gtav"

    @property
    def gtalens_search_link(self) -> str:
        return f"https://gtalens.com/?cat=comm&page=1&search={self.name.replace(' ', '%20')}&sort=searchscore&platforms=pc"


class SpreadsheetCar:
    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def gtacars_search_link(self) -> str:
        return f"https://gtacars.net/gta5?q={self.name.replace(' ', '%20')}"


class SpreadsheetDriver:
    def __init__(
        self,
        social_club_name: str,
        discord_id: Optional[int] = None,
        division: str = "N/A",
        qualifying_division: str = "N/A",
        status: str = "Racing",
        reserve: Optional[SpreadsheetDriver] = None,
    ) -> None:
        """ """

        self.social_club_name = social_club_name
        self.discord_id = discord_id
        self.division = division
        self.qualifying_division = qualifying_division
        self.status = status
        self.reserve = reserve

        self.reserve_division: Optional[int] = None

    @property
    def interpreted_division(self) -> int:
        if self.division.isnumeric() and self.qualifying_division.isnumeric():
            return min(int(self.division), int(self.qualifying_division))
        else:
            return int(self.qualifying_division)

    @property
    def social_club_link(self) -> str:
        return f"https://socialclub.rockstargames.com/member/{self.social_club_name}"
