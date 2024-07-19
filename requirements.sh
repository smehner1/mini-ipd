#!/bin/bash

# Function to check if the package is installed and add it to the list if not
check_and_add_package() {
    local package_name=$1
    if ! dpkg -l | grep -qw "$package_name"; then
        missing_packages+=("$package_name")
    fi
}

# Function to determine the OS and print a statement if it's not Debian or Ubuntu
check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
            echo "This script is intended for Debian or Ubuntu systems only."
            exit 1
        fi
    else
        echo "Cannot determine the operating system."
        exit 1
    fi
}

# Initialize an empty array to hold missing packages
missing_packages=()

# Check the OS
check_os

# Check for required packages
check_and_add_package "docker.io"
check_and_add_package "python3"
check_and_add_package "openvswitch-switch"
check_and_add_package "screen"

# Output the list of missing packages
if [ ${#missing_packages[@]} -eq 0 ]; then
    echo "All required packages are already installed."
else
    echo "The following packages are required and not installed:"
    for package in "${missing_packages[@]}"; do
        echo "$package"
    done
    echo "To install them, use the following command:"
    echo "sudo apt update && sudo apt install -y ${missing_packages[*]}"
fi

