import hashlib
import csv
import os
import random
from datetime import datetime
from urllib import request
from pathlib import Path
from multiprocessing import Pool
from datetime import datetime

from malware import Malware
from base import Session, engine, Base

import sqlalchemy
import requests
from pathvalidate import sanitize_filename
from hurry.filesize import size

filesize_limit = 10000000 # 10MB per sample. If the malware is bigger than that, they should write smaller malware.

urlhaus_dump = "urlhaus_online.csv"
urlhaus_dump_url = "https://urlhaus.abuse.ch/downloads/csv_online/"
samples_dir = "samples/"

catalogued_samples = []

if not os.path.exists(samples_dir):
    os.mkdir(samples_dir)

dump_exists = os.path.isfile(urlhaus_dump)

def chunks(item_list, chunk_count):
    for i in range(0, len(item_list), chunk_count):
        yield item_list[i:i+chunk_count]

def process_chunk(dump):
    thread_id = random.randint(0, 100)

    for row in dump:
        if not row.startswith("#") and row:
            url = row.split(",")[2]
            if url.startswith('"') and url.endswith('"'):
                url = url[1:-1]

                try: 
                    print("[{thread_id}] Getting headers of {url}".format(url=url, thread_id=thread_id))
                    url_headers = dict(request.urlopen(url).getheaders())
                except:
                    print("[{thread_id}] Received an error code from {url}, skipping.".format(url=url, thread_id=thread_id))
                    continue

                try:
                    content_type = url_headers.get("Content-Type").split(";")[0]
                except:
                    continue

                content_length = url_headers.get("Content-Length")

                filename = url.split("/")[-1]
                if not filename:
                    filename = sanitize_filename(url)


                if not os.path.isfile(samples_dir + "/" + filename) and content_type != "text/html" and content_length and int(content_length) <= filesize_limit:
                    print("[{thread_id}] Downloading {filename} from {url} content type of {content_type}, file size of {content_length}".format(filename=filename,url=url, content_type=content_type, content_length=size(int(content_length)), thread_id=thread_id))

                    headers = {
                        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0"
                    }

                    malware_request = requests.get(url, headers=headers, timeout=30)
                    print("[{thread_id}] Downloaded {filename}".format(filename=filename, thread_id=thread_id))

                    # Write the sample to disk 
                    print("[{thread_id}] Writing {filename} to disk".format(filename=filename, thread_id=thread_id))

                    if type(malware_request.content) == bytes:
                        mode = "wb+"
                    else:
                        mode = "w+"
                    
                    with open(str(samples_dir + filename), mode) as f:
                        f.write(malware_request.content)


                    # Reopen the file either as plaintext or binary, hash it, and catalogue it
                    print("[{thread_id}] Calculating the SHA256 hash of {filename}".format(filename=filename, thread_id=thread_id))

                    try:
                        with open(samples_dir + filename, "r") as f:
                            sample_hash = hashlib.sha256(bytes(f.read(), encoding="utf-8")).hexdigest()
                    except UnicodeDecodeError:
                        with open(samples_dir + filename, "rb") as f:
                            sample_hash = hashlib.sha256(bytes(f.read())).hexdigest()
                    
                    print("[{thread_id}] Got SHA256 hash of {sample_hash}".format(sample_hash=sample_hash, thread_id=thread_id))
                            
                    seen = os.path.getctime(samples_dir + filename)

                    malware = Malware(sample_hash, filename, url, seen)
                    catalogued_samples.append(malware)
                else:
                    print("[{thread_id}] Skipping URL {url} because its HTML, we already downloaded its sample, or the file is above our size limit.".format(url=url, thread_id=thread_id))

def main():

    Base.metadata.create_all(engine)
    session = Session()

    if dump_exists:
        filestat = os.stat(urlhaus_dump)

        now = datetime.now()
        download_time = datetime.fromtimestamp(filestat.st_ctime)
        lapsed = now - download_time

    elif not dump_exists or filestat.st_size == 0 or lapsed.total_seconds > refresh_wait:
        print("{dumpfile} does not exist, is invalid, or is stale. Re-downloading from {url}".format(dumpfile=urlhaus_dump, url=urlhaus_dump_url))
        r = requests.get(urlhaus_dump_url)
        with open(urlhaus_dump, "w") as f:
            f.write(r.text)

    with open(urlhaus_dump, "r") as f:
        dump = f.read().split("\n")
        threads = 20

        chunked = list(chunks(dump, threads))
        with Pool(threads) as p:
            p.map(process_chunk, chunked)

    for sample in catalogued_samples:
        session.add(sample)
    session.commit()

if __name__ == "__main__":
    main()
