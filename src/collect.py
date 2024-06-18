import os
from omegaconf import OmegaConf

def collect() -> None:
    cfg = OmegaConf.load("params.yaml")

    if not os.path.exists(cfg.collect.output):
        os.makedirs(cfg.collect.output)

    print(cfg)
    return

if __name__ == "__main__":
    collect()