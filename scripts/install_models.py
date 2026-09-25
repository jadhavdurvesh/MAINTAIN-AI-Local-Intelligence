#!/usr/bin/env python3
"""Prepare optional local model dependencies/checkpoints.

No model training is performed. This script only installs optional packages and
caches released pretrained checkpoints.
"""
from __future__ import annotations
import argparse
import subprocess
import sys


def run(*args):
    subprocess.run(list(args), check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--forecasts', action='store_true', help='cache Timer and Chronos-2')
    p.add_argument('--timeradar', action='store_true', help='install TimeRadar dependencies')
    args = p.parse_args()

    if args.timeradar:
        run(sys.executable, '-m', 'pip', 'install', 'torch', 'transformers', 'safetensors', 'torch-frft')
        print('TimeRadar dependencies installed. Download the TimeRadar checkpoint into a local private model directory.')

    if args.forecasts:
        run(sys.executable, '-m', 'pip', 'install', 'torch', 'transformers', 'chronos-forecasting')
        run(sys.executable, '-c', "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('thuml/timer-base-84m', trust_remote_code=True)")
        run(sys.executable, '-c', "from chronos import Chronos2Pipeline; Chronos2Pipeline.from_pretrained('amazon/chronos-2')")
        print('Timer and Chronos-2 checkpoints cached.')

    if not args.timeradar and not args.forecasts:
        print('Nothing selected. Use --timeradar and/or --forecasts.')

if __name__ == '__main__':
    main()
