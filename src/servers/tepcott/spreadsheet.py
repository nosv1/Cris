from __future__ import annotations

import gspread as gs
from typing import Optional

from servers.tepcott.tepcott import (
    MY_SHEET_BOTTOM_DIVISION_NAMED_RANGE,
    MY_SHEET_NAME,
    MY_SHEET_ROUND_NUMBER_NAMED_RANGE,
    MY_SHEET_ROUND_TAB_DIVISION_OFFSET,
    MY_SHEET_STARTING_ORDER_DRIVERS_RANGE_NAMED_RANGE,
    MY_SHEET_STARTING_ORDER_RESERVES_RANGE_NAMED_RANGE,
    ROUND_TAB_PREFIX,
    ROSTER_STATUS_NAMED_RANGE,
    ROSTER_DIVS_NAMED_RANGE,
    ROSTER_DISCORD_IDS_NAMED_RANGE,
    ROSTER_SOCIAL_CLUB_LINKS_NAMED_RANGE,
    ROSTER_DRIVERS_NAMED_RANGE,
    ROSTER_SHEET_NAME,
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
            ROSTER_STATUS_NAMED_RANGE,
        ]

        self._starting_order_range_column_indexes = [
            MY_SHEET_ROUND_TAB_DIVISION_OFFSET,
            MY_SHEET_BOTTOM_DIVISION_NAMED_RANGE,
            MY_SHEET_STARTING_ORDER_DRIVERS_RANGE_NAMED_RANGE,
            MY_SHEET_STARTING_ORDER_RESERVES_RANGE_NAMED_RANGE,
        ]

        # these are just the A1:A notiation, not the full range used in requests
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

    def set_reserves(self, round_number: int, drivers: list[SpreadsheetDriver]) -> None:
        """`drivers` is a list of drivers that we are updating the reserves for."""

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
            sheet_name=ROSTER_SHEET_NAME, ranges=self._roster_column_indexes
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
        for (driver, social_club_link, discord_id, division_number, status) in zip(
            roster_drivers,
            roster_social_club_links,
            roster_discord_ids,
            roster_divs,
            roster_status,
        ):
            driver = SpreadsheetDriver(
                social_club_name=driver,
                discord_id=int(discord_id),
                division=division_number,
                status=status,
            )
            drivers_by_social_club_name[driver.social_club_name] = driver
            drivers_by_discord_id[driver.discord_id] = driver

        return drivers_by_social_club_name, drivers_by_discord_id

    def get_starting_orders(self, round_number: int) -> list[list[SpreadsheetDriver]]:
        """ """

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

            if len(starting_order_reserves) > i:
                reserve = SpreadsheetDriver(
                    social_club_name=starting_order_reserves[i][0],
                )
                driver.reserve = reserve

            if division_number >= len(starting_orders):
                starting_orders.append([])

            starting_orders[division_number].append(driver)

        return starting_orders


class SpreadsheetDriver:
    def __init__(
        self,
        social_club_name: str,
        discord_id: Optional[int] = None,
        division: str = "N/A",
        status: str = "Racing",
        reserve: Optional[SpreadsheetDriver] = None,
    ) -> None:
        """ """

        self.social_club_name = social_club_name
        self.discord_id = discord_id
        self.division = division
        self.status = status
        self.reserve = reserve
