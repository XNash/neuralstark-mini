#!/bin/bash
# Patch webpack-dev-server to suppress deprecation warnings
# This script patches the webpack-dev-server warnings that come from react-scripts 5.0.1

WEBPACKDEVSERVER_PATH="/app/frontend/node_modules/webpack-dev-server/lib/Server.js"

if [ -f "$WEBPACKDEVSERVER_PATH" ]; then
    # Create backup if it doesn't exist
    if [ ! -f "$WEBPACKDEVSERVER_PATH.backup" ]; then
        cp "$WEBPACKDEVSERVER_PATH" "$WEBPACKDEVSERVER_PATH.backup"
    fi
    
    # Suppress the deprecation warnings by adding process.removeAllListeners at the start
    sed -i '1i\
// Suppress deprecation warnings for onBeforeSetupMiddleware and onAfterSetupMiddleware\
process.removeAllListeners("warning");' "$WEBPACKDEVSERVER_PATH"
    
    echo "✓ Patched webpack-dev-server to suppress deprecation warnings"
else
    echo "⚠ webpack-dev-server not found at $WEBPACKDEVSERVER_PATH"
fi
