import hashlib
import os
from datetime import datetime
import tempfile
from urllib.parse import urlparse

from source import Source
from sample import Sample
from base import Session, engine, Base

from minio import Minio, error
import requests
from pathvalidate import sanitize_filename
from hurry.filesize import size

filesize_limit = 10000000  # 10MB per sample. If the malware is bigger than that, they should write smaller malware.

urlhaus_dump = "urlhaus_online.csv"
urlhaus_dump_url = "https://urlhaus.abuse.ch/downloads/csv_online/"

Base.metadata.create_all(engine)
session = Session()

minio_client = Minio(
    "127.0.0.1:9001", access_key="minio", secret_key="minio123", secure=False
)

dump_exists = os.path.isfile(urlhaus_dump)

seen = set()
down = set()


def process_sample(row):

    if not row.startswith("#") and row:
        url = row.split(",")[2]
        if url.startswith('"') and url.endswith('"'):
            url = url[1:-1]
            domain = urlparse(url).netloc

            if url not in seen and domain not in down:

                seen.add(url)

                try:
                    response = requests.head(url, allow_redirects=False, timeout=2)
                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ConnectTimeout,
                    requests.exceptions.ReadTimeout,
                ):
                    down.add(domain)
                    return

                if response.status_code == requests.codes.ok:
                    try:
                        content_type = response.headers.get("Content-Type").split(";")[
                            0
                        ]
                    except:
                        print("No content type specified. Can't guarantee this is a file we're interested in.")
                        return

                    content_length = response.headers.get("Content-Length")

                    filename = url.split("/")[-1]
                    if not filename:
                        filename = sanitize_filename(url)

                    if (
                        content_type != "text/html"
                        and content_length
                        and int(content_length) <= filesize_limit # Don't accidentally download gigantic files
                    ):

                        headers = {
                            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0"
                        }

                        try:
                            # Being explicit about the timeouts is important, otherwise you'll basically tarpit yourself.
                            malware_request = requests.get(
                                url, headers=headers, timeout=(30, 30)
                            )
                        except (
                            requests.exceptions.ConnectionError,
                            requests.exceptions.ConnectTimeout,
                            requests.exceptions.ReadTimeout,
                        ):
                            down.add(domain)
                            return

                        print(
                            "Downloading {filename} from {url} content type of {content_type}, file size of {content_length}".format(
                                filename=filename,
                                url=url,
                                content_type=content_type,
                                content_length=size(int(content_length)),
                            )
                        )

                        fp = tempfile.NamedTemporaryFile()
                        fp.write(bytes(malware_request.content))

                        fp.seek(0)
                        sha256hash = hashlib.sha256(fp.read()).hexdigest()
                        fp.seek(0)
                        md5hash = hashlib.md5(fp.read()).hexdigest()

                        print(
                            "Got SHA256 hash of {sha256hash}".format(
                                sha256hash=sha256hash
                            )
                        )
                        print("Got MD5 hash of {md5hash}".format(md5hash=md5hash))

                        if sha256hash not in [
                            item.object_name
                            for item in minio_client.list_objects("samples")
                        ]:
                            print("Uploading sample to MinIO store")
                            minio_client.fput_object("samples", sha256hash, fp.name)
                            session.add(
                                Sample(sha256hash, md5hash, filename, content_type)
                            )
                        else:
                            print("Sample with that hash already in MinIO store")

                        fp.close()

                        source = Source(sha256hash, url, datetime.now())

                        session.add(source)
                        session.commit()

                    else:
                        return


def main():

    if dump_exists:
        filestat = os.stat(urlhaus_dump)

        now = datetime.now()
        download_time = datetime.fromtimestamp(filestat.st_ctime)
        lapsed = now - download_time

    elif not dump_exists or filestat.st_size == 0 or lapsed.total_seconds > 3600:
        print(
            "{dumpfile} does not exist, is invalid, or is stale. Re-downloading from {url}".format(
                dumpfile=urlhaus_dump, url=urlhaus_dump_url
            )
        )
        r = requests.get(urlhaus_dump_url)
        with open(urlhaus_dump, "w") as f:
            f.write(r.text)

    try:
        minio_client.make_bucket("samples")
    except error.BucketAlreadyOwnedByYou:
        pass

    with open(urlhaus_dump, "r") as f:
        dump = f.read().split("\n")

        for row in dump:
            process_sample(row)


if __name__ == "__main__":
    main()
