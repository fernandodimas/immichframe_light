#!/bin/bash

echo "Building immichframe-light image..."
docker build -t immichframe-light:latest .

echo "Saving image to tar file..."
docker save immichframe-light:latest -o immichframe-light.tar

echo "Done! File created: immichframe-light.tar"
echo ""
echo "To load this image on your Portainer server:"
echo "  1. Transfer immichframe-light.tar to your server"
echo "  2. Run: docker load -i immichframe-light.tar"
echo "  3. Then deploy the stack in Portainer"
