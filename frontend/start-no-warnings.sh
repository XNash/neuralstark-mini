#!/bin/bash
# Suppress deprecation warnings from webpack-dev-server
export NODE_OPTIONS="--no-deprecation"
exec yarn start
