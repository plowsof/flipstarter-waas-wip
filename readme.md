Work in progress. 

Currently have a VPS up and running @ http://109.228.52.142/funding

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
- [ ] update monero / bch / btc wallet files
- [ ] clean up the prompts / text shown (pretty colours)

I will then begin work on Pi / VPS tutorials to show how easily you can deploy a funding page(and make a real readme! (:)

Then fix this:
- [ ] heartbeat to check if the monero remote node is online. If not try a list of nodes from the monero project
