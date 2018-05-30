From ubuntu:17.10

MAINTAINER Daniel Wheeler <daniel.wheeler2@gmail.com>

ENV DEBIAN_FRONTEND noninteractive

USER root

RUN apt-get -y update
RUN apt-get install -y apt-utils && apt-get clean
RUN apt-get install -y sudo && apt-get clean
RUN apt-get install -y bzip2 && apt-get clean
RUN apt-get install -y curl && apt-get clean
RUN apt-get -y update

ENV NB_USER jovyan
ENV NB_UID 1000
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}

# RUN adduser --disabled-password --gecos "Default user" --uid 1000 main
# RUN echo "${NB_USER}:${NB_USER}" | chpasswd
# RUN adduser ${NB_USER} sudo

EXPOSE 8888

USER ${NB_USER}

ENV SHELL /bin/bash
ENV USER ${NB_USER}
WORKDIR $HOME

USER root

# RUN chown -R ${NB_USER}:${NB_USER} $HOME
# RUN echo "${NB_USER} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN mkdir /etc/nix
RUN echo "build-users-group =" > /etc/nix/nix.conf
RUN mkdir /nix
RUN chown -R ${NB_USER}:${NB_USER} /nix

USER ${NB_USER}


## Install Nix

RUN curl https://nixos.org/nix/install > ./install.sh
RUN bash ./install.sh
RUN cp ~/.nix-profile/etc/profile.d/nix.sh ~/nix.sh
RUN chmod +wx ~/nix.sh
RUN /bin/bash -c "echo -e 'unset PATH\n$(cat ~/nix.sh)' > ~/nix.sh"
RUN echo "export PATH=\$PATH:/nix/var/nix/profiles/default/bin:/bin:/usr/bin" >> ~/nix.sh
RUN echo "export NIX_USER_PROFILE_DIR=/nix/var/nix/profiles/per-user/\$USER " >> ~/nix.sh
RUN echo "export MANPATH=/nix/var/nix/profiles/default/share/man:\$HOME/.nix-profile/share/man:\$MANPATH" >> ~/nix.sh

## Copy directory

RUN /bin/bash -c " \
    source ~/nix.sh; \
    nix-env -i git; \
    git clone https://github.com/wd15/s-ndr.git; \
    cd s-ndr; \
    nix-shell"

COPY . $HOME
USER root
RUN chown -R 1000 ${HOME}
USER ${NB_USER}

RUN /bin/bash -c " \
    source ~/nix.sh; \
    nix-shell"

RUN echo "source ~/nix.sh" >> ~/.bashrc
EXPOSE 8888

CMD /bin/bash -c " \
    source ~/nix.sh; \
    nix-shell --command 'jupyter notebook --port 8888 --ip 0.0.0.0';"
