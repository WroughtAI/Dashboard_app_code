#!/bin/bash

# Set default git configuration
git config --global user.name "mutabletao"
git config --global user.email "jim@barnebee.com"

# Function to create a new repo in WroughtAI organization
create_wrought_repo() {
  REPO_NAME=$1
  DESCRIPTION=$2
  PRIVATE=${3:-true}  # Default to private repo
  
  echo "Creating repository $REPO_NAME in WroughtAI organization..."
  gh repo create WroughtAI/$REPO_NAME --description "$DESCRIPTION" --${PRIVATE} --clone
  
  if [ $? -eq 0 ]; then
    echo "Repository created successfully!"
    echo "Clone URL: https://github.com/WroughtAI/$REPO_NAME.git"
    cd $REPO_NAME
  else
    echo "Failed to create repository."
  fi
}

# Function to push existing repo to WroughtAI organization
push_to_wrought() {
  REPO_NAME=$(basename $(pwd))
  
  echo "Setting up remote for $REPO_NAME in WroughtAI organization..."
  git remote remove origin 2>/dev/null
  git remote add origin https://github.com/WroughtAI/$REPO_NAME.git
  
  echo "Remote set to: https://github.com/WroughtAI/$REPO_NAME.git"
  echo "Use 'git push -u origin main' to push your code"
}

# Instructions
echo "WroughtAI GitHub Configuration"
echo "------------------------------"
echo "To create a new WroughtAI repository:"
echo "  source set_wrought_ai_default.sh"
echo "  create_wrought_repo repo-name \"Description of repo\" [true|false for private]"
echo ""
echo "To push an existing repository to WroughtAI:"
echo "  source set_wrought_ai_default.sh"
echo "  push_to_wrought"
echo "  git push -u origin main" 