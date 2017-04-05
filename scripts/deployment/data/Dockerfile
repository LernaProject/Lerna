FROM python:3.5

# 1. Moving entry script to the image and setting it as an entry point.
COPY docker_run.sh /
CMD ["/docker_run.sh"]

# 2. Preparing directory for Lerna sources.
# 3. Updating available packages.
# 4. Installing nginx and Supervisor.
# 5. Cleaning package lists.
# 6. Installing Pandoc.
# 7. Setting up nginx.
RUN set -ux                                    && \
    readonly PANDOC_VERSION=1.19.2.1           && \
    mkdir /lerna                               && \
    apt-get update                             && \
    apt-get install -y nginx supervisor        && \
    apt-get clean                              && \
    curl -fSLO https://github.com/jgm/pandoc/releases/download/$PANDOC_VERSION/pandoc-$PANDOC_VERSION-1-amd64.deb && \
    dpkg -i pandoc-$PANDOC_VERSION-1-amd64.deb && \
    echo 'daemon off;' >>/etc/nginx/nginx.conf && \
    rm -f pandoc-$PANDOC_VERSION-1-amd64.deb /etc/nginx/sites-enabled/* /etc/nginx/sites-available/*

COPY lerna.nginx /etc/nginx/sites-enabled/

# 8. Setting up Supervisor.
COPY supervisord.conf /etc/supervisor/conf.d/

# 9. Installing pip requirements.
# 10. Installing gUnicorn.
# 11. Installing a Pandoc extension.
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
