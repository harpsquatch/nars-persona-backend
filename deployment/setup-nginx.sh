#!/bin/bash
# Copy Nginx configuration
sudo cp deployment/nginx/nars-persona.conf /etc/nginx/sites-available/nars-persona

# Create symlink
sudo ln -sf /etc/nginx/sites-available/nars-persona /etc/nginx/sites-enabled/

# Remove default config if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
