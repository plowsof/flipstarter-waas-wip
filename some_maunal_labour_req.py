import os
url = "p2pcrowd.fund"
HOME = "https://www.github.com/monero-project"
title = "SomeOTherz"
pagename = title.lower()
intro = "Hello everyone this is montero mcdonalds page"
ip = "172.28.0.2"
#INDEX LIST INFO
index_desc = "a fake person to test the functionality"

port = 8000

newbranch = [ 
           "cd flipstarter-waas-wip",
           f"git branch {pagename}",
           f"git checkout {pagename}",
           "git reset main --hard"
            ]

string = ""
for c in newbranch:
    c += ";"
    string += c

os.system(string)

changeme = [ "flipstarter-waas-wip/app/static/template_index.html", 
            "flipstarter-waas-wip/app/static/static_html_loop.py",
            "flipstarter-waas-wip/app/static/index.html",
            "flipstarter-waas-wip/app/rss_feed.py",
            "flipstarter-waas-wip/app/main.py",
            "flipstarter-waas-wip/app/static/index.html",
            "flipstarter-waas-wip/app/static/js/appv4.js"
            ]

for f in changeme:
    with open(f,"r") as w:
        inf = w.read()
    with open(f,"w") as w:
        w.write(inf.replace("/donate",f"/{pagename}").replace("port=8000",f"port={port}").replace('href="../">Home',f'href="{HOME}">Home').replace('<body class=dark id=top>','<body class=dark id=top><nav><a href="/">p2pcrowd.fund</a></nav>'))

#edit index
with open("/var/www/html/index.html", 'r') as f:
    lines = f.readlines()
with open("/var/www/html/index.html", 'w') as f:
    for line in lines:
        if "</ul>" in line:
            f.write(f'<li><a href="/{pagename}">{title}</a> - {index_desc}</li>\n')
        f.write(line)
os.system(f"docker build ./flipstarter-waas-wip -t {pagename}")


compose = f"""version: '3.3'
services:
  waas:
    image: {pagename}
    restart: on-failure
    container_name: {pagename}_c
    volumes:
      - waas-db{port}:/home/app/db
      - waas-wallets{port}:/home/app/wallets
      - waas-static{port}:/home/app/static
      - /proc:/writable_proc
    networks:
      poordevs:
          ipv4_address: {ip}
    expose:
      - {port}
    cap_add:
      - SYS_ADMIN
    devices:
      - /dev/fuse
    security_opt:
      - apparmor:unconfined
    environment:
      - waas_RSS_ON=1
      - waas_TITLE="{title}"
      - waas_INTRO="{intro}"
      - waas_RSS_TITLE="Crypto-Funding Page"
      - waas_RSS_DESC="Help support my projects and running costs"
      - waas_RSS_LINK="https://{url}/{pagename}" 
      - waas_remote_node_1="nodex.monerujo.io:18081"
      - waas_remote_node_2="node.sethforprivacy.com:18089"
      - waas_remote_node_3="xmr-node-usa-east.cakewallet.com:18081"
      - waas_remote_node_4="electroncash.dk:18089"
      - waas_remote_node_5="node.community.rino.io:18081"
      - waas_remote_node_6="selsta2.featherwallet.net:18081" 
      - waas_remote_node_7="selsta1.featherwallet.net:18081"
      - waas_wow_remote_node_1="node.monerodevs.org:34568"
      - waas_wow_remote_node_2="nodes.hashvault.pro:34568"
      - waas_wow_remote_node_3="eu-west-1.wow.xmr.pm:34568"
      - waas_wow_remote_node_4="wownero.fyi:34568"
      - waas_wow_remote_node_5="nimiq.wangyp.eu.org:34568"
      - waas_mainnet=1
volumes:
  waas-db{port}:
  waas-wallets{port}:
  waas-static{port}:
networks:
  poordevs:
     name: poors
     external: true
"""
if not os.path.exists(f"./{pagename}"):
    os.mkdir(f"./{pagename}")
with open(f"{pagename}/docker-compose.yml","w+") as f:
    f.write(compose)


nginx = f"""
location /{pagename} {{
  proxy_pass http://{ip}:{port};
}}
location /{pagename}/ws {{
proxy_pass http://{ip}:{port};
proxy_http_version 1.1;
proxy_ssl_certificate /etc/letsencrypt/live/{url}/fullchain.pem;
proxy_ssl_certificate_key /etc/letsencrypt/live/{url}/privkey.pem;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "Upgrade";
proxy_set_header Host $host;
}}
"""
with open(f"/etc/nginx/sites-available/{url}","r") as f:
    lines = f.readlines()
with open(f"/etc/nginx/sites-available/{url}","w") as f:
    listenfound = 0
    for line in lines:
        if "listen" in line:
            if listenfound != 1:
                listenfound = 1
                f.write(nginx)
                f.write(line)
            else:
                f.write(line)
        else:
            f.write(line)

cmdlist = [
           "cd flipstarter-waas-wip",
           f"docker build . -t {pagename}",
           "/etc/init.d/nginx restart",
           f"cd ../{pagename}/",
           f"ufw allow {port}",
           "docker-compose up -d",
           f"docker exec -it {pagename}_c /bin/bash"
          ]

string = ""
for c in cmdlist:
    c += ";"
    string += c

os.system(string)
