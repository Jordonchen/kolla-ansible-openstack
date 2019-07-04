#!/bin/bash

keystone-manage --config-file /etc/keystone/keystone.conf fernet_rotate --keystone-user keystone --keystone-group keystone

