# Run S-NDR in a Docker Instance

## Install Docker

Install Docker and run the Daemon. See
https://docs.docker.com/install/linux/docker-ce/ubuntu/ for
installation details.

    $ sudo service docker start

## Pull the Docker instance

Pull the Docker Instance from Dockerhub

    $ docker pull docker.io/wd15/s-ndr

## Run PFHub

Run the container

    $ docker run -i -t -p 4000:4000 wd15/s-ndr:latest

and then

    # nix-shell
    # jupyter notebook

## Build the Docker instance

Clone this repository and run

    $ docker build -t wd15/s-ndr:latest .

## Push the Docker instance

Create the repository in Dockerhub and then push it.

    $ docker login
    $ docker push docker.io/wd15/s-ndr
