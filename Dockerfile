# Stage 1: Download and verify binaries
FROM ubuntu:22.04 AS verified

# Install necessary tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg wget curl bash tar ca-certificates bzip2 && \
    rm -rf /var/lib/apt/lists/*

# Define environment variables
ENV JONALDKEY=https://raw.githubusercontent.com/fyookball/keys-n-hashes/master/pubkeys/jonaldkey.txt \
    JONALDKEY2=https://raw.githubusercontent.com/fyookball/keys-n-hashes/master/pubkeys/jonaldkey2.txt \
    SOMBERNIGHT=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/sombernight_releasekey.asc \
    THOMASV=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/ThomasV.asc \
    EMZY=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/Emzy.asc \
    VER_ELECTRUM=4.5.8 \
    VER_ELECTRON=4.4.1 \
    URL_ELECTRUM=https://download.electrum.org/4.5.8/electrum-4.5.8-x86_64.AppImage \
    URL_ELECTRON=https://github.com/Electron-Cash/Electron-Cash/releases/download/4.4.1/Electron-Cash-4.4.1-x86_64.AppImage \
    SIG_ELECTRUM=https://download.electrum.org/4.5.8/electrum-4.5.8-x86_64.AppImage.asc \
    SIG_ELECTRON=https://raw.githubusercontent.com/Electron-Cash/keys-n-hashes/refs/heads/master/sigs-and-sums/4.4.1/win-linux/Electron-Cash-4.4.1-x86_64.AppImage.asc \
    VER_WOWNERO=0.11.1.0 \
    URL_WOWNERO=https://git.wownero.com/attachments/280753b0-3af0-4a78-a248-8b925e8f4593 \
    HASH_WOWNERO=a5b2aa0cffa4c7bf82d9d6072aca0bdeb501bdbde33db1d04edb2c4089878e82 \
    VER_MONERO=0.18.3.4 \
    HASH_MONERO=51ba03928d189c1c11b5379cab17dd9ae8d2230056dc05c872d0f8dba4a87f1d \
    URL_MONERO=https://downloads.getmonero.org/cli/monero-linux-x64-v0.18.3.4.tar.bz2

WORKDIR /wallets

# Import GPG keys
RUN curl -sSL $SOMBERNIGHT | gpg --import && \
    curl -sSL $EMZY | gpg --import && \
    curl -sSL $THOMASV | gpg --import && \
    curl -sSL $JONALDKEY2 | gpg --import

# Download files
RUN wget -O run_electrum.asc $SIG_ELECTRUM && \
    wget -O electron-cash.asc $SIG_ELECTRON && \
    wget -O run_electrum $URL_ELECTRUM && \
    wget -O electron-cash $URL_ELECTRON && \
    wget -O wownero.tar.bz2 $URL_WOWNERO && \
    wget -O monero.tar.bz2 $URL_MONERO

# Verify signatures
RUN gpg --verify electron-cash.asc electron-cash && \
    gpg --verify run_electrum.asc run_electrum

# Verify hashes
RUN echo "${HASH_WOWNERO}  wownero.tar.bz2" | sha256sum -c - && \
    echo "${HASH_MONERO}  monero.tar.bz2" | sha256sum -c -

# Extract necessary files
RUN tar -xvjf wownero.tar.bz2 && \
    tar -xvjf monero.tar.bz2 && \
    cp wownero*/wownero-wallet-rpc . && \
    cp monero*/monero-wallet-rpc . && \
    rm *.tar.bz2

# Stage 2: Dependencies
FROM python:3.8-slim AS dependencies
COPY ./app/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 3: Final application image
FROM python:3.8-slim

# Install FUSE
RUN apt-get update && apt-get install -y --no-install-recommends fuse && \
    rm -rf /var/lib/apt/lists/*

# Copy verified binaries
COPY --from=verified /wallets/ /home/app/bin/

# Copy dependencies
COPY --from=dependencies /root/.local /root/.local

# Copy application code
COPY ./app /home/app

WORKDIR /home/app/bin

# Ensure binaries are executable
RUN chmod +x run_electrum electron-cash

# Set PATH for dependencies
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

WORKDIR /home/app
CMD ["python3", "./main.py"]
