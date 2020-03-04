import csv
import os
from urllib import request
from pathlib import Path
from multiprocessing import Pool
from datetime import datetime
from pathvalidate import sanitize_filename

import requests
from hurry.filesize import size

filesize_limit = 10000000 # 10MB per sample. If the malware is bigger than that, they should write smaller malware.

urlhaus_dump = "urlhaus_online.csv"
urlhaus_dump_url = "https://urlhaus.abuse.ch/downloads/csv_online/"
samples_dir = "samples/"

dump_exists = os.path.isfile(urlhaus_dump)

def chunks(item_list, chunk_count):
    for i in range(0, len(item_list), chunk_count):
        yield item_list[i:i+chunk_count]

def process_chunk(dump):

    for row in dump:
        if not row.startswith("#") and row:
            url = row.split(",")[2]
            if url.startswith('"') and url.endswith('"'):
                url = url[1:-1]

                try: 
                    url_headers = dict(request.urlopen(url).getheaders())
                except:
                    print("Received an error code from {url}, skipping.".format(url=url))
                    continue

                try:
                    content_type = url_headers.get("Content-Type").split(";")[0]
                except:
                    continue

                content_length = url_headers.get("Content-Length")

                filename = url.split("/")[-1]
                if not filename:
                    filename = sanitize_filename(url)


                if not os.path.isfile(samples_dir + "/" + filename) and content_type != "text/html" and int(content_length) <= filesize_limit:
                    print("Downloading {filename} from {url} content type of {content_type}, file size of {content_length}".format(filename=filename,url=url, content_type=content_type, content_length=size(int(content_length))))

                    headers = {
                        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0"
                    }

                    malware_request = requests.get(url, headers=headers, timeout=30)

                    # Write the sample to disk 
                    if type(malware_request.content) == bytes:
                        mode = "wb+"
                    else:
                        mode = "w+"
                    
                    with open(str(samples_dir + filename), mode) as f:
                        f.write(malware_request.content)

def main():
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
        threads = 5

        chunked = list(chunks(dump, threads))
        with Pool(threads) as p:
            p.map(process_chunk, chunked)

if __name__ == "__main__":
    main()
