import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


def get_staff_by_telegram_id(telegram_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM staff
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    staff = cursor.fetchone()

    cursor.close()
    connection.close()
    return staff


def create_staff(full_name: str, citizenship: str, phone: str, telegram_id: int,
                 telegram_username: str, passport_photo_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO staff
        (role_id, full_name, citizenship, phone, telegram_id, telegram_username, passport_photo_id, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (2, full_name, citizenship, phone, telegram_id, telegram_username, passport_photo_id, True)
    )

    connection.commit()

    cursor.close()
    connection.close()


def get_all_staff():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT s.*
        FROM staff s
        LEFT JOIN staff_blacklist sb ON s.staff_id = sb.staff_id
        WHERE s.is_active = 1
          AND s.telegram_id IS NOT NULL
          AND sb.blacklist_id IS NULL
        """
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


def create_default_customer_if_needed():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT customer_id
        FROM customers
        WHERE phone = '000'
        LIMIT 1
        """
    )

    customer = cursor.fetchone()

    if customer:
        customer_id = customer["customer_id"]
    else:
        cursor.execute(
            """
            INSERT INTO customers (full_name, phone, comment)
            VALUES ('Системный заказчик Telegram-бота', '000', 'Создан автоматически для мероприятий через Telegram-бота')
            """
        )
        connection.commit()
        customer_id = cursor.lastrowid

    cursor.close()
    connection.close()
    return customer_id


def create_event(event_date: str, comment: str):
    customer_id = create_default_customer_if_needed()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO events
        (customer_id, format_id, status_id, event_name, event_date, guest_count, reserve_percent, comment, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            customer_id,
            1,
            1,
            "Мероприятие из Telegram-бота",
            event_date,
            1,
            10.00,
            comment,
            True
        )
    )

    connection.commit()
    event_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return event_id


def get_active_event():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM events
        WHERE is_active = 1
          AND staff_required IS NOT NULL
        ORDER BY event_id DESC
        LIMIT 1
        """
    )

    event = cursor.fetchone()

    cursor.close()
    connection.close()
    return event


def add_event_response(event_id: int, staff_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT response_id
        FROM event_responses
        WHERE event_id = %s AND staff_id = %s
        """,
        (event_id, staff_id)
    )

    existing = cursor.fetchone()

    if existing:
        cursor.close()
        connection.close()
        return False

    cursor.execute(
        """
        INSERT INTO event_responses (event_id, staff_id, response_status)
        VALUES (%s, %s, 'Откликнулся')
        """,
        (event_id, staff_id)
    )

    connection.commit()

    cursor.close()
    connection.close()
    return True


def count_event_responses(event_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM event_responses
        WHERE event_id = %s
          AND response_status = 'Откликнулся'
        """,
        (event_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()
    return result["total"]


def close_event(event_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE events
        SET is_active = 0
        WHERE event_id = %s
        """,
        (event_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()


def cancel_event(event_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE events
        SET is_active = 0,
            status_id = 6
        WHERE event_id = %s
        """,
        (event_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()


def get_event_participants(event_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT s.staff_id, s.full_name, s.phone, s.telegram_id, s.telegram_username
        FROM event_responses er
        JOIN staff s ON er.staff_id = s.staff_id
        WHERE er.event_id = %s
          AND er.response_status = 'Откликнулся'
        ORDER BY er.created_at
        """,
        (event_id,)
    )

    result = cursor.fetchall()

    cursor.close()
    connection.close()
    return result


def confirm_event_participants(event_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE event_responses
        SET response_status = 'Подтвержден'
        WHERE event_id = %s
          AND response_status = 'Откликнулся'
        """,
        (event_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()


def get_confirmed_participants(event_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT s.staff_id, s.full_name, s.phone, s.telegram_id, s.telegram_username
        FROM event_responses er
        JOIN staff s ON er.staff_id = s.staff_id
        WHERE er.event_id = %s
          AND er.response_status = 'Подтвержден'
        ORDER BY er.created_at
        """,
        (event_id,)
    )

    result = cursor.fetchall()

    cursor.close()
    connection.close()
    return result


def remove_participant(event_id: int, staff_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM event_responses
        WHERE event_id = %s
          AND staff_id = %s
        """,
        (event_id, staff_id)
    )

    connection.commit()

    cursor.close()
    connection.close()


def find_participant_by_lastname(event_id: int, lastname: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT s.staff_id, s.full_name, s.phone, s.telegram_id
        FROM event_responses er
        JOIN staff s ON er.staff_id = s.staff_id
        WHERE er.event_id = %s
          AND er.response_status = 'Откликнулся'
          AND LOWER(s.full_name) LIKE LOWER(%s)
        LIMIT 1
        """,
        (event_id, f"{lastname}%")
    )

    participant = cursor.fetchone()

    cursor.close()
    connection.close()
    return participant


def clear_old_events():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM event_responses
        WHERE event_id IN (
            SELECT event_id
            FROM events
            WHERE event_date < DATE_SUB(CURDATE(), INTERVAL 2 DAY)
        )
        """
    )

    connection.commit()

    cursor.close()
    connection.close()

def get_registered_staff():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT staff_id, full_name, phone, citizenship, telegram_username, is_active
        FROM staff
        WHERE telegram_id IS NOT NULL
        ORDER BY full_name
        """
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


def find_staff_by_lastname(lastname: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT staff_id, full_name, phone, telegram_id
        FROM staff
        WHERE LOWER(full_name) LIKE LOWER(%s)
        LIMIT 1
        """,
        (f"{lastname}%",)
    )

    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result


def add_staff_to_blacklist(staff_id: int, reason: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO staff_blacklist (staff_id, reason)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE reason = VALUES(reason)
        """,
        (staff_id, reason)
    )

    connection.commit()
    cursor.close()
    connection.close()


def get_blacklist():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT sb.blacklist_id, s.full_name, s.phone, s.telegram_username, sb.reason, sb.created_at
        FROM staff_blacklist sb
        JOIN staff s ON sb.staff_id = s.staff_id
        ORDER BY sb.created_at DESC
        """
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


def is_staff_blacklisted(staff_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT blacklist_id
        FROM staff_blacklist
        WHERE staff_id = %s
        """,
        (staff_id,)
    )

    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result is not None

def remove_staff_from_blacklist(staff_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM staff_blacklist
        WHERE staff_id = %s
        """,
        (staff_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

def get_event_by_date(event_date: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM events
        WHERE event_date = %s
          AND is_active = 1
        ORDER BY event_id DESC
        LIMIT 1
        """,
        (event_date,)
    )

    event = cursor.fetchone()
    cursor.close()
    connection.close()
    return event


def create_event_shift(event_id: int, shift_start: str, shift_end: str, staff_required: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO event_shifts
        (event_id, shift_start, shift_end, staff_required, is_active)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (event_id, shift_start, shift_end, staff_required, True)
    )

    connection.commit()
    shift_id = cursor.lastrowid

    cursor.close()
    connection.close()
    return shift_id


def get_event_shifts(event_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM event_shifts
        WHERE event_id = %s
          AND is_active = 1
        ORDER BY shift_start
        """,
        (event_id,)
    )

    shifts = cursor.fetchall()
    cursor.close()
    connection.close()
    return shifts

def get_shift_by_date_and_start(event_date: str, shift_start: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            e.event_id,
            e.event_date,
            e.comment,
            es.shift_id,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end,
            es.staff_required
        FROM event_shifts es
        JOIN events e ON es.event_id = e.event_id
        WHERE e.event_date = %s
          AND TIME_FORMAT(es.shift_start, '%H:%i') = %s
          AND e.is_active = 1
          AND es.is_active = 1
        ORDER BY es.shift_id DESC
        LIMIT 1
        """,
        (event_date, shift_start)
    )

    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result


def add_shift_response(event_id: int, shift_id: int, staff_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT response_id, response_status
        FROM event_responses
        WHERE event_id = %s
          AND shift_id = %s
          AND staff_id = %s
        """,
        (event_id, shift_id, staff_id)
    )

    existing = cursor.fetchone()

    if existing:
        if existing["response_status"] == "Отказался":
            cursor.execute(
                """
                UPDATE event_responses
                SET response_status = 'Откликнулся'
                WHERE response_id = %s
                """,
                (existing["response_id"],)
            )

            connection.commit()
            cursor.close()
            connection.close()
            return True

        cursor.close()
        connection.close()
        return False

    cursor.execute(
        """
        INSERT INTO event_responses (event_id, shift_id, staff_id, response_status)
        VALUES (%s, %s, %s, 'Откликнулся')
        """,
        (event_id, shift_id, staff_id)
    )

    connection.commit()
    cursor.close()
    connection.close()
    return True


def count_shift_responses(shift_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM event_responses
        WHERE shift_id = %s
          AND response_status = 'Откликнулся'
        """,
        (shift_id,)
    )

    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result["total"]


def close_shift(shift_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE event_shifts
        SET is_active = 0
        WHERE shift_id = %s
        """,
        (shift_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

def get_all_events_with_shifts():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            e.event_id,
            e.event_date,
            e.comment,
            e.is_active AS event_active,
            es.shift_id,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end,
            es.staff_required,
            es.is_active AS shift_active,
            (
                SELECT COUNT(*)
                FROM event_responses er
                WHERE er.shift_id = es.shift_id
                  AND er.response_status = 'Откликнулся'
            ) AS response_count
        FROM events e
        LEFT JOIN event_shifts es ON e.event_id = es.event_id
        WHERE e.staff_required IS NULL
        AND e.is_active = 1
        AND e.status_id != 6
        ORDER BY e.event_date DESC, es.shift_start
        """
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


def get_shift_participants(shift_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            s.staff_id,
            s.full_name,
            s.phone,
            s.telegram_id,
            s.telegram_username,
            er.response_status
        FROM event_responses er
        JOIN staff s ON er.staff_id = s.staff_id
        WHERE er.shift_id = %s
            AND er.response_status IN ('Откликнулся', 'Подтвержден')
        ORDER BY er.created_at
        """,
        (shift_id,)
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result

def confirm_shift_participants(shift_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE event_responses
        SET response_status = 'Подтвержден'
        WHERE shift_id = %s
          AND response_status = 'Откликнулся'
        """,
        (shift_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

def get_events_by_date_with_shifts(event_date: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            e.event_id,
            e.event_date,
            e.comment,
            e.is_active AS event_active,
            es.shift_id,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end,
            es.staff_required,
            es.is_active AS shift_active
        FROM events e
        LEFT JOIN event_shifts es ON e.event_id = es.event_id
        WHERE e.event_date = %s
          AND e.staff_required IS NULL
          AND e.is_active = 1
          AND e.status_id != 6
        ORDER BY es.shift_start
        """,
        (event_date,)
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result

def find_shift_participant_by_lastname(shift_id: int, lastname: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT s.staff_id, s.full_name, s.phone, s.telegram_id
        FROM event_responses er
        JOIN staff s ON er.staff_id = s.staff_id
        WHERE er.shift_id = %s
          AND LOWER(s.full_name) LIKE LOWER(%s)
        LIMIT 1
        """,
        (shift_id, f"{lastname}%")
    )

    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result

def remove_participant_from_shift(shift_id: int, staff_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM event_responses
        WHERE shift_id = %s
          AND staff_id = %s
        """,
        (shift_id, staff_id)
    )

    connection.commit()
    cursor.close()
    connection.close()

def close_event_shifts(event_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE event_shifts
        SET is_active = 0
        WHERE event_id = %s
        """,
        (event_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

def get_event_participants_by_event(event_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT DISTINCT
            s.staff_id,
            s.full_name,
            s.phone,
            s.telegram_id,
            s.telegram_username
        FROM event_responses er
        JOIN staff s ON er.staff_id = s.staff_id
        WHERE er.event_id = %s
        """,
        (event_id,)
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result

def remove_staff_from_shift_response(shift_id: int, staff_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE event_responses
        SET response_status = 'Отказался'
        WHERE shift_id = %s
          AND staff_id = %s
          AND response_status IN ('Откликнулся', 'Подтвержден')
        """,
        (shift_id, staff_id)
    )

    connection.commit()
    updated = cursor.rowcount

    cursor.close()
    connection.close()

    return updated > 0

def has_staff_response_on_event_date(event_date: str, staff_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT er.response_id
        FROM event_responses er
        JOIN events e ON er.event_id = e.event_id
        WHERE e.event_date = %s
          AND er.staff_id = %s
          AND er.response_status IN ('Откликнулся', 'Подтвержден')
        LIMIT 1
        """,
        (event_date, staff_id)
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result is not None

def get_active_events_for_users():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            e.event_id,
            e.event_date,
            e.comment,
            es.shift_id,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end,
            es.staff_required,
            (
                SELECT COUNT(*)
                FROM event_responses er
                WHERE er.shift_id = es.shift_id
                  AND er.response_status IN ('Откликнулся', 'Подтвержден')
            ) AS response_count
        FROM events e
        JOIN event_shifts es ON e.event_id = es.event_id
        WHERE e.is_active = 1
          AND e.status_id != 6
          AND es.is_active = 1
        ORDER BY e.event_date, es.shift_start
        """
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result

def get_staff_active_responses(staff_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            e.event_date,
            e.comment,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end,
            er.response_status
        FROM event_responses er
        JOIN events e ON er.event_id = e.event_id
        JOIN event_shifts es ON er.shift_id = es.shift_id
        WHERE er.staff_id = %s
          AND er.response_status IN ('Откликнулся', 'Подтвержден')
          AND e.is_active = 1
          AND es.is_active = 1
          AND e.status_id != 6
        ORDER BY e.event_date, es.shift_start
        """,
        (staff_id,)
    )

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result

def get_shift_by_id(shift_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            e.event_id,
            e.event_date,
            e.comment,
            es.shift_id,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end,
            es.staff_required
        FROM event_shifts es
        JOIN events e ON es.event_id = e.event_id
        WHERE es.shift_id = %s
          AND e.is_active = 1
          AND es.is_active = 1
          AND e.status_id != 6
        LIMIT 1
        """,
        (shift_id,)
    )

    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result

def get_tomorrow_shift_participants_for_reminder():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            er.response_id,
            s.telegram_id,
            s.full_name,
            e.event_date,
            e.comment,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end
        FROM event_responses er
        JOIN staff s ON er.staff_id = s.staff_id
        JOIN events e ON er.event_id = e.event_id
        JOIN event_shifts es ON er.shift_id = es.shift_id
        LEFT JOIN shift_reminders sr 
            ON sr.response_id = er.response_id
            AND sr.reminder_type = 'tomorrow'
        WHERE e.event_date = DATE_ADD(CURDATE(), INTERVAL 1 DAY)
          AND er.response_status IN ('Откликнулся', 'Подтвержден')
          AND e.is_active = 1
          AND es.is_active = 1
          AND e.status_id != 6
          AND sr.reminder_id IS NULL
        """
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


def mark_shift_reminder_sent(response_id: int, reminder_type: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT IGNORE INTO shift_reminders (response_id, reminder_type)
        VALUES (%s, %s)
        """,
        (response_id, reminder_type)
    )

    connection.commit()
    cursor.close()
    connection.close()

def get_active_events():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT event_id, event_date, comment
        FROM events
        WHERE is_active = 1
          AND status_id != 6
        ORDER BY event_date
        """
    )

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result

def get_active_shifts_for_admin():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            e.event_id,
            e.event_date,
            e.comment,
            es.shift_id,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end,
            es.staff_required,
            (
                SELECT COUNT(*)
                FROM event_responses er
                WHERE er.shift_id = es.shift_id
                  AND er.response_status IN ('Откликнулся', 'Подтвержден')
            ) AS response_count
        FROM events e
        JOIN event_shifts es ON e.event_id = es.event_id
        WHERE e.is_active = 1
          AND e.status_id != 6
          AND es.is_active = 1
        ORDER BY e.event_date, es.shift_start
        """
    )

    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result

def get_staff_active_responses_with_ids(staff_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            er.response_id,
            er.event_id,
            er.shift_id,
            e.event_date,
            e.comment,
            TIME_FORMAT(es.shift_start, '%H:%i') AS shift_start,
            TIME_FORMAT(es.shift_end, '%H:%i') AS shift_end,
            er.response_status
        FROM event_responses er
        JOIN events e ON er.event_id = e.event_id
        JOIN event_shifts es ON er.shift_id = es.shift_id
        WHERE er.staff_id = %s
          AND er.response_status IN ('Откликнулся', 'Подтвержден')
          AND e.is_active = 1
          AND es.is_active = 1
          AND e.status_id != 6
        ORDER BY e.event_date, es.shift_start
        """,
        (staff_id,)
    )

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result

def archive_past_events():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE event_shifts es
        JOIN events e ON es.event_id = e.event_id
        SET es.is_active = 0
        WHERE e.event_date < CURDATE()
        """
    )

    cursor.execute(
        """
        UPDATE events
        SET is_active = 0
        WHERE event_date < CURDATE()
        """
    )

    connection.commit()

    cursor.close()
    connection.close()