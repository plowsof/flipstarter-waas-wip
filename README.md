[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/plowsof/flipstarter-waas-wip/graphs/contributors)    
Currently, this will just create a mirror of the page @ rucknium.me/flask, however, i will eventually be making a generic version, and use the rucknium page as an example of installing a template (just copy and pasting a folder)    

Also ```ctrl+z``` and starting the script again is your friend if something goes wrong during ```make_wishlist.py``` e.g. wrongly select Restore from keys.   

### Production / On a VPS

Lets pretend my name is George, i have a domain called getwishlisted.xyz and i want to run this wishlist on it.


First things first, i need to install nginx on my Debian vps:
```
sudo apt-get install nginx
```
I need to go to the sites-available folder create a file the same name as my domain ```getwishlisted.xyz```
```
cd /etc/nginx/sites-available
nano getwishlisted.xyz
```
Nano is a text editor, it will create the file and allow me to begin editing it. I'll paste this inside:    
```
server {
    listen 80;
    listen [::]:80;
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    server_name getwishlisted.xyz www.getwishlisted.xyz;
        location /donate {
          proxy_pass http://172.20.111.2:8000;
        }
}
```
Then, i must press ```ctrl+x``` then press ```Y``` and ```ENTER``` to save the file.     
These next lines just create a mirrored copy of the file we created, and restarts the nginx web server. Why create a mirror you ask? i don't know but everyone else does it, so i assume its important (i'll search up on that later):    
```
sudo ln -s /etc/nginx/sites-available/getwishlisted.xyz /etc/nginx/sites-enabled/ 
sudo /etc/init.d/nginx restart
```

Lets get certs. Again, i find snap to be most helpful in this process. I use it to install ```certbot``` which is going to give us the SSL keys. It's basically going to create some files on our webserver to prove that we own it, and the certificate authority confirms this, then issues us our SSL certs.
```
apt install snapd
snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
``` 
```
sudo certbot
```
I ran ```sudo certbot``` a 2nd time for the ```www.``` url.    
After running through the setup / selecting nginx / agreeing to t&c's i see this output:
```
Successfully received certificate.    
Certificate is saved at: /etc/letsencrypt/live/www.getwishlisted.xyz/fullchain.pem    
Key is saved at:         /etc/letsencrypt/live/www.getwishlisted.xyz/privkey.pem    
```
For the websockets to allow your donation page to update in real time you must now manually edit your websites file.   
So Goerge now has to open up his 'getwishlisted.xyz' file in sites-enabled with a text editor e.g. nano and paste this under the original /dnonate location block:   
```
location /donate/ws {
    proxy_pass http://172.20.111.2:8000;
    proxy_http_version 1.1;
    proxy_ssl_certificate /etc/letsencrypt/live/www.getwishlisted.xyz/fullchain.pem;
    proxy_ssl_certificate_key /etc/letsencrypt/live/www.getwishlisted.xyz/privkey.pem;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;
}
```
At this point we need to ```cd``` to our ```/home``` folder and download the docker-compose file:
```
curl https://raw.githubusercontent.com/plowsof/flipstarter-waas-wip/mainnet/docker-compose.yml -o docker-compose.yml
```
Perfect. Now lets install docker and docker-compose with these handy install scripts:
```
 curl -fsSL https://test.docker.com -o test-docker.sh
 sudo sh test-docker.sh

```
now to install docker-compose:
```
 sudo curl -L --fail https://github.com/docker/compose/releases/download/1.29.2/run.sh -o /usr/local/bin/docker-compose
 sudo chmod +x /usr/local/bin/docker-compose
```
I can now start the wishlist the same way as i did locally: (in the same dir as ```docker-compose.yml``` not in the ssl folder    
Dont forget to go back to the same dir as your docker-compose file using ```cd..``` then:
```
sudo docker-compose up -d
```
And get on the terminal inside it using:
```
sudo docker exec -it fresh /bin/bash
```
from here (you will already be in /home/app) you can run ```make_wishlist.py``` using:
```
python3 make_wishlist.py
```
You can choose to paste your viewkeys or have wallets created for you (Write the seed words down though! else your money is gone forever)    
when finished press ctrl+p then ctrl+q to detatch from the docker container     

### Editing wishes
```edit_wishlist.py``` will allow you to:    
- add / delete wishes
- edit values / titles / descriptions
- add a custom status e.g. WIP / RELEASED 
- add a recurring montlhy payment e.g. -$100 USD each month
To access it, just terminal into the container as before and run:   
```
python3 edit_wishlist.py
```
Then follow the instructions      

### Wallets / Seeing Donations
WaaS is based on these 3 wallets:
- Monero GUI
- Electron-cash
- Electrum    
Some donations may not appear in your wallet because of something called a gap limit. In Electron-cash / Electrum to go view -> console. And paste this line:
```
for i in range(0, 100): print(wallet.create_new_address(False))
```
You should be able to see any missing donations then. Repeat it if needed.   
### Updating the front end using a template from [waas-templates](https://github.com/plowsof/waas-templates)
Follow the instructions in the github readme of waas-templates. The only issue you will have here is if your browser / domain provider is storing things in the cache. ```ctrl+f5``` will purge your local browser. See your domain providers instructions on how to purge its cache if you can't see updates.    
### Updating the backend
The container must be stopped, image removed, and then the docker-compose file ran again to get the new version: (in the same dir as docker-compose.yml) 
```
docker stop fresh && \
docker rmi plowsof/waas-rucknium:latest --force && \
docker-compose up -d
```
If you run into issues, it must not be running in ```docker ps``` list, and you can use ```--force``` after the remove commands.    
```docker images``` will give you an image id to use if all else fails ```docker image rm <imageid> --force```. do not delete the docker compose image!   
Ignore the error message when trying ```docker-compose up -d``` the wishlist data is safe.

Here is what my nginx.conf file (getwishlisted.xyz) looks like:
```
server {
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    server_name getwishlisted.xyz www.getwishlisted.xyz custom;
        location /donate {
            proxy_pass http://172.20.111.2:8000;
        }
        location /donate/ws {
            proxy_pass http://172.20.111.2:8000;
            proxy_http_version 1.1;
            proxy_ssl_certificate /etc/letsencrypt/live/www.getwishlisted.xyz/fullchain.pem;
            proxy_ssl_certificate_key /etc/letsencrypt/live/www.getwishlisted.xyz/privkey.pem;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
        }

    listen [::]:443 ssl ipv6only=on; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/www.getwishlisted.xyz/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/www.getwishlisted.xyz/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}
server {
    if ($host = www.getwishlisted.xyz) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    if ($host = getwishlisted.xyz) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    listen 80;
    listen [::]:80;
    server_name getwishlisted.xyz www.getwishlisted.xyz;
    return 404; # managed by Certbot
}

###Testing on stagenet/testnet
All 5 of the remote nodes in ```docker-compose.yml``` must be replaced with stagenet ones, and then set ```waas_mainnet=0```.    
Switching back and forth is a litte tricky as you have to delete the wishlist text file ```rm static/data/wishlist-data.json``` and run ```python3 make_wishlist.py``` again to create your wishlist/mainnet wallets.

```

### TODO
This is still in beta so i must do some sanity checks 
- [ ] sanity checks
### Support
The initial funding for this project was obtained through Bitcoin-cash' crowdfunding system - FlipStarter.    
I will not be asking for any donations for this particular projects further development until someone using this WaaS receives their first (mainnet)     donation / and i have fulfilled my FlipStarter promises. I think thats fair right? :)    
