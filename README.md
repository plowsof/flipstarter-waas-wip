Docker repo/instructions here https://hub.docker.com/r/plowsof/waas4rucknium-testnet   

Currently, this will just create a mirror of the page @ rucknium.me/flask, however, i will eventually be making a generic version, and use the rucknium page as an example of installing a template (just copy and pasting a folder) 

### TODO
- [x] Fix Negative bitcoin donations :) 
- [x] non-js version incorrect and donations should trigger an update 
- fix bugs in
    - [x] install wizard
    - [ ] edit wishlist 
- [ ] sanity checks

also todo ~ make a tutorial based on these notes

hello, lets pretend my name is George, i have a domain called getwishlisted.xyz and i want to run this wishlist on it. I need nginx/docker-compose/docker and the docker-compose.yml file. For testing locally, i dont need nginx or ssl certs, i can just go to http://172.20.111.2:8000/donate after running ```sudo docker-compose up``` in the same directory as the ```docker-compose.yml``` file above.

Local testing on a Mac? You'll need Docker Desktop https://docs.docker.com/desktop/mac/install/    

Linux/Ubuntu? I prefer to use snapd to install docker and docker-compose
```
sudo apt-get install snapd
sudo snap install docker
```
```
curl https://raw.githubusercontent.com/plowsof/flipstarter-waas-wip/main/docker-compose.yml -o docker-compose.yml
```
```
sudo docker-compose up -d
```
```
cd /etc/nginx/sites-available
nano getwishlisted.xyz
```

Take note of the 'https' - if you're not using ssl certs, set it to http else you can't see the page afaik
```
server {
    listen 80;
    listen [::]:80;
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    server_name moneroresearch.info www.moneroresearch.info;
        location /donate {
          proxy_pass https://172.20.111.2:8000;
        }
}
```
```
sudo ln -s /etc/nginx/sites-available/getwishlisted.xyz /etc/nginx/sites-enabled/ 

sudo /etc/init.d/nginx restart
```
lets get certs:
```
apt install snapd
snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```
I had an error 'to many redirects' because my dns providers ssl setting was off, i needed to change it to 'Full'    

Successfully received certificate.    
Certificate is saved at: /etc/letsencrypt/live/www.getwishlisted.xyz/fullchain.pem    
Key is saved at:         /etc/letsencrypt/live/www.getwishlisted.xyz/privkey.pem    

cd to the ssl folder next to your docker-compose.yml file (maybe a needless step to create this folder)    
```
cp /etc/letsencrypt/live/www.getwishlisted.xyz/* .    

docker stop fresh     
docker-compose up    
docker exec -it fresh /bin/bash    
python3 make_wishlist.py    
```
when finished press ctrl+p then ctrl+q to detatch from the docker container    

### Support
The initial funding for this project was obtained through Bitcoin-cash' crowdfunding system - FlipStarter.    
I will not be asking for any donations for this particular projects further development until someone using this WaaS receives their first (mainnet)     donation / and i have fulfilled my FlipStarter promises. I think thats fair right? :)    
