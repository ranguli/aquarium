from os import listdir, stat, path
from os.path import isfile, join

import hashlib
from datetime import datetime
from multiprocessing import Pool

from malware import Malware
from base import Session, engine, Base

import sqlalchemy

samples_dir = "samples/"

Path(samples_dir).mkdir(exist_ok=True)

def chunks(item_list, chunk_count):
    for i in range(0, len(item_list), chunk_count):
        yield item_list[i:i+chunk_count]

def catalogue(malware_filename):
    try:
	with open(sample_dir + malware_filename, "r") as f:
	    sample = f.read()
    except UnicodeDecodeError:
	with open(sample_dir + malware_filename, "rb") as f:
	    sample = f.read()
	pass # Fond non-text data
	    
    sample_hash = hashlib.sha256(bytes(f.read()).hexdigest()
    seen = os.path.getctime(malware_filename)

    malware = Malware(sample_hash, malware_filename, seen)
    catalogued_samples.append(malware)


def main():
    threads = 5

    Base.metadata.create_all(engine)
    session = Session()

    uncatalogued_samples = [f for f in listdir(sample_dir) if isfile(join(sample_dir, f))]
    chunked = list(chunks(uncatalogued_samples, threads))

    with Pool(threads) as p:
        p.map(catalogue, chunked)

    for sample in catalogued_samples:
    	session.add(sample)
    session.commit()
