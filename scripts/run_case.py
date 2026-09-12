import argparse
import json
from pathlib import Path
from breedframe.agent import Agent
from breedframe.classifier import Classifier
from breedframe.controller import Controller
from breedframe.store import Store
from breedframe.config import ROOT

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("photo", type=Path)
    parser.add_argument("--resume")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    store = Store(ROOT / "data/cli-cases")
    case = (
        store.add_photo(store.load(args.resume), args.photo.read_bytes())
        if args.resume
        else store.create(args.photo.read_bytes())
    )
    classifier = Classifier()
    try:
        Agent(store, Controller(), classifier).run(case)
    finally:
        classifier.close()
    result = json.dumps(case, indent=2)
    if args.output:
        args.output.write_text(result + "\n")
    print(result)
