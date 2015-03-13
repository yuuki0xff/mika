
-- version: 0.0.1
DROP DATABASE IF EXISTS mika;
CREATE DATABASE mika;
USE mika;

CREATE TABLE SYSTEM(
	id CHAR(10),
	value CHAR(10),
	PRIMARY KEY(id)
);

CREATE TABLE thread(
	-- titleのサイズは適当
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	title CHAR(255) NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	records INT NOT NULL DEFAULT 0,
	UNIQUE i_title(title)
);

CREATE TABLE record(
	thread_id INT UNSIGNED,
	id INT UNSIGNED AUTO_INCREMENT,
	bin_id BINARY(16),
	timestamp TIMESTAMP NOT NULL,
	is_remove_notify BOOLEAN NOT NULL DEFAULT FALSE,
	is_attach BOOLEAN NOT NULL DEFAULT FALSE,
	PRIMARY KEY(id),
	INDEX(thread_id, bin_id, timestamp)
);
CREATE TABLE record_post(
	-- name,mailのサイズは適当
	thread_id INT UNSIGNED,
	record_id INT UNSIGNED,
	name CHAR(255) NOT NULL,
	mail CHAR(255) NOT NULL,
	body MEDIUMTEXT NOT NULL,
	PRIMARY KEY(thread_id, record_id)
);
CREATE TABLE record_attach(
	-- suffixのサイズは適当
	thread_id INT UNSIGNED,
	record_id INT UNSIGNED,
	attach MEDIUMBLOB NOT NULL,
	suffix CHAR(8) NOT NULL,
	PRIMARY KEY(thread_id, record_id)
);
CREATE TABLE record_remove(
	thread_id INT UNSIGNED,
	record_id INT UNSIGNED,
	remove_id BINARY(16) NOT NULL,
	remove_stamp TIMESTAMP NOT NULL,
	PRIMARY KEY(thread_id, record_id)
);
CREATE TABLE record_signature(
	-- 公開鍵の長さは86文字 : http://shingetsu.info/protocol/protocol-0.5-2.pdf
	-- targetのサイズは適当
	thread_id INT UNSIGNED,
	record_id INT UNSIGNED,
	pubkey CHAR(86) NOT NULL,
	sign CHAR(64) NOT NULL,
	target CHAR(64) NOT NULL,
	PRIMARY KEY(thread_id, record_id)
);

CREATE TABLE tagname(
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	name VARCHAR(1024) NOT NULL
);
CREATE TABLE tag(
	tag_id INT UNSIGNED,
	thread_id INT UNSIGNED,
	PRIMARY KEY(tag_id, thread_id)
);

CREATE TABLE node(
	host CHAR(64) PRIMARY KEY,
	linked BOOLEAN NOT NULL DEFAULT false,
	timestamp TIMESTAMP
);


DELIMITER $$

CREATE TRIGGER insert_thread AFTER INSERT ON record FOR EACH ROW
BEGIN
	UPDATE thread SET records = record+1;
	IF NEW.timestamp > (SELECT thread.timestamp FROM thread WHERE NEW.thread_id = thread.id) THEN
		UPDATE thread SET timestamp = NEW.timestamp;
	END IF;
END;
$$

CREATE TRIGGER delete_thread AFTER DELETE ON record FOR EACH ROW
BEGIN
	UPDATE thread SET records = record-1;
	UPDATE thread SET timestamp = (SELECT MAX(record.timestamp)
		FROM thread INNER JOIN record ON thread.id = record.thread_id
		WHERE thread.id = OLD.thread_id);
END;
$$

DELIMITER ;

