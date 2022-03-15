
Currently, this will just create a mirror of the page @ rucknium.me/flask, however, i will eventually be making a generic version, and use the rucknium page as an example of installing a template (just copy and pasting a folder)    

Also ```ctrl+z``` and starting the script again is your friend if something goes wrong during ```make_wishlist.py``` e.g. wrongly select Restore from keys.   

### Testing Locally 
The only obstacle we're going to face in testing this locally, is getting Docker Engine and Docker Compose. I'm using Ubuntu: 
```
apt install docker.io docker-compose
```
Once this is done, we just need to download the ```docker-compose.yml``` file. Easily done with this line:
```
curl https://raw.githubusercontent.com/plowsof/flipstarter-waas-wip/mainnet/docker-compose.yml -o docker-compose.yml
```
Now, in the same directory, we just need to run ```docker-compose```, which will start the webserver @ http://172.20.111.2:8000/donate
```
sudo docker-compose up -d
```
The last step is to create our wishlist. To do this we must get onto the command line in the Docker container using:
```
sudo docker exec -it fresh /bin/bash
```
The word 'fresh' is just the name i've set in the docker compose file. You will now have command line access and be inside the ```home/app``` directory.
To run the wallet install wizard type this inside the docker container:
```
python3 make_wishlist.py
```
It's going to start up the wallets, and at each step, ask us if we want to paste in our view keys, or create them from scratch. You must take note of the seed phrases shown (when choosing to create wallets) otherwise you will not have access to any donations received.

Note - you must press enter when this appears: (when creating a bitcoin-cash wallet - the wallets can not / do not need to be encrypted, its just a view-only wallet also)   
```
Password (hit return if you do not wish to encrypt your wallet):
```
After the ```make_wishlist``` script is finished, the wallets will be loaded and the web page refreshed with your list. This process will take about minute or less.    

### Production / On a VPS
Lets pretend my name is George, i have a domain called getwishlisted.xyz and i want to run this wishlist on it. The only difference from running it locally is that i need to point nginx to my wishlist container and to set up the SSL serts (so my site is accessible using HTTPS).    

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
          proxy_pass https://172.20.111.2:8000;
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
I had an error 'to many redirects' because my dns providers ssl setting was off, i needed to change it to 'Full'   
Because this is a fresh server i am going to do a full install (where certbot modified the file we created earlier)    
````
sudo certbot
````
I ran ```sudo certbot``` a 2nd time for the ```www.``` url.    
After running through the setup / selecting nginx / agreeing to t&c's i see this output:
```
Successfully received certificate.    
Certificate is saved at: /etc/letsencrypt/live/www.getwishlisted.xyz/fullchain.pem    
Key is saved at:         /etc/letsencrypt/live/www.getwishlisted.xyz/privkey.pem    
```
At this point we need to ```cd``` to our ```/home``` folder and download the docker-compose file:
```
curl https://raw.githubusercontent.com/plowsof/flipstarter-waas-wip/mainnet/docker-compose.yml -o docker-compose.yml
```
We need an 'ssl' folder next to it to paste our certs in.
```
mkdir ssl
cd ssl
cp /etc/letsencrypt/live/www.getwishlisted.xyz/* . 
```
Which will look like:
```
docker-compose.yml
ssl/
    - fullchain.pem
    - privkey.pem
```
Perfect. Now lets install docker:
```
sudo apt install docker.io docker-compose
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
**I do not have internet access inside my docker container, searching for solution**     

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
### TODO
This is still in beta so i must do some sanity checks 
- [ ] sanity checks
### Support
The initial funding for this project was obtained through Bitcoin-cash' crowdfunding system - FlipStarter.    
I will not be asking for any donations for this particular projects further development until someone using this WaaS receives their first (mainnet)     donation / and i have fulfilled my FlipStarter promises. I think thats fair right? :)    
