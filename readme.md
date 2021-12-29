Work in progress. 

Currently have a VPS up and running @ http://109.228.52.142

I have been focusing on making it load quicker / supporting NonJS users.

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
- [x] static html creation loop
- [ ] a prompt if user wants to supply their viewkey (else wallets are made for them)

I will then begin work on Pi / VPS tutorials to show how easily you can deploy a funding page(and make a real readme! (:)

Then fix this: (can go in the static html refresher loop)
- [x] heartbeat to check if the monero remote node is online. If not try a list of nodes from the monero project (instead of a list of nodes, the "OK" status from the json metadata is removed.


## Electron-Cash-4.2.6
Comes with CashFusion. Reusable Payment Addresses are planned for a future release too! 
