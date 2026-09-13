FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server sudo procps net-tools iproute2 curl \
        vim-tiny less psmisc lsof \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash referencia \
    && usermod -aG sudo referencia
RUN echo 'referencia:referencia' | chpasswd

RUN mkdir -p /home/referencia/projetos /home/referencia/backups \
    && echo 'dados de exemplo' > /home/referencia/projetos/notas.txt \
    && echo '#!/bin/bash' > /home/referencia/backups/rotina.sh

RUN mkdir -p /run/sshd \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D", "-e"]
