import copy
from Database import Database
from datetime import datetime

from servers.tepcott.spreadsheet import SpreadsheetDriver
from servers.tepcott.tepcott import (
    RESERVE_REQUESTS_TABLE_NAME,
    RESERVE_REQUESTS_REQUEST_IDS_COLUMN,
    RESERVE_REQUESTS_DISCORD_IDS_COLUMN,
    RESERVE_REQUESTS_DIVISIONS_COLUMN,
    RESERVES_AVAILABLE_TABLE_NAME,
    RESERVES_AVAILABLE_AVAILABLE_IDS_COLUMN,
    RESERVES_AVAILABLE_DISCORD_IDS_COLUMN,
    RESERVES_AVAILABLE_RESERVE_DIVISIONS_COLUMN,
    RESERVES_AVAILABLE_DIVISIONS_COLUMN,
)


def add_reserve_available(database: Database, reserve: SpreadsheetDriver):
    """ """

    database.connect()
    sql = (
        f"INSERT INTO {RESERVES_AVAILABLE_TABLE_NAME} "
        f"({RESERVES_AVAILABLE_AVAILABLE_IDS_COLUMN}, {RESERVES_AVAILABLE_DISCORD_IDS_COLUMN}, {RESERVES_AVAILABLE_DIVISIONS_COLUMN}, {RESERVES_AVAILABLE_RESERVE_DIVISIONS_COLUMN}) "
        f"VALUES ('{int(datetime.utcnow().timestamp())}', '{reserve.discord_id}', '{reserve.division}', '{reserve.reserve_division}') "
        f"ON DUPLICATE KEY UPDATE "
        f"{RESERVES_AVAILABLE_DISCORD_IDS_COLUMN} = '{reserve.discord_id}', "
        f"{RESERVES_AVAILABLE_DIVISIONS_COLUMN} = '{reserve.division}', "
        f"{RESERVES_AVAILABLE_RESERVE_DIVISIONS_COLUMN} = '{reserve.reserve_division}'"
    )

    database.cursor.execute(sql)
    database.commit()
    database.close()


def add_reserve_request(database: Database, driver: SpreadsheetDriver):
    """ """

    database.connect()
    sql = (
        f"INSERT INTO {RESERVE_REQUESTS_TABLE_NAME} "
        f"({RESERVE_REQUESTS_REQUEST_IDS_COLUMN}, {RESERVE_REQUESTS_DISCORD_IDS_COLUMN}, {RESERVE_REQUESTS_DIVISIONS_COLUMN}) "
        f"VALUES ('{int(datetime.utcnow().timestamp())}', '{driver.discord_id}', '{driver.division}') "
        f"ON DUPLICATE KEY UPDATE {RESERVE_REQUESTS_DIVISIONS_COLUMN} = '{driver.division}'"
    )
    database.cursor.execute(sql)
    database.commit()
    database.close()


def remove_reserve_available(database: Database, reserve: SpreadsheetDriver):
    """ """

    database.connect()
    sql = (
        f"DELETE FROM {RESERVES_AVAILABLE_TABLE_NAME} "
        f"WHERE "
        f"  {RESERVES_AVAILABLE_DISCORD_IDS_COLUMN} = '{reserve.discord_id}' "
        f"  AND {RESERVES_AVAILABLE_RESERVE_DIVISIONS_COLUMN} = '{reserve.reserve_division}'"
    )
    database.cursor.execute(sql)
    database.commit()
    database.close()


def remove_reserve_request(database: Database, driver: SpreadsheetDriver):
    """ """

    database.connect()
    sql = (
        f"DELETE FROM {RESERVE_REQUESTS_TABLE_NAME} "
        f"WHERE {RESERVE_REQUESTS_DISCORD_IDS_COLUMN} = '{driver.discord_id}' "
    )
    database.cursor.execute(sql)
    database.commit()
    database.close()


def get_reserve_requests(
    database: Database, drivers_by_discord_id: dict[int, SpreadsheetDriver]
) -> list[SpreadsheetDriver]:
    """ """

    reserve_requests_column_indexes = [
        RESERVE_REQUESTS_DISCORD_IDS_COLUMN,
        RESERVE_REQUESTS_DIVISIONS_COLUMN,
    ]

    database.connect()
    sql = (
        f"SELECT {', '.join(reserve_requests_column_indexes)} "
        f"FROM {RESERVE_REQUESTS_TABLE_NAME} "
        f"ORDER BY {RESERVE_REQUESTS_REQUEST_IDS_COLUMN} ASC "
    )
    database.cursor.execute(sql)
    database.close()

    rows = database.cursor.fetchall()

    if not rows:
        return []

    discord_id_column_index = reserve_requests_column_indexes.index(
        RESERVE_REQUESTS_DISCORD_IDS_COLUMN
    )
    reserve_requests = [
        copy.deepcopy(drivers_by_discord_id[int(r[discord_id_column_index])])
        for r in rows
    ]

    return reserve_requests


def get_reserves_available(
    database: Database, drivers_by_discord_id: dict[int, SpreadsheetDriver]
) -> list[SpreadsheetDriver]:
    """ """

    reserves_available_column_indexes = [
        RESERVES_AVAILABLE_DISCORD_IDS_COLUMN,
        RESERVES_AVAILABLE_DIVISIONS_COLUMN,
        RESERVES_AVAILABLE_RESERVE_DIVISIONS_COLUMN,
    ]

    database.connect()
    sql = (
        f"SELECT {', '.join(reserves_available_column_indexes)} "
        f"FROM {RESERVES_AVAILABLE_TABLE_NAME} "
        f"ORDER BY {RESERVES_AVAILABLE_AVAILABLE_IDS_COLUMN} ASC "
    )
    database.cursor.execute(sql)
    database.close()

    rows = database.cursor.fetchall()

    if not rows:
        return []

    discord_id_column_index = reserves_available_column_indexes.index(
        RESERVES_AVAILABLE_DISCORD_IDS_COLUMN
    )
    reserve_division_column_index = reserves_available_column_indexes.index(
        RESERVES_AVAILABLE_RESERVE_DIVISIONS_COLUMN
    )
    reserves_available: list[SpreadsheetDriver] = []
    for row in rows:
        discord_id = int(row[discord_id_column_index])
        reserve_division = int(row[reserve_division_column_index])

        reserve = copy.deepcopy(drivers_by_discord_id[discord_id])
        reserve.reserve_division = reserve_division
        reserves_available.append(reserve)

    return reserves_available


def clear_reserves_available(database: Database):
    """ """

    database.connect()
    sql = f"DELETE FROM {RESERVES_AVAILABLE_TABLE_NAME}"
    database.cursor.execute(sql)
    database.commit()
    database.close()


def clear_reserve_requests(database: Database):
    """ """

    database.connect()
    sql = f"DELETE FROM {RESERVE_REQUESTS_TABLE_NAME}"
    database.cursor.execute(sql)
    database.commit()
    database.close()
