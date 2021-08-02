## CDM-BI Documentation

This branch contains the GitHub pages and the source code to generate those pages. The manual was written in [RMarkdown](https://rmarkdown.rstudio.com) using the [bookdown](https://bookdown.org) package. All the code is stored in the ''src'' directory as well as the script to build all the documentation.

**Do not change** the files in the root, because those files will be removed during the build and replaced by the new ones. Therefore, to update this documentation, change the files in directory ''src''.

To build the documentation, you need to have R installed and if you are using UNIX-based systems, you only need to run `sh _build.sh`  in the directory ''src''.

To edit the images containing the dashboards layout, please use the [Draw.io](https://draw.io) tool and the file ''Dashboards-layout.xml''.