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
import time
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
	for thread in os.listdir(cache_dir):
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
			for record in os.listdir(dir_path):
				count_rec += 1
				count_all_rec += 1

				record_stamp = datetime.fromtimestamp(int(record[:record.index('_')]))
				record_id = record[record.index('_')+1:]
				record_id_bin = binascii.a2b_hex(record_id)
				record_id_hex = '0x'+record_id

				cur.execute(
						'select r.thread_id from record as r where r.thread_id=%s and r.timestamp=%s and r.bin_id=%s'+ \
						'union select rr.thread_id from record_removed as rr where rr.thread_id=%s and rr.timestamp=%s and rr.bin_id=%s',
						(thread_id, record_stamp, record_id_bin)*2)
				if len(cur.fetchall()):
					continue

				if is_removed:
					cur.execute('insert into record_removed(thread_id, bin_id, timestamp) values(%s,%s,%s)', (thread_id, record_id_bin, record_stamp))
					continue

				records = load_text(cache_dir+'/'+thread+'/record/'+record).strip().split('<>')
				record_body = {}
				for i in records[2:]:
					s = i.index(':')
					record_body[i[:s]] = i[s+1:]
				is_rm_notify = False
				is_attach = False
				is_sign = False
				if 'remove_id' in record_body:
					is_rm_notify = True
				if 'attach' in record_body:
					is_attach = True
				if 'pubkey' in record_body:
					is_sign = True
				log("\t".join((str(count_all_rec), str(count_rec), thread_title, record_id, str(record_stamp))))

				#con.start_transaction()
				cur.execute('insert into record(thread_id, bin_id, timestamp, is_post, is_remove_notify, is_attach) values(%s,%s,%s,%s,%s,%s)',(thread_id, record_id_bin, record_stamp, True, is_rm_notify, is_attach))
				cur.execute('select last_insert_id()')
				id = cur.fetchone()[0]
				cur.execute('insert into record_post(record_id, name, mail, body) values(%s,%s,%s,%s)',(
					id,
					record_body.get('name',''),
					record_body.get('mail',''),
					record_body.get('body',''),))
				if is_rm_notify:
					cur.execute('insert into record_remove_notify(record_id, remove_id, remove_stamp) values(%s,%s,%s)', (
						id,
						record_body['remove_id'],
						record_body['remove_stamp']))
				if is_attach:
					cur.execute('insert into record_attach(record_id, attach, suffix) values(%s,%s,%s)', (
						id,
						base64.b64decode(record_body['attach']),
						record_body['suffix']))
				if is_sign:
					cur.execute('insert into record_signature(record_id, pubkey, sign, target) values(%s,%s,%s,%s)', (
						id,
						record_body['pubkey'],
						record_body['sign'],
						record_body['target']))

				#con.commit()
		con.commit()

	cur.close()
	con.close()

if __name__=='__main__':
	main()
