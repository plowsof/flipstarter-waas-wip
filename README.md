Docker repo/instructions here https://hub.docker.com/r/plowsof/waas4rucknium-testnet   

Currently, this will just create a mirror of the page @ rucknium.me/flask, however, i will eventually be making a generic version, and use the rucknium page as an example of installing a template (just copy and pasting a folder) 

### TODO
- [x] Fix Negative bitcoin donations :) 
- [ ] non-js version incorrect and donations should trigger an update 
- fix bugs in
    - [x] install wizard
    - [ ] edit wishlist 
- [ ] sanity checks

also todo ~ make a tutorial based on these notes
```
hello, lets pretend my name is George, i have a domain called getwishlisted.xyz and i want to run this wishlist on it. I need nginx/dockercompose/docker and the docker-compose.yml file  

dockercompose 
https://docs.docker.com/compose/install/
docker
https://docs.docker.com/engine/install/debian/

curl https://raw.githubusercontent.com/plowsof/flipstarter-waas-wip/main/docker-compose.yml -o docker-compose.yml

docker-compose up -d


cd /etc/nginx/sites-available
nano getwishlisted.xyz

server {
    listen 80;
    listen [::]:80;
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    server_name moneroresearch.info www.moneroresearch.info;
        location /flask {
          proxy_pass http://172.20.111.2:8000;
        }
}

sudo ln -s /etc/nginx/sites-available/getwishlisted.xyz /etc/nginx/sites-enabled/ 

sudo /etc/init.d/nginx restart

lets get certs:

apt install snapd
snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

I had an error 'to many redirects' because my dns providers ssl setting was off, i needed to change it to 'Full'

Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/www.getwishlisted.xyz/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/www.getwishlisted.xyz/privkey.pem

cd to the ssl folder next to your docker-compose.yml file (maybe a needless step to create this folder)
cp /etc/letsencrypt/live/www.getwishlisted.xyz/* .

docker stop fresh
docker-compose up
docker exec -it fresh /bin/bash
python3 make_wishlist.py

when finished press ctrl+p then ctrl+q to detatch from the docker container
```
### Support
The initial funding for this project was obtained through Bitcoin-cash' crowdfunding system - FlipStarter.
I will not be asking for any donations for this particular projects further development until someone using this WaaS receives their first (mainnet) donation / and i have fulfilled my FlipStarter promises. I think thats fair right? :) 
