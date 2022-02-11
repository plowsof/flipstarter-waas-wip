Currently this will create a donation page @ localhost:8000/flask which is an exact copy of https://rucknium.me/flask/

### setup for (mistakes likely brb learning docker)

debian vps: 

(remove screen if you are testing locally)           
sudo apt-get -y install python3 pip3 git   
pip3 install uvicorn fastapi         
pip3 install -r requirements.txt    

git clone https://github.com/plowsof/flipstarter-waas-wip

cd to that directory and run:

sudo python3 make_wishlist.py

screen python3 start_daemons.py    
screen python3 -m uvicorn main:app --reload    
(press Ctrl+a then Ctrl+d to leave each of those screen sessions running) 

nginx conf:    

location /flask {
    include proxy_params;
    proxy_pass https://localhost:8000;
}

visit <url>/flask     

(in production this will be using cert files)    
### TODO
    
Tutorials will come after:    
- [x] the list can be edited while running
- [x] view only wallets can be created automatically @ setup 
    - [x] monero
    - [x] bch
    - [x] btc 
- [x] secure deletion of hot wallet files
- [x] wipe memory caches (must run make_wishlist as root for this)
- [x] detect btc/bch addresses so non-modified wallets can be used
- [x] update monero / bch / btc wallet files
- [ ] clean up the prompts / text shown (pretty colours)
- [x] a prompt if user wants to supply their viewkey (else wallets are made for them)
- [ ] static version for Non-JS users
- [ ] Dockerise:
    - monero-wallet-rpc
    - uvicorn
    - nginx    

I will then begin work on Pi / VPS tutorials to show how easily you can deploy a funding page(and make a real readme! (:)

Yes, it runs on a Pi - the source files for electrum/electron wallets must be used instead of the source , and alot more dependencies installed alot with:
sudo apt install libsecp256k1-dev
and the arm version of the monero-rpc-wallet is to be used.
If i can compile armv6 binaries of the monero rpc - it should (in theory) work on a pi zero - but im more certain about the Pi Zero 2.
I will be making a specific version / tutorials for this soon.
