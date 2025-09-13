#!/bin/bash

echo "Installing dependencies for Sticky Notes Application..."

# Install npm dependencies
npm install

echo "Installation complete!"
echo ""
echo "To start the development server, run:"
echo "npm run dev"
echo ""
echo "Make sure you have an MQTT broker running on localhost:1883 for the monitoring features to work."