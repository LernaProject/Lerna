FROM python:3.5

ARG MAIL_DOMAIN=

# 1. Moving entry script to the image and setting it as an entry point.
COPY docker_run.sh /
CMD ["/docker_run.sh"]

# 2. Preparing directory for Lerna sources.
# 3. Updating available packages.
# 4. (Optional) Installing and configuring Postfix.
# 5. Installing nginx and Supervisor.
# 6. Cleaning package lists.
# 7. Installing Pandoc.
# 8. Setting up nginx.
RUN set -ux                                    && \
    readonly PANDOC_VERSION=1.19.2.1           && \
    mkdir /lerna                               && \
    apt-get update                             && \
    if [ -n "${MAIL_DOMAIN:-}" ]; then            \
        {                                         \
            echo "postfix postfix/mailname string $MAIL_DOMAIN";            \
            echo "postfix postfix/main_mailer_type string 'Internet Site'"; \
        } | debconf-set-selections             && \
        apt-get install -y postfix             && \
        sed -i 's/inet_interfaces = all/inet_interfaces = loopback-only/' /etc/postfix/main.cf && \
        sed -i 's!myorigin = /etc/mailname!myorigin = </etc/mailname!'    /etc/postfix/main.cf;   \
    fi                                         && \
    apt-get install -y nginx supervisor        && \
    apt-get clean                              && \
    curl -fSLO https://github.com/jgm/pandoc/releases/download/$PANDOC_VERSION/pandoc-$PANDOC_VERSION-1-amd64.deb && \
    dpkg -i pandoc-$PANDOC_VERSION-1-amd64.deb && \
    echo 'daemon off;' >>/etc/nginx/nginx.conf && \
    rm -f pandoc-$PANDOC_VERSION-1-amd64.deb /etc/nginx/sites-enabled/* /etc/nginx/sites-available/*

COPY lerna.nginx /etc/nginx/sites-enabled/

# 9. Setting up Supervisor.
COPY supervisord.conf /etc/supervisor/conf.d/

# 10. Installing pip requirements.
# 11. Installing gUnicorn.
# 12. Installing a Pandoc extension.
COPY requirements.txt.tmp /
RUN set -ux                                                       && \
    pip3 install --no-cache-dir --upgrade -r requirements.txt.tmp && \
    pip3 install --no-cache-dir gunicorn                          && \
    cd /tmp                                                       && \
    git clone git://github.com/SirNickolas/pandoc-anglequotes     && \
    cd pandoc-anglequotes                                         && \
    pip install --no-cache-dir --upgrade -r requirements.txt      && \
    make install-python                                           && \
    cd /                                                          && \
    rm -rf /tmp/pandoc-anglequotes /requirements.txt.tmp
