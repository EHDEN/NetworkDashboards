# Documentation

## Requirements (Debian)

```sh
sudo apt install -y r-base pandoc pandoc pandoc-citeproc texlive-xetex
sudo Rscript -e 'install.packages("bookdown")'
```

## How to build

1. Change ONLY the files on the `docs/src` directory.

2. Run the `_build.sh` script
