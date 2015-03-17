
-- version: 0.0.2
DROP DATABASE IF EXISTS mika;
CREATE DATABASE mika;
USE mika;

CREATE TABLE SYSTEM(
	id CHAR(10),
	value VARCHAR(255),
	PRIMARY KEY(id)
);
INSERT INTO SYSTEM(id, value) VALUES('version', '0.0.2');

CREATE TABLE thread(
	-- titleのサイズは適当
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	title CHAR(255) NOT NULL,
	timestamp TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00',
	records INT NOT NULL DEFAULT 0,
	removed_records INT NOT NULL DEFAULT 0,
	UNIQUE(title),
	INDEX(timestamp, id)
);

CREATE TABLE record(
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	thread_id INT UNSIGNED NOT NULL,
	bin_id BINARY(16) NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	is_post BOOLEAN NOT NULL DEFAULT TRUE,
	is_remove_notify BOOLEAN NOT NULL DEFAULT FALSE,
	is_attach BOOLEAN NOT NULL DEFAULT FALSE,
	INDEX(thread_id, timestamp)
);
CREATE TABLE record_removed(
	thread_id INT UNSIGNED,
	timestamp TIMESTAMP,
	bin_id BINARY(16),
	PRIMARY KEY(thread_id, timestamp, bin_id)
);
CREATE TABLE record_post(
	-- name,mailのサイズは適当
	record_id INT UNSIGNED,
	name CHAR(255) NOT NULL,
	mail CHAR(255) NOT NULL,
	body MEDIUMTEXT NOT NULL,
	PRIMARY KEY(record_id)
);
CREATE TABLE record_attach(
	-- suffixのサイズは適当
	record_id INT UNSIGNED,
	attach MEDIUMBLOB NOT NULL,
	suffix CHAR(8) NOT NULL,
	PRIMARY KEY(record_id)
);
CREATE TABLE record_remove_notify(
	record_id INT UNSIGNED,
	remove_id BINARY(16) NOT NULL,
	remove_stamp TIMESTAMP NOT NULL,
	PRIMARY KEY(record_id)
);
CREATE TABLE record_signature(
	-- 公開鍵の長さは86文字 : http://shingetsu.info/protocol/protocol-0.5-2.pdf
	-- targetのサイズは適当
	record_id INT UNSIGNED,
	pubkey CHAR(86) NOT NULL,
	sign CHAR(64) NOT NULL,
	target CHAR(64) NOT NULL,
	PRIMARY KEY(record_id)
);
CREATE TABLE record_raw(
	record_id INT UNSIGNED,
	md5 BINARY(16) NOT NULL,
	body MEDIUMTEXT NOT NULL,
	PRIMARY KEY(record_id)
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

CREATE TRIGGER insert_record AFTER INSERT ON record FOR EACH ROW
BEGIN
	UPDATE thread SET thread.records = thread.records+1
	WHERE thread.id = NEW.thread_id;
	IF NEW.timestamp > (SELECT thread.timestamp FROM thread WHERE NEW.thread_id = thread.id) THEN
		UPDATE thread SET timestamp = NEW.timestamp
		WHERE thread.id = NEW.thread_id;
	END IF;
END;
$$
CREATE TRIGGER delete_record AFTER DELETE ON record FOR EACH ROW
BEGIN
	UPDATE thread SET thread.records = thread.records-1
	WHERE thread.id = OLD.thread_id;
	INSERT INTO record_removed(thread_id, timestamp, bin_id)
	VALUES(OLD.thread_id, OLD.bin_id, OLD.timestamp);
END;
$$

CREATE TRIGGER insert_record_removed AFTER INSERT ON record_removed FOR EACH ROW
BEGIN
	UPDATE thread SET thread.removed_records = thread.removed_records+1
	WHERE thread.id = NEW.thread_id;
END;
$$
CREATE TRIGGER delete_record_removed AFTER DELETE ON record_removed FOR EACH ROW
BEGIN
	UPDATE thread SET thread.removed_records = thread.removed_records-1
	WHERE thread.id = OLD.thread_id;
END;
$$

DELIMITER ;

