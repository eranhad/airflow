def get_latest_timestamp(conn, sql_command):
    try:
        cursor = conn.cursor()
        cursor.execute(sql_command)
        last_timestamp = cursor.fetchall()
        last_timestamp = last_timestamp[0][0]
        last_timestamp = str(last_timestamp).replace(' ', 'T')

    except Exception as e:
        error = f"error occurred while fetching latest value: {e} {last_timestamp}"
        conn.rollback()
        raise Exception(error)
    else:
        conn.commit()
        return last_timestamp


def write_log_dbadb(conn, name, start_time, end_time, row_count, error_message):
    SQL_COMMAND = f""" \
INSERT INTO [dbo].actionLog \
(indiceName, startTime, endTime, rowNum, errorMsg) \
VALUES (%s, %s, %s, %d, %s)"""

    try:
        cursor = conn.cursor()
        cursor.execute(SQL_COMMAND, (name, start_time, end_time, row_count, error_message))

    except Exception as e:
        error = f"error occurred while writing log: {e}"
        conn.rollback()
        raise Exception(error)

    else:
        conn.commit()
