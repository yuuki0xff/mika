
-- version: 0.0.4
DROP DATABASE IF EXISTS mika;
CREATE DATABASE mika;
USE mika;

CREATE TABLE SYSTEM(
	id CHAR(10),
	value VARCHAR(255),
	PRIMARY KEY(id)
);
INSERT INTO SYSTEM(id, value) VALUES('version', '0.0.4');

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
	thread_id INT UNSIGNED,
	timestamp TIMESTAMP,
	bin_id BINARY(16),
	-- post
	name CHAR(255),
	mail CHAR(255),
	body MEDIUMTEXT,
	-- attach
	attach MEDIUMBLOB,
	suffix CHAR(8),
	-- remove_notify
	remove_id BINARY(16),
	remove_stamp TIMESTAMP,
	-- signature
	-- 公開鍵の長さは86文字 : http://shingetsu.info/protocol/protocol-0.5-2.pdf
	-- targetのサイズは適当
	pubkey CHAR(86),
	sign CHAR(64),
	target CHAR(64),
	-- raw
	raw_body MEDIUMTEXT NOT NULL,
	PRIMARY KEY(thread_id, timestamp, bin_id),
	FOREIGN KEY(thread_id) REFERENCES thread(id)
);
CREATE TABLE record_removed(
	thread_id INT UNSIGNED,
	timestamp TIMESTAMP,
	bin_id BINARY(16),
	PRIMARY KEY(thread_id, timestamp, bin_id),
	FOREIGN KEY(thread_id) REFERENCES thread(id)
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

CREATE TABLE message_type(
	id INT UNSIGNED AUTO_INCREMENT,
	name CHAR(30) NOT NULL,
	priority TINYINT(1) UNSIGNED NOT NULL,
	PRIMARY KEY(id),
	UNIQUE(name)
);
CREATE TABLE message_queue(
	id INT UNSIGNED AUTO_INCREMENT,
	msgtype_id INT UNSIGNED NOT NULL,
	msg CHAR(255) NOT NULL,
	PRIMARY KEY(id),
	INDEX USING BTREE(msgtype_id, id),
	FOREIGN KEY(msgtype_id) REFERENCES message_type(id)
) ENGINE=MEMORY;
INSERT INTO message_type(priority, name) values
	(50, 'get_record'),
	(60, 'update_record'),
	(70, 'get_thread');

DELIMITER $$

DROP TRIGGER IF EXISTS mika_insert_record $$
CREATE TRIGGER mika_insert_record AFTER INSERT ON record FOR EACH ROW
BEGIN
	UPDATE thread SET thread.records = thread.records+1
	WHERE thread.id = NEW.thread_id;
	IF NEW.timestamp > (SELECT thread.timestamp FROM thread WHERE NEW.thread_id = thread.id) THEN
		UPDATE thread SET timestamp = NEW.timestamp
		WHERE thread.id = NEW.thread_id;
	END IF;

	IF NOT (
		(
		(NEW.attach IS NULL AND NEW.suffix IS NULL) OR
		(NEW.attach IS NOT NULL AND NEW.suffix IS NOT NULL)
		) AND (
		(NEW.remove_id IS NULL) OR
		(NEW.remove_id IS NOT NULL)
		) AND (
		(NEW.pubkey IS NULL AND NEW.sign IS NULL AND NEW.target IS NULL) OR
		(NEW.pubkey IS NOT NULL AND NEW.sign IS NOT NULL AND NEW.target IS NOT NULL)
		)) THEN
		UPDATE record SET thread_id = NULL;
	END IF;
END;
$$
DROP TRIGGER IF EXISTS mika_delete_record $$
CREATE TRIGGER mika_delete_record AFTER DELETE ON record FOR EACH ROW
BEGIN
	UPDATE thread SET thread.records = thread.records-1
	WHERE thread.id = OLD.thread_id;
	INSERT INTO record_removed(thread_id, timestamp, bin_id)
	VALUES(OLD.thread_id, OLD.bin_id, OLD.timestamp);
END;
$$

DROP TRIGGER IF EXISTS mika_insert_record_removed $$
CREATE TRIGGER mika_insert_record_removed AFTER INSERT ON record_removed FOR EACH ROW
BEGIN
	UPDATE thread SET thread.removed_records = thread.removed_records+1
	WHERE thread.id = NEW.thread_id;
END;
$$
DROP TRIGGER IF EXISTS mika_delete_record_removed $$
CREATE TRIGGER mika_delete_record_removed AFTER DELETE ON record_removed FOR EACH ROW
BEGIN
	UPDATE thread SET thread.removed_records = thread.removed_records-1
	WHERE thread.id = OLD.thread_id;
END;
$$

DELIMITER ;

