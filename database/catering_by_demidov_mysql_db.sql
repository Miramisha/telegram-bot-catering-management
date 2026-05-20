
-- База данных для информационной системы предприятия «Кейтеринг by Demidov»
-- Назначение: учет мероприятий, ресурсов, персонала, автоматический расчет материалов,
-- формирование данных для Excel и подбор персонала через Telegram-бота.

CREATE DATABASE IF NOT EXISTS catering_by_demidov
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE catering_by_demidov;

-- 1. Заказчики
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(100),
    organization_name VARCHAR(150),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Форматы мероприятий: банкет, фуршет, смешанный формат
CREATE TABLE event_formats (
    format_id INT AUTO_INCREMENT PRIMARY KEY,
    format_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

INSERT INTO event_formats (format_name, description) VALUES
('Банкет', 'Мероприятие с посадочными местами для гостей'),
('Фуршет', 'Мероприятие без полной посадки гостей'),
('Смешанный формат', 'Мероприятие, включающее элементы банкета и фуршета');

-- 3. Статусы мероприятий
CREATE TABLE event_statuses (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    status_name VARCHAR(100) NOT NULL UNIQUE
);

INSERT INTO event_statuses (status_name) VALUES
('Заявка создана'),
('Согласование'),
('Подготовка'),
('Проводится'),
('Завершено'),
('Отменено');

-- 4. Мероприятия
CREATE TABLE events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    format_id INT NOT NULL,
    status_id INT NOT NULL DEFAULT 1,
    event_name VARCHAR(200) NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    location VARCHAR(255),
    guest_count INT NOT NULL,
    reserve_percent DECIMAL(5,2) DEFAULT 10.00,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_events_customer
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_events_format
        FOREIGN KEY (format_id) REFERENCES event_formats(format_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_events_status
        FOREIGN KEY (status_id) REFERENCES event_statuses(status_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT chk_guest_count CHECK (guest_count > 0),
    CONSTRAINT chk_reserve_percent CHECK (reserve_percent >= 0)
);

-- 5. Категории ресурсов
CREATE TABLE resource_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

INSERT INTO resource_categories (category_name) VALUES
('Мебель'),
('Текстиль'),
('Посуда'),
('Столовые приборы'),
('Бокалы'),
('Расходные материалы'),
('Оборудование');

-- 6. Ресурсы / материалы / инвентарь
CREATE TABLE resources (
    resource_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    resource_name VARCHAR(150) NOT NULL,
    unit VARCHAR(50) NOT NULL DEFAULT 'шт.',
    total_quantity INT NOT NULL DEFAULT 0,
    available_quantity INT NOT NULL DEFAULT 0,
    comment TEXT,

    CONSTRAINT fk_resources_category
        FOREIGN KEY (category_id) REFERENCES resource_categories(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT chk_total_quantity CHECK (total_quantity >= 0),
    CONSTRAINT chk_available_quantity CHECK (available_quantity >= 0)
);

-- 7. Нормы расчета ресурсов по форматам мероприятий
-- quantity_per_guest показывает, сколько единиц ресурса нужно на 1 гостя.
-- fixed_quantity используется для ресурсов, которые добавляются фиксированно.
CREATE TABLE resource_norms (
    norm_id INT AUTO_INCREMENT PRIMARY KEY,
    format_id INT NOT NULL,
    resource_id INT NOT NULL,
    quantity_per_guest DECIMAL(10,3) DEFAULT 0,
    fixed_quantity INT DEFAULT 0,
    rounding_rule VARCHAR(50) DEFAULT 'CEIL',
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT fk_norms_format
        FOREIGN KEY (format_id) REFERENCES event_formats(format_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_norms_resource
        FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT chk_quantity_per_guest CHECK (quantity_per_guest >= 0),
    CONSTRAINT chk_fixed_quantity CHECK (fixed_quantity >= 0),

    UNIQUE (format_id, resource_id)
);

-- 8. Результаты автоматического расчета ресурсов
CREATE TABLE event_resource_calculations (
    calculation_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    resource_id INT NOT NULL,
    calculated_quantity INT NOT NULL,
    reserve_quantity INT NOT NULL DEFAULT 0,
    final_quantity INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_calc_event
        FOREIGN KEY (event_id) REFERENCES events(event_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_calc_resource
        FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT chk_calculated_quantity CHECK (calculated_quantity >= 0),
    CONSTRAINT chk_reserve_quantity CHECK (reserve_quantity >= 0),
    CONSTRAINT chk_final_quantity CHECK (final_quantity >= 0)
);

-- 9. История Excel-выгрузок
CREATE TABLE excel_exports (
    export_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_excel_event
        FOREIGN KEY (event_id) REFERENCES events(event_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 10. Роли персонала
CREATE TABLE staff_roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

INSERT INTO staff_roles (role_name, description) VALUES
('Повар', 'Приготовление блюд и работа на кухне'),
('Официант', 'Обслуживание гостей на мероприятии'),
('Помощник официанта', 'Подготовка зала и помощь официантам'),
('Грузчик', 'Погрузка, доставка и разгрузка оборудования'),
('Клининг', 'Уборка площадки после мероприятия'),
('Менеджер', 'Координация мероприятия и работа с заказчиком'),
('Бухгалтер', 'Финансовое сопровождение заказа'),
('Руководитель', 'Контроль и анализ деятельности');

-- 11. Персонал
CREATE TABLE staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    telegram_id BIGINT UNIQUE,
    telegram_username VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    comment TEXT,

    CONSTRAINT fk_staff_role
        FOREIGN KEY (role_id) REFERENCES staff_roles(role_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 12. Нормы расчета персонала по форматам мероприятий
-- guests_per_staff показывает, на сколько гостей нужен один сотрудник данной роли.
CREATE TABLE staff_norms (
    staff_norm_id INT AUTO_INCREMENT PRIMARY KEY,
    format_id INT NOT NULL,
    role_id INT NOT NULL,
    guests_per_staff INT NOT NULL,
    minimum_staff INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT fk_staff_norm_format
        FOREIGN KEY (format_id) REFERENCES event_formats(format_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_staff_norm_role
        FOREIGN KEY (role_id) REFERENCES staff_roles(role_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT chk_guests_per_staff CHECK (guests_per_staff > 0),
    CONSTRAINT chk_minimum_staff CHECK (minimum_staff >= 0),

    UNIQUE (format_id, role_id)
);

-- 13. Расчет потребности в персонале
CREATE TABLE event_staff_requirements (
    requirement_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    role_id INT NOT NULL,
    required_count INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_staff_req_event
        FOREIGN KEY (event_id) REFERENCES events(event_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_staff_req_role
        FOREIGN KEY (role_id) REFERENCES staff_roles(role_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT chk_required_count CHECK (required_count >= 0)
);

-- 14. Назначение персонала на мероприятия
CREATE TABLE event_staff_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    staff_id INT NOT NULL,
    assignment_status ENUM('Предложено', 'Принято', 'Отклонено', 'Назначен', 'Отменено') DEFAULT 'Предложено',
    response_time TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_assignment_event
        FOREIGN KEY (event_id) REFERENCES events(event_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_assignment_staff
        FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    UNIQUE (event_id, staff_id)
);

-- 15. Сообщения Telegram-бота
CREATE TABLE telegram_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    staff_id INT,
    telegram_chat_id BIGINT,
    message_text TEXT NOT NULL,
    message_status ENUM('Создано', 'Отправлено', 'Доставлено', 'Ошибка') DEFAULT 'Создано',
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_tg_event
        FOREIGN KEY (event_id) REFERENCES events(event_id)
        ON UPDATE CASCADE ON DELETE SET NULL,

    CONSTRAINT fk_tg_staff
        FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- 16. Финансовые операции
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    payment_type ENUM('Предоплата', 'Доплата', 'Полная оплата', 'Возврат') NOT NULL,
    comment TEXT,

    CONSTRAINT fk_payment_event
        FOREIGN KEY (event_id) REFERENCES events(event_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT chk_payment_amount CHECK (amount >= 0)
);

-- 17. Пользователи системы
CREATE TABLE system_users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    staff_id INT,
    login VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    system_role ENUM('Администратор', 'Менеджер', 'Бухгалтер', 'Руководитель', 'Склад', 'Персонал') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_staff
        FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- Индексы для ускорения поиска
CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_events_customer ON events(customer_id);
CREATE INDEX idx_event_calc_event ON event_resource_calculations(event_id);
CREATE INDEX idx_staff_role ON staff(role_id);
CREATE INDEX idx_assignment_event ON event_staff_assignments(event_id);
CREATE INDEX idx_assignment_staff ON event_staff_assignments(staff_id);

-- Пример ресурсов для демонстрации работы системы
INSERT INTO resources (category_id, resource_name, unit, total_quantity, available_quantity) VALUES
(1, 'Стол банкетный', 'шт.', 300, 300),
(1, 'Стул', 'шт.', 3000, 3000),
(2, 'Скатерть', 'шт.', 500, 500),
(3, 'Тарелка основная', 'шт.', 3500, 3500),
(3, 'Тарелка закусочная', 'шт.', 3500, 3500),
(4, 'Вилка', 'шт.', 3500, 3500),
(4, 'Нож', 'шт.', 3500, 3500),
(4, 'Ложка', 'шт.', 3500, 3500),
(5, 'Бокал', 'шт.', 3500, 3500),
(6, 'Салфетка', 'шт.', 5000, 5000);

-- Пример норм для банкета
INSERT INTO resource_norms (format_id, resource_id, quantity_per_guest, fixed_quantity) VALUES
(1, 1, 0.10, 0),   -- 1 стол на 10 гостей
(1, 2, 1.00, 0),   -- 1 стул на 1 гостя
(1, 3, 0.10, 0),   -- 1 скатерть на 10 гостей
(1, 4, 1.00, 0),
(1, 5, 1.00, 0),
(1, 6, 1.00, 0),
(1, 7, 1.00, 0),
(1, 8, 1.00, 0),
(1, 9, 1.00, 0),
(1, 10, 2.00, 0);

-- Пример норм для фуршета
INSERT INTO resource_norms (format_id, resource_id, quantity_per_guest, fixed_quantity) VALUES
(2, 1, 0.03, 0),   -- меньше столов
(2, 2, 0.20, 0),   -- ограниченное количество стульев
(2, 3, 0.03, 0),
(2, 4, 1.00, 0),
(2, 5, 1.00, 0),
(2, 6, 1.00, 0),
(2, 7, 0.30, 0),
(2, 8, 0.30, 0),
(2, 9, 1.00, 0),
(2, 10, 2.00, 0);

-- Пример норм для смешанного формата
INSERT INTO resource_norms (format_id, resource_id, quantity_per_guest, fixed_quantity) VALUES
(3, 1, 0.07, 0),
(3, 2, 0.70, 0),
(3, 3, 0.07, 0),
(3, 4, 1.00, 0),
(3, 5, 1.00, 0),
(3, 6, 1.00, 0),
(3, 7, 0.70, 0),
(3, 8, 0.70, 0),
(3, 9, 1.00, 0),
(3, 10, 2.00, 0);

-- Пример норм персонала
INSERT INTO staff_norms (format_id, role_id, guests_per_staff, minimum_staff) VALUES
(1, 1, 80, 1),   -- повар
(1, 2, 15, 1),   -- официант
(1, 3, 30, 1),   -- помощник официанта
(1, 4, 100, 1),  -- грузчик
(1, 5, 100, 1),  -- клининг

(2, 1, 100, 1),
(2, 2, 25, 1),
(2, 3, 40, 1),
(2, 4, 120, 1),
(2, 5, 120, 1),

(3, 1, 90, 1),
(3, 2, 20, 1),
(3, 3, 35, 1),
(3, 4, 110, 1),
(3, 5, 110, 1);

-- Представление для Excel-выгрузки ресурсов по мероприятию
CREATE VIEW v_event_resource_excel AS
SELECT
    e.event_id,
    e.event_name AS 'Название мероприятия',
    e.event_date AS 'Дата мероприятия',
    ef.format_name AS 'Формат',
    e.guest_count AS 'Количество гостей',
    rc.category_name AS 'Категория',
    r.resource_name AS 'Ресурс',
    r.unit AS 'Единица измерения',
    erc.calculated_quantity AS 'Расчетное количество',
    erc.reserve_quantity AS 'Резерв',
    erc.final_quantity AS 'Итоговое количество'
FROM event_resource_calculations erc
JOIN events e ON erc.event_id = e.event_id
JOIN event_formats ef ON e.format_id = ef.format_id
JOIN resources r ON erc.resource_id = r.resource_id
JOIN resource_categories rc ON r.category_id = rc.category_id;

-- Представление для контроля персонала по мероприятию
CREATE VIEW v_event_staff_status AS
SELECT
    e.event_id,
    e.event_name AS 'Название мероприятия',
    e.event_date AS 'Дата мероприятия',
    sr.role_name AS 'Роль',
    s.full_name AS 'Сотрудник',
    esa.assignment_status AS 'Статус назначения'
FROM event_staff_assignments esa
JOIN events e ON esa.event_id = e.event_id
JOIN staff s ON esa.staff_id = s.staff_id
JOIN staff_roles sr ON s.role_id = sr.role_id;

-- Процедура автоматического расчета ресурсов
DELIMITER //

CREATE PROCEDURE calculate_event_resources(IN p_event_id INT)
BEGIN
    DECLARE v_guest_count INT;
    DECLARE v_format_id INT;
    DECLARE v_reserve_percent DECIMAL(5,2);

    SELECT guest_count, format_id, reserve_percent
    INTO v_guest_count, v_format_id, v_reserve_percent
    FROM events
    WHERE event_id = p_event_id;

    DELETE FROM event_resource_calculations
    WHERE event_id = p_event_id;

    INSERT INTO event_resource_calculations
    (
        event_id,
        resource_id,
        calculated_quantity,
        reserve_quantity,
        final_quantity
    )
    SELECT
        p_event_id,
        rn.resource_id,
        CEIL((v_guest_count * rn.quantity_per_guest) + rn.fixed_quantity) AS calculated_quantity,
        CEIL(CEIL((v_guest_count * rn.quantity_per_guest) + rn.fixed_quantity) * v_reserve_percent / 100) AS reserve_quantity,
        CEIL((v_guest_count * rn.quantity_per_guest) + rn.fixed_quantity)
        + CEIL(CEIL((v_guest_count * rn.quantity_per_guest) + rn.fixed_quantity) * v_reserve_percent / 100) AS final_quantity
    FROM resource_norms rn
    WHERE rn.format_id = v_format_id
      AND rn.is_active = TRUE;
END //

CREATE PROCEDURE calculate_event_staff_requirements(IN p_event_id INT)
BEGIN
    DECLARE v_guest_count INT;
    DECLARE v_format_id INT;

    SELECT guest_count, format_id
    INTO v_guest_count, v_format_id
    FROM events
    WHERE event_id = p_event_id;

    DELETE FROM event_staff_requirements
    WHERE event_id = p_event_id;

    INSERT INTO event_staff_requirements
    (
        event_id,
        role_id,
        required_count
    )
    SELECT
        p_event_id,
        sn.role_id,
        GREATEST(CEIL(v_guest_count / sn.guests_per_staff), sn.minimum_staff) AS required_count
    FROM staff_norms sn
    WHERE sn.format_id = v_format_id
      AND sn.is_active = TRUE;
END //

DELIMITER ;
