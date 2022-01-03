--- 
title: "Data Network Dashboards"
author: "This document is currently under construction"
date: "2022-01-03"
site: bookdown::bookdown_site
output: bookdown::gitbook
documentclass: book
bibliography: [refs.bib]
biblio-style: apalike
link-citations: yes
github-repo: rstudio/bookdown-demo
description: "This is the manual for setting up a clean installation of the dashboards used in the EHDEN project."
---

# Preface

<!--<img src="images/Cover/Cover.png" width="250" height="375" alt="Cover image" align="right" style="margin: 0 1em 0 1em" /> -->

Automated Characterization of Health Information at Large-scale Longitudinal Evidence Systems (ACHILLES) is a profiling tool developed by the OHDSI community to provide descriptive statistics of databases standardized to the OMOP Common Data Model. These characteristics are presented graphically in the ATLAS tool. However, this solution does not allow for database comparison across the data network. The Data Network Dashboards aggregates ACHILLES results files from databases in the network and displays the descriptive statistics through graphical dashboards. This tool is helpful to gain insight in the growth of the data network and is useful for the selection of databases for specific research questions. In the software demonstration we show a first version of this tool that will be further developed in EHDEN in close collaboration with all our stakeholders, including OHDSI.


### Contributors {-}

To develop this tool, EHDEN organized a hack-a-thon (Aveiro, December 2-3, 2019), where we defined and implemented a series of charts and dashboards containing the most relevant information about the OMOP CDM databases. The team involved in this task were composed by the following members:

* João Rafael Almeida^1^
* André Pedrosa^1^
* Peter R. Rijnbeek^2^
* Marcel de Wilde^2^
* Michel Van Speybroeck^3^
* Maxim Moinat^4^
* Pedro Freire^1^
* Alina Trifan^1^
* Sérgio Matos^1^
* José Luís Oliveira^1^

1 - Institute of Electronics and Informatics Engineering of Aveiro, Department of Electronics and Telecommunication, University of Aveiro, Aveiro, Portugal

2 - Erasmus MC, Rotterdam, Netherlands

3 - Janssen Pharmaceutica NV, Beerse, Belgium

4 - The Hyve, Utrecht, Netherlands

### Considerations {-}

This manual was written to be a guide for a clean installation of this system with all the dashboards that we defined during the project. The first chapter describes the goal of the system and the second how to install the system. The remaining chapters are dedicated to the dashboards, in which chapters describes one dashboard and all its charts. To simplify the representation of the dashboard's layout, we used similar schemas as it is presented in Figure \@ref(fig:dashboardsLayout). The white box is the dashboard and the inside boxes are charts. The colour changes in relation to the type of chart.

<div class="figure">
<img src="images/dashboardsLayout.png" alt="Example of a dashboards tool presenting the databases available in the network (simulated data)" width="100%" />
<p class="caption">(\#fig:dashboardsLayout)Example of a dashboards tool presenting the databases available in the network (simulated data)</p>
</div>

### License {-}

The system is open-source <!--under the license ....-->
and this manual was written in [RMarkdown](https://rmarkdown.rstudio.com) using the [bookdown](https://bookdown.org) package.

### Acknowledges {-}

This work has been conducted in the context of EHDEN, a project that receives funding from the European Union’s Horizon 2020 and EFPIA through IMI2 Joint Undertaking initiative, under grant agreement No 806968.
