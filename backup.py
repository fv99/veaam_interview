import os
import time
from datetime import datetime
import hashlib # for md5
import shutil # for file operations
import argparse # for arguments

def calc_md5(filepath):
	hash = hashlib.md5()
	try:
		with open(filepath, 'rb') as f: # open file in read binary mode
			while True:
				chunk = f.read(8192) # chunk size
				if not chunk:
					break
				hash.update(chunk)
	except FileNotFoundError:
		return None
	return hash.hexdigest()

def log(msg, logfile):
	timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	full_msg = f"[{timestamp}] {msg}"

	print (full_msg)
	if logfile:
		with open(logfile, 'a', encoding='utf-8') as f:
			f.write(full_msg + '\n')

# synchronizes the dest folder with the source folder
# for each file:
# - if not in dest, copy it
# - if MD5 does not match, copy it
# - if not in source, delete it
def sync(source, dest, logfile):

	# add or update files from source to destination dir
	for root, dirs, files in os.walk(source):
		# make relative paths from source and replica
		rel_source = os.path.relpath(root, source)
		dest_root = os.path.join(dest, rel_source)

		# create directory structure in destination folder
		if not os.path.exists(dest_root):
			os.makedirs(dest_root)
			log(f"Created directory: {dest_root}", logfile)
		
		for d in dirs:
			source_dir = os.path.join(root, d)
			dest_dir = os.path.join(dest_root, d)
			if not os.path.exists(dest_dir):
				os.makedirs(dest_dir)
				log(f"Created directory: {dest_dir}", logfile)

		# process files
		for file in files:
			source_file = os.path.join(root, file)
			dest_file = os.path.join(dest_root, file)

			# calculate checksum
			source_md5 = calc_md5(source_file)
			if os.path.exists(dest_file):
				dest_md5 = calc_md5(dest_file)
			else:
				dest_md5 = None

			# if checksum does not match, copy/replace
			if source_md5 != dest_md5:
				shutil.copy2(source_file, dest_file)
				if dest_md5 is None:
					log(f"Copied new file: {source_file} to {dest_file}", logfile)
				else:
					log(f"Updated file: {source_file} to {dest_file}", logfile)

	# delete files/dirs in destination folder which are not in source
	for root, dirs, files in os.walk(dest, topdown=False):
		# make relative path from destination folder
		rel_path = os.path.relpath(root, dest)
		source_root = os.path.join(source, rel_path)

		# process files
		for file in files:
			dest_file = os.path.join(root, file)
			source_file = os.path.join(source_root, file)
			if not os.path.exists(source_file):
				os.remove(dest_file)
				log(f"Deleted file: {dest_file}", logfile)
		
		# process directories
		for d in dirs:
			dest_dir = os.path.join(root, d)
			source_dir = os.path.join(source_root, d)
			if not os.path.exists(source_dir):
				shutil.rmtree(dest_dir)
				log(f"Deleted directory: {dest_dir}", logfile)

def main():
	parser = argparse.ArgumentParser(prog="Veeam test task", description="One way folder backup")
	parser.add_argument("-s", required=True, help="Path to the source folder")
	parser.add_argument("-d", required=True, help="Path to the destination folder")
	parser.add_argument("-i", required=True, help="Synchronization interval (in seconds)")
	parser.add_argument("-l", required=True, help="Path to the logfile")

	args = parser.parse_args()
	source = args.s
	dest = args.d
	interval = int(args.i)
	logfile = args.l

	# create destination folder if does not exist
	if not os.path.exists(dest):
		os.makedirs(dest)

	log("Starting folder sync...", logfile)
	log(f"Source folder: {source}", logfile)
	log(f"Destination folder: {dest}", logfile)
	log(f"Sync interval: {interval} seconds", logfile)
	log(f"Logfile: {logfile}", logfile)

	while True:
		try:
			sync(source, dest, logfile)
		except Exception as e:
			log(f"Error: {e}", logfile)
		log("Synchronization completed", logfile)
		time.sleep(interval)

if __name__ == "__main__":
	main()