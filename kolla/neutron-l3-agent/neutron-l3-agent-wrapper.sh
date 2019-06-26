#!/bin/bash

set -o errexit


neutron-l3-agent \
        --config-file /etc/neutron/neutron.conf \
        --config-file /etc/neutron/neutron_vpnaas.conf \
        --config-file /etc/neutron/l3_agent.ini \
        --config-file /etc/neutron/fwaas_driver.ini
