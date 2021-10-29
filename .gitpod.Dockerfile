FROM gitpod/workspace-full

USER gitpod

RUN sudo apt-get update && \
pyenv install 3.9.7