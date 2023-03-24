#download and verify binaries
FROM alpine:latest as verified
RUN apk add gnupg wget curl bash tar

ENV JONALDKEY2=https://raw.githubusercontent.com/fyookball/keys-n-hashes/master/pubkeys/jonaldkey2.txt 
ENV SOMBERNIGHT=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/sombernight_releasekey.asc 
ENV THOMASV=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/ThomasV.asc 
ENV EMZY=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/Emzy.asc 
ENV VER_ELECTRUM=4.3.4 
ENV VER_ELECTRON=4.2.14 
ENV URL_ELECTRUM=https://download.electrum.org/${VER_ELECTRUM}/electrum-${VER_ELECTRUM}-x86_64.AppImage 
ENV URL_ELECTRON=https://github.com/Electron-Cash/Electron-Cash/releases/download/${VER_ELECTRON}/Electron-Cash-${VER_ELECTRON}-x86_64.AppImage 
ENV SIG_ELECTRUM=https://download.electrum.org/${VER_ELECTRUM}/electrum-${VER_ELECTRUM}-x86_64.AppImage.asc
ENV SIG_ELECTRON=https://raw.githubusercontent.com/Electron-Cash/keys-n-hashes/master/sigs-and-sums/${VER_ELECTRON}/win-linux/Electron-Cash-${VER_ELECTRON}-x86_64.AppImage.asc
ENV VER_WOWNERO=0.11
ENV URL_WOWNERO=https://git.wownero.com/attachments/86864223-7335-473e-a401-ab9da7f3188f
ENV HASH_WOWNERO=dbbe79f2cf13f822b19a17d4711f177abb9feb1182141b7126d1a7d8efacfaa5
ENV VER_MONERO=0.18.2.0
ENV HASH_MONERO=83e6517dc9e5198228ee5af50f4bbccdb226fe69ff8dd54404dddb90a70b7322
ENV URL_MONERO=https://downloads.getmonero.org/cli/linux64



RUN gpg --import <(curl ${JONALDKEY2} ) \
&& gpg --import <(curl ${SOMBERNIGHT} ) \
&& gpg --import <(curl ${EMZY} ) \ 
&& gpg --import <(curl ${THOMASV})

WORKDIR /wallets

RUN wget -O run_electrum.asc ${SIG_ELECTRUM} \ 
&&  wget -O electron-cash.asc ${SIG_ELECTRON} \
&&  wget -O run_electrum ${URL_ELECTRUM} \
&&  wget -O electron-cash ${URL_ELECTRON} \ 
&&  wget -O wownero-x86_64-linux-gnu-v${VER_WOWNERO}.tar.bz2 ${URL_WOWNERO} \ 
&&  wget -O monero-linux-x64-v${VER_MONERO}.tar.bz2 ${URL_MONERO}

#if any of these checks fail, the image will not be built
RUN gpg --status-fd=1 --verify electron-cash.asc 2>/dev/null | grep "GOODSIG 4FD06489EFF1DDE1 Jonald Fyookball <jonf@electroncash.org>" || exit 1
RUN gpg --status-fd=1 --verify run_electrum.asc 2>/dev/null | grep "GOODSIG 2BD5824B7F9470E6 Thomas Voegtlin (https://electrum.org) <thomasv@electrum.org>" || exit 1
RUN gpg --status-fd=1 --verify run_electrum.asc 2>/dev/null | grep "GOODSIG CA9EEEC43DF911DC SomberNight/ghost43 (Electrum RELEASE signing key) <somber.night@protonmail.com>" || exit 1
RUN gpg --status-fd=1 --verify run_electrum.asc 2>/dev/null | grep "GOODSIG 3152347D07DA627C Stephan Oeste (it) <it@oeste.de>" || exit 1
#verify wownero hash
RUN [ "${HASH_WOWNERO}  wownero-x86_64-linux-gnu-v${VER_WOWNERO}.tar.bz2" = "$(sha256sum  wownero-x86_64-linux-gnu-v${VER_WOWNERO}.tar.bz2)" ]
#verify monero hash
RUN [ "${HASH_MONERO}  monero-linux-x64-v${VER_MONERO}.tar.bz2" = "$(sha256sum  monero-linux-x64-v${VER_MONERO}.tar.bz2)" ]

RUN tar -xvjf wownero-x86_64-linux-gnu-v${VER_WOWNERO}.tar.bz2 wownero-x86_64-linux-gnu-v${VER_WOWNERO}/wownero-wallet-rpc && \
cp wownero-x86_64-linux-gnu-v${VER_WOWNERO}/wownero-wallet-rpc wownero-wallet-rpc

RUN tar -xvjf  monero-linux-x64-v${VER_MONERO}.tar.bz2 monero-x86_64-linux-gnu-v${VER_MONERO}/monero-wallet-rpc && \
cp monero-x86_64-linux-gnu-v${VER_MONERO}/monero-wallet-rpc monero-wallet-rpc && \
rm *bz2 && rm -r *v0*

FROM python:3.8-slim as dependencies

COPY ./app/requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.8-slim

#app images require fuse to function



#get the verified binaries , and copy to the apps bin folder
COPY --from=verified /wallets/ /home/app/bin/
#copy wishlist files to the docker
COPY ./app /home/app

#default port of uvicorn is 8000 - nginx will proxy pass to this
EXPOSE 8000

WORKDIR /home/app/bin
RUN chmod +x run_electrum \ 
    && chmod +x electron-cash \
    && apt-get update \ 
    && apt-get install -y --no-install-recommends fuse \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove 

COPY --from=dependencies /root/.local /root/.local
# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

WORKDIR /home/app
#main.py starts the /donate webpage/server
CMD ["python3", "./main.py"]
#users must then shell into the container and run the 'setup_wallets.py'
#sudo docker volume rm $(sudo docker volume ls -q)
#certbot certonly --standalone -d <domaim> --staple-ocsp -m <email> --agree-tos
