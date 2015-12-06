#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 朔のキャッシュをmikaのデータベースへインポートします
# 使い方:
#    python3 cache2db.py path/to/cache/dir
#   OR
#    python3 cache2db.py --exclude-removed path/to/cache/dir

# DBの設定
DB_NAME = 'mika'
DB_USER = 'root'
DB_PASSWD = 'root'



from mysql.connector import connect as mysqlConnect
import os
import sys
import binascii
from datetime import datetime
import base64

def load_text(fname):
	with open(fname,'r',encoding='utf-8') as fh:
		return fh.read()
def log(s):
	sys.stdout.buffer.write((s + "\n").encode('UTF-8'))

def main():
	con = mysqlConnect(db=DB_NAME, user=DB_USER, passwd=DB_PASSWD)
	cur = con.cursor()

	cache_dir = './cache'
	add_removed_record = True
	for argv in sys.argv:
		if argv.startswith('--'):
			if argv=='--exclude-removed':
				add_removed_record = False
			else:
				print('err')
				return 1
		else:
			cache_dir = argv
	cache_dir.rstrip('/')

	cut_index = len('thread_')
	count_all_rec = 0
	for thread in sorted(os.listdir(cache_dir)):
		thread_title = binascii.unhexlify(thread[cut_index:]).decode('utf-8','replace')

		con.start_transaction()
		cur.execute('select id from thread where title=%s', (thread_title,))
		ret = cur.fetchone()
		if not ret:
			cur.execute('insert into thread(title) values(%s)',(thread_title,))
			cur.execute('select last_insert_id()')
			ret = cur.fetchone()
		thread_id = int(ret[0])
		#con.commit()
		count_rec = 0
		for is_removed in [0,1]:
			if not add_removed_record and is_removed:
				break
			dir_path = cache_dir+'/'+thread+'/record'
			if is_removed:
				dir_path = cache_dir+'/'+thread+'/removed'
			for record in sorted(os.listdir(dir_path)):
				count_rec += 1
				count_all_rec += 1

				record_stamp = datetime.fromtimestamp(int(record[:record.index('_')]))
				record_id = record[record.index('_')+1:]
				record_id_bin = binascii.a2b_hex(record_id)

				cur.execute(
						'select r.thread_id from record as r where r.thread_id=%s and r.timestamp=%s and r.bin_id=%s'+ \
						'union select rr.thread_id from record_removed as rr where rr.thread_id=%s and rr.timestamp=%s and rr.bin_id=%s',
						(thread_id, record_stamp, record_id_bin)*2)
				if len(cur.fetchall()):
					continue

				if is_removed:
					cur.execute('insert into record_removed(thread_id, bin_id, timestamp) values(%s,%s,%s)', (thread_id, record_id_bin, record_stamp))
					continue

				record_raw = load_text(cache_dir+'/'+thread+'/record/'+record).strip()
				tmp, md5_hex, body_raw = record_raw.split('<>', 2)
				record_body = {}
				for i in body_raw.split('<>'):
					s = i.index(':')
					record_body[i[:s]] = i[s+1:]

				column = [thread_id, record_stamp, record_id_bin]
				columnName = list('thread_id timestamp bin_id'.split())

				column.extend((
					record_body.get('name',''),
					record_body.get('mail',''),
					record_body.get('body',''),))
				columnName.extend('name mail body'.split())

				column.extend((body_raw,))
				columnName.extend('raw_body'.split())

				if 'remove_id' in record_body:
					column.extend((
						record_body['remove_id'],
						record_body['remove_stamp']))
					columnName.extend('remove_id remove_stamp'.split())
				if 'attach' in record_body:
					column.extend([
						base64.b64decode(record_body['attach']),
						record_body['suffix'],])
					columnName.extend('attach suffix'.split())
				if 'pubkey' in record_body:
					column.extend((
						record_body['pubkey'],
						record_body['sign'],
						record_body['target']))
					columnName.extend('pubkey sign target'.split())
				log("\t".join((str(count_all_rec), str(count_rec), thread_title, record_id, str(record_stamp))))

				cur.execute('insert into record({}) values({})'.format(','.join(columnName), ','.join(['%s']*len(columnName))),
						column)
		con.commit()

	cur.close()
	con.close()

if __name__=='__main__':
	main()
