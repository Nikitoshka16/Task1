--5 случайных строк из логов
SELECT * FROM user_logs ORDER BY RANDOM() LIMIT 5;

--среднее значение по s_all_avg
SELECT AVG(s_all_avg) AS average_activity FROM user_logs;

--замена запятых на точки в колонке s_all_avg
UPDATE user_logs 
SET s_all_avg = REPLACE(s_all_avg, ',', '.') 
WHERE s_all_avg LIKE '%,%';

--преобразование текстовых значений в числовой формат REAL
ALTER TABLE user_logs 
ALTER COLUMN s_all_avg TYPE REAL USING s_all_avg::REAL;
