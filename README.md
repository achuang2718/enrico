# enrico, the Fermi1 lab assistant

Handles real-time image logging, analysis, and plotting for day-to-day data taking in Fermi1. Built on https://github.com/biswaroopmukherjee/breadboard-python-client.

Also monitors/controls the numerous assorted sensors/actuators around the lab (e.g. optical powers, vacuum pressures, laser locks, etc.) and sends customized Slack status updates.

## Getting started

*System Requirements*
Create a conda environment from enrico.yml. Requirements that are installed via pip can be found in pipRequirements.txt.

*Config files*
There are several .json files that need to be configured, indicating where
- the BEC1server is mounted,
- matlab analysis code is stored,
- the breadboard-python-client is stored.

There are also private API keys (ask me for them) that need to be stored in enrico/API_config_private.
