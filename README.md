Work in progress. 


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
- [x] a prompt if user wants to supply their viewkey (else wallets are made for them)
- [ ] static version for Non-JS users
I will then begin work on Pi / VPS tutorials to show how easily you can deploy a funding page(and make a real readme! (:)

Then fix this: (can go in the static html refresher loop)
- [x] heartbeat to check if the monero remote node is online. If not try a list of nodes from the monero project (instead of a list of nodes, the "OK" status from the json metadata is removed.
- [x] Attempt at switching the monero remote node if/when it goes offline

