#get monero-rpc from a trusted source (i could also download and verify..)
FROM sethsimmons/simple-monero-wallet-rpc as build

#download and verify binaries
FROM alpine:latest as verified
RUN apk add gnupg wget curl bash

ENV JONALDKEY2=https://raw.githubusercontent.com/fyookball/keys-n-hashes/master/pubkeys/jonaldkey2.txt 
ENV SOMBERNIGHT=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/sombernight_releasekey.asc 
ENV THOMASV=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/ThomasV.asc 
ENV EMZY=https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/Emzy.asc 
ENV VER_ELECTRUM=4.1.5 
ENV VER_ELECTRON=4.2.7 
ENV URL_ELECTRUM=https://download.electrum.org/${VER_ELECTRUM}/electrum-${VER_ELECTRUM}-x86_64.AppImage 
ENV URL_ELECTRON=https://github.com/Electron-Cash/Electron-Cash/releases/download/${VER_ELECTRON}/Electron-Cash-${VER_ELECTRON}-x86_64.AppImage 
ENV SIG_ELECTRUM=https://download.electrum.org/${VER_ELECTRUM}/electrum-${VER_ELECTRUM}-x86_64.AppImage.asc
ENV SIG_ELECTRON=https://raw.githubusercontent.com/Electron-Cash/keys-n-hashes/master/sigs-and-sums/${VER_ELECTRON}/win-linux/Electron-Cash-${VER_ELECTRON}-x86_64.AppImage.asc 


RUN gpg --import <(curl ${JONALDKEY2} ) \
&& gpg --import <(curl ${SOMBERNIGHT} ) \
&& gpg --import <(curl ${EMZY} ) \ 
&& gpg --import <(curl ${THOMASV})

WORKDIR /wallets

RUN wget -O run_electrum.asc ${SIG_ELECTRUM} \ 
&&  wget -O electron-cash.asc ${SIG_ELECTRON} \
&&  wget -O run_electrum ${URL_ELECTRUM} \
&&  wget -O electron-cash ${URL_ELECTRON}

#if any of these checks fail, the image will not be built
RUN gpg --status-fd=1 --verify electron-cash.asc 2>/dev/null | grep "GOODSIG 4FD06489EFF1DDE1 Jonald Fyookball <jonf@electroncash.org>" || exit 1
RUN gpg --status-fd=1 --verify run_electrum.asc 2>/dev/null | grep "GOODSIG 2BD5824B7F9470E6 Thomas Voegtlin (https://electrum.org) <thomasv@electrum.org>" || exit 1
RUN gpg --status-fd=1 --verify run_electrum.asc 2>/dev/null | grep "GOODSIG CA9EEEC43DF911DC SomberNight/ghost43 (Electrum RELEASE signing key) <somber.night@protonmail.com>" || exit 1
RUN gpg --status-fd=1 --verify run_electrum.asc 2>/dev/null | grep "GOODSIG 3152347D07DA627C Stephan Oeste (it) <it@oeste.de>" || exit 1


FROM python:3.8-slim as dependencies

COPY ./app/requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.8-slim

#app images require fuse to function



#get the rpc binary from seths docker image
COPY --from=build /usr/local/bin/monero-wallet-rpc /home/app/bin/monero-wallet-rpc
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
#users must then shell into the container and run the 'make_wishlist.py'
#sudo docker volume rm $(sudo docker volume ls -q)
#certbot certonly --standalone -d <domaim> --staple-ocsp -m <email> --agree-tos